# tools/sys_log/logconfig.py
import logging
import os
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from typing import  Any

# 注册退出钩子
import atexit

# 导入 SafeFormatter 支持默认字段填充
from .logger import SafeFormatter, dash_logger
from config.base_config import BaseConfig
from .db_log_handler import DatabaseLogHandler


def setup_logging(app) -> None:
    """
    统一配置所有日志记录器：Flask/Dash logger + root logger + dash_logger
    增强特性：
    - 完善的错误处理与资源释放
    - 灵活的日志轮转配置
    - 路径自动创建与权限检查
    - 全参数可配置化

    :param app: Flask/Dash 应用实例
    """
    _validate_config()
    if not getattr(BaseConfig, "ENABLE_LOGGING", True):
        app.logger.info("日志系统已禁用")
        return

    try:
        # 确保日志目录存在并具有写入权限
        log_dir = Path(app.root_path) / "logs"
        _ensure_directory(log_dir)

        # 构建统一的结构化日志格式
        formatter = SafeFormatter(
            "{"
            '"timestamp": "%(asctime)s", '
            '"level": "%(levelname)s", '
            '"message": "%(message)s", '
            '"logmodule": "%(logmodule)s", '
            '"operation": "%(operation)s", '
            '"status": "%(status)s", '
            '"duration_ms": %(duration_ms)d, '
            '"logmodule_operation": "%(logmodule_operation)s", '
            '"description": %(description)s, '
            "}"
        )

        # 获取并配置日志器
        root_logger = logging.getLogger()
        flask_logger = app.logger
        _configure_logger(root_logger, flask_logger, formatter)

        # 移除已有的 handlers，避免重复添加
        # for handler in flask_logger.handlers[:]:
        #     flask_logger.removeHandler(handler)

        # for handler in root_logger.handlers[:]:
        #     root_logger.removeHandler(handler)

        # 初始化 dash_logger
        dash_logger.init_app(flask_logger)
        flask_logger.info("日志系统初始化完成")

    except Exception as e:
        # 紧急情况下输出到标准错误流
        print(f"日志系统初始化失败: {str(e)}", file=sys.stderr)


def _validate_config() -> None:
    required_configs = [
        "LOG_TO_DB",
        "LOG_DB_BATCH_SIZE",
        "LOG_DB_FLUSH_INTERVAL",
        "LOG_QUEUE_MAX_SIZE",
        "LOG_DB_LEVEL",
    ]
    missing = [cfg for cfg in required_configs if not hasattr(BaseConfig, cfg)]
    if missing:
        raise ValueError(f"日志配置缺失必填项: {', '.join(missing)}")


