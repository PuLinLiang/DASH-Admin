# models/system/syslog/logs_server.py
from typing import Any
from sqlalchemy.orm import Session
from .logs_model import LogModel


class LogService:

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.model = LogModel

    def create_log(
        self,
        user_id: str,
        log_level: str,
        ip: str,
        action: str,
        category_type: str,
        category: str,
        message: str,
        status: str,
        duration_ms: int,
        description:dict
    ):
        """
        创建一个新的日志条目并保存到数据库
        """
        new_log = LogModel(
            user_id=user_id,
            log_level=log_level,
            ip=ip,
            action=action,
            category_type=category_type,
            category=category,
            message=message,
            status=status,
            duration_ms=duration_ms,
            description=description
        )
        self.db_session.add(new_log)
        self.db_session.commit()
        return new_log
    def batch_create_logs(self, logs: list[dict[str, Any]]):
        """批量创建日志记录"""
        db_logs = [LogModel(**log) for log in logs]
        self.db_session.bulk_save_objects(db_logs)
    def get_logs_by_user(self, user_id: str):
        """
        根据用户ID查询所有相关日志
        """
        return self.db_session.query(LogModel).filter(LogModel.user_id == user_id).all()

    # 根据动态字段查询所有日志
    def get_all_by_fields(self, page: int = 1, page_size: int = 30, **kwargs):
        """
        根据任意字段查询所有日志
        """
        query = self.db_session.query(LogModel)
        if 'create_time_start' in kwargs and kwargs['create_time_start']:
            query = query.filter(LogModel.create_time >= kwargs.pop('create_time_start'))
        if 'create_time_end' in kwargs and kwargs['create_time_end']:
            query = query.filter(LogModel.create_time <= kwargs.pop('create_time_end'))
        count_query = query.filter_by(**kwargs)
        total = count_query.count()
        offset = (page - 1) * page_size
        logs = count_query.offset(offset).limit(page_size).all()
        return logs, total
