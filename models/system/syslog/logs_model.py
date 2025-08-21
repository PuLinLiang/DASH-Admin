# models/system/syslog/logs_model.py
from sqlalchemy import DateTime, func, Text, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from models.base import Base


class LogModel(Base):
    """
    系统日志模型，使用 SQLAlchemy 2.0 风格定义字段。
    所有字段命名与日志格式及数据库写入处理器保持一致。
    """

    __tablename__ = 'sys_logs'

    # 日志主键 ID，自增主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 日志创建时间，默认为当前时间
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())

    # 日志等级（INFO/WARNING/ERROR等），用于分类日志严重程度
    log_level: Mapped[str] = mapped_column(String(10), nullable=False)

    # 日志消息内容
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # 模块名称（如 system/user）
    logmodule: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    # 操作标识符（如 system.role.update）
    operation: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # 操作类型（如 增、删、改、查、登录、系统状态）
    logmodule_operation: Mapped[str] = mapped_column(String(20), nullable=False)

    # 用户ID（支持 anonymous 表示未登录用户）
    user_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    # 客户端IP地址
    ip: Mapped[str] = mapped_column(String(50), nullable=False)

    # 操作状态（成功、失败、异常等）
    status: Mapped[str] = mapped_column(String(10), default="success", nullable=False)

    # 操作耗时（单位毫秒）
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 扩展描述字段，可用于记录请求参数、响应数据等（JSON字符串）
    description: Mapped[dict] = mapped_column(JSON, default={})
