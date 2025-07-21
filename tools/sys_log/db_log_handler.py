import logging
import sys
import queue
import time
import threading
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import json  

from models.system.service import LogService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.base_config import DB_Config, BaseConfig
from contextlib import contextmanager


from tools.public.enum import LogModule, OperationType  # 导入枚举类

# 使用配置中的数据库 URL，但可单独配置为其他数据库
engine = create_engine(DB_Config.URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


@contextmanager
def get_log_db():
    """数据库会话上下文管理器，确保连接自动关闭"""
    db = SessionLocal()
    try:
        print("日志数据库连接")
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        print("日志数据库关闭连接")
        db.close()


class DatabaseLogHandler(logging.Handler):
    def __init__(
        self,
        batch_size: int,
        flush_interval: int,
        level=logging.NOTSET,
    ): 
        """
        数据库日志处理器，支持批量写入和枚举值处理
        :param level: 日志级别
        :param batch_size: 批量写入阈值
        :param flush_interval: 定时刷新间隔(秒)
        """
        super().__init__(level=level)
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.log_queue = queue.Queue(maxsize=BaseConfig.LOG_QUEUE_MAX_SIZE)
        self._closed = False
        self.retry_count = 0
        self.log_to_db = BaseConfig.LOG_TO_DB  # 添加配置检查
        # 仅在启用数据库日志时启动线程
        if self.log_to_db:
            self.flush_thread = threading.Thread(target=self._flush_worker, daemon=True)
            self.flush_thread.start()

    def emit(self, record):
        print("当前列队数量：",self.log_queue.qsize())
        if not sys.is_finalizing() and not self._closed:
            try:
                # 转换为可序列化的字典
                log_entry = self._convert_record(record)
                self.log_queue.put(log_entry)
            except Exception as e:
                self.handleError(record)

    def _convert_record(self, record) -> Dict[str, Any]:
        """转换日志记录为数据库条目格式，处理枚举值"""
        # 处理枚举值
        logmodule = getattr(record, 'logmodule', LogModule.CUSTOM)
        operation = getattr(record, 'operation', OperationType.CUSTOM)
        return {
            "log_level": record.levelname,
            "message": record.getMessage(),
            "status": getattr(record, "status", "成功"),
            "duration_ms": getattr(record, "duration_ms", 0),
            "description": dict(getattr(record, "description", {})),
            "user_id": getattr(record, "user", "anonymous"),
            "ip": getattr(record, "ip", "unknown"),
            "logmodule": logmodule.code,
            "operation": operation.code,
            # 优化组合字段
            "logmodule_operation": f"{logmodule.description}-{operation.description}",
        }

    def _flush_worker(self):
        """后台线程：定时批量写入日志"""
        while not self._closed and self.log_to_db:  # 添加配置检查
            time.sleep(self.flush_interval)
            self._batch_write()

    # @retry(
    #     stop=stop_after_attempt(BaseConfig.LOG_DB_RETRY_MAX),
    #     wait=wait_exponential(multiplier=1, min=1, max=10),
    # )
    def _batch_write(self):
        """批量写入日志到数据库，带有限重试机制"""
        if self.log_queue.empty():
            return

        batch: List[Dict[str, Any]] = []
        try:
            while len(batch) < self.batch_size and not self.log_queue.empty():
                batch.append(self.log_queue.get_nowait())

            if not batch:
                return

            with get_log_db() as db:
                log_service = LogService(db)
                log_service.batch_create_logs(batch)

        except Exception as e:
            # 有限重试机制
            if self.retry_count < BaseConfig.LOG_DB_RETRY_MAX:
                self.retry_count += 1
                time.sleep(BaseConfig.LOG_DB_RETRY_DELAY * (2 **(self.retry_count - 1)))  # 指数退避
                self.log_queue.put(batch)
                return

            # 重试失败后写入本地应急文件
            self._write_to_emergency_file(batch, e)
            self.retry_count = 0  # 重置重试计数器
        else:
            for _ in batch:
                self.log_queue.task_done()

    def _write_to_emergency_file(self, batch: list[dict], error: Exception):
        """写入应急日志文件，防止数据丢失"""
        emergency_path = Path(BaseConfig.LOG_EMERGENCY_PATH)
        if not emergency_path.exists():
            emergency_path.mkdir(parents=True, exist_ok=True)

        filename = f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(emergency_path / filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'error': str(error),
                'batch_size': len(batch),
                'logs': batch
            }, f, ensure_ascii=False, indent=2)

    def get_queue_status(self):
        """获取队列状态"""

        return {
            "current_size": self.log_queue.qsize(),
            "max_size": self.log_queue.maxsize,
            "is_full": self.log_queue.full(),
            
        }

    def close(self):
        """关闭处理器，确保所有日志都被写入"""
        if not self._closed:
            self._closed = True
            # 等待队列处理完成
            self.log_queue.join()
            # 最后一次批量写入
            self._batch_write()
        super().close()