def _ensure_directory(path: Path) -> None:
    """
    确保目录存在并具有写入权限
    :param path: 目录路径
    :raises OSError: 当无法创建目录或无写入权限时
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        # 检查写入权限
        test_file = path / ".write_test.tmp"
        with open(test_file, "w") as f:
            f.write("test")
        test_file.unlink()
    except PermissionError:
        raise OSError(f"对目录 {path} 没有写入权限")
    except Exception as e:
        raise OSError(f"创建目录 {path} 失败: {str(e)}")


def _configure_logger(
    root_logger: logging.Logger,
    flask_logger: logging.Logger,
    formatter: logging.Formatter,
) -> None:
    """
    配置日志处理器
    :param root_logger: 根日志器
    :param flask_logger: Flask应用日志器
    :param formatter: 日志格式化器
    """
    # 移除已有处理器，避免重复输出
    for logger in [root_logger, flask_logger]:
        logger.propagate = False
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        logger.setLevel(
            logging.getLevelName(getattr(BaseConfig, "LOG_LEVEL", "INFO").upper())
        )

    # 配置控制台处理器
    if getattr(BaseConfig, "LOG_TO_CONSOLE", True):
        console_handler = _create_console_handler(formatter)
        flask_logger.addHandler(console_handler)
        root_logger.addHandler(console_handler)
        flask_logger.info(
                f"控制台日志处理器已初始化，级别: {BaseConfig.LOG_LEVEL}"
            )

    # 配置文件处理器
    if getattr(BaseConfig, "LOG_TO_FILE", True):
        try:
            file_handler = _create_file_handler(formatter)
            flask_logger.addHandler(file_handler)
            root_logger.addHandler(file_handler)
            flask_logger.info(
                f"文件日志处理器已初始化，级别: {BaseConfig.LOG_LEVEL}"
            )
        except Exception as e:
            flask_logger.error(f"文件日志处理器创建失败: {str(e)}")

    # 配置数据库处理器
    if getattr(BaseConfig, "LOG_TO_DB", False):
        try:
            db_handler = _create_db_handler()
            db_handler.setFormatter(formatter)
            flask_logger.addHandler(db_handler)
            root_logger.addHandler(db_handler)
            flask_logger.info(
                f"数据库日志处理器已初始化，级别: {BaseConfig.LOG_DB_LEVEL}"
            )
        except Exception as e:
            flask_logger.error(f"数据库日志处理器创建失败: {str(e)}")


def _create_console_handler(formatter: logging.Formatter) -> logging.StreamHandler:
    """
    创建控制台日志处理器
    :param formatter: 日志格式化器
    :return: 配置好的控制台处理器
    """
    console_handler = logging.StreamHandler()
    console_level = getattr(BaseConfig, "LOG_CONSOLE_LEVEL", "DEBUG").upper()
    console_handler.setLevel(logging.getLevelName(console_level))
    console_handler.setFormatter(formatter)
    return console_handler


def _create_file_handler(formatter: logging.Formatter) -> TimedRotatingFileHandler:
    """
    创建文件日志处理器，支持自动轮转
    :param formatter: 日志格式化器
    :return: 配置好的文件处理器
    """
    log_file_path = getattr(BaseConfig, "LOG_FILE_PATH", "logs/app.log")
    log_dir = os.path.dirname(log_file_path)
    _ensure_directory(Path(log_dir))

    # 日志轮转配置
    when = getattr(BaseConfig, "LOG_ROTATE_WHEN", "midnight")
    interval = getattr(BaseConfig, "LOG_ROTATE_INTERVAL", 1)
    backup_count = getattr(BaseConfig, "LOG_FILE_BACKUP_COUNT", 30)
    encoding = getattr(BaseConfig, "LOG_FILE_ENCODING", "utf-8")
    delay = getattr(BaseConfig, "LOG_FILE_DELAY", False)

    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding=encoding,
        delay=delay,
    )

    # 设置日志级别
    file_level = getattr(BaseConfig, "LOG_FILE_LEVEL", "INFO").upper()
    file_handler.setLevel(logging.getLevelName(file_level))
    file_handler.setFormatter(formatter)

    # 添加日志轮转后缀格式
    file_handler.suffix = "%Y-%m-%d.log"
    return file_handler


def _create_db_handler() -> Any:
    """
    创建数据库日志处理器
    :return: 配置好的数据库处理器
    """

    # 从配置获取批量参数
    batch_size = getattr(BaseConfig, "LOG_DB_BATCH_SIZE", 100)
    flush_interval = getattr(BaseConfig, "LOG_DB_FLUSH_INTERVAL", 5.0)
    db_level = getattr(BaseConfig, "LOG_DB_LEVEL", "INFO").upper()

    db_handler = DatabaseLogHandler(
        batch_size=batch_size, flush_interval=flush_interval
    )
    db_handler.setLevel(logging.getLevelName(db_level))
    return db_handler


# 确保应用退出时正确关闭日志处理器
def shutdown_logging() -> None:
    """关闭所有日志处理器，确保资源正确释放"""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        try:
            if hasattr(handler, "close"):
                handler.close()
            root_logger.removeHandler(handler)
        except Exception as e:
            print(f"关闭日志处理器失败: {str(e)}", file=sys.stderr)

    # 添加系统关闭日志
    if dash_logger.logger:
        dash_logger.info(
            "系统已关闭...",
            logmodule=dash_logger.logmodule.SYSTEM,
            operation=dash_logger.operation.SYSTEM_SHUTDOWN,
        )


atexit.register(shutdown_logging)
