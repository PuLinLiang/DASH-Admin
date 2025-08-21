# 导入系统包
# 导入第三方包
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging

# 导入自定义包
from config.base_config import DB_Config
log = logging.getLogger(__name__)



# 创建数据库连接引擎
engine = create_engine(
    url=DB_Config.URL,
    echo=DB_Config.ECHO,
    pool_size=DB_Config.POOL_SIZE,
    max_overflow=DB_Config.MAX_OVERFLOW,
    pool_timeout=DB_Config.POOL_TIMEOUT,
    pool_recycle=DB_Config.POOL_RECYCLE,
)

# 创建基类
Base = declarative_base()

# 创建会话工厂（推荐使用更明确的变量名）
SessionFactory = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # 防止commit后对象过期
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    安全的数据库会话上下文管理器

    示例用法：
    with get_db() as db:
        db.query(...)
    """
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        log.error(f"数据库事务上下文异常:数据库异常:{e}")
        session.rollback()
        raise
    except Exception as e:
        log.error(f"数据库事务上下文异常:非数据库异常:{e}")
        session.rollback()
        raise
    finally:
        try:
            session.close()
        except Exception as e:
            log.warning(f"关闭数据库连接时出错:{e}")


def configure_pool_monitoring(engine):
    """配置连接池监控事件"""

    # @event.listens_for(engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        """
        当数据库连接建立时触发的回调函数

        Args:
            dbapi_connection: 数据库API连接对象，用于与数据库进行底层交互
            connection_record: 连接记录对象，用于存储连接的相关信息
        """
        print(f"[{datetime.now()}] 数据库连接已建立。")
        connection_record.info['connect_time'] = datetime.now()
        log_pool_status(engine)
        log_pool_status(engine)

    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """
        当数据库连接从连接池取出时触发的回调函数

        Args:
            dbapi_connection: 数据库API连接对象，用于与数据库进行底层交互
            connection_record: 连接记录对象，用于存储连接的相关信息
            connection_proxy: 连接代理对象，用于管理连接的事务和其他属性
        """
        print(f"[{datetime.now()}] 连接从连接池中取出。")
        log_pool_status(engine)
        log_connection_id(dbapi_connection)
        if 'checkout_time' in connection_record.info:
            duration = (datetime.now() - connection_record.info['checkout_time']).total_seconds()
            if duration > 30:
                print(f"连接长时间占用: {duration}秒")
        connection_record.info['checkout_time'] = datetime.now()
        log_pool_status(engine)

    # @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        """
        当数据库连接返回到连接池时触发的回调函数

        Args:
            dbapi_connection: 数据库API连接对象，用于与数据库进行底层交互
            connection_record: 连接记录对象，用于存储连接的相关信息
        """
        print(f"[{datetime.now()}] 连接返回到连接池。")
        log_pool_status(engine)
        log_connection_id(dbapi_connection)

    # @event.listens_for(engine, "invalidate")
    def on_invalidate(dbapi_connection, connection_record, exception):
        """
        当数据库连接无效化（连接断开）时触发的回调函数

        Args:
            dbapi_connection: 数据库API连接对象，用于与数据库进行底层交互
            connection_record: 连接记录对象，用于存储连接的相关信息
            exception: 异常对象，描述连接断开的原因
        """
        print(f"[{datetime.now()}] 连接无效化: {exception}")
        log_pool_status(engine)
        log_connection_id(dbapi_connection)

    @event.listens_for(engine, "first_connect")
    def on_first_connect(dbapi_connection, connection_record):
        """
        当数据库连接第一次建立时触发的回调函数

        Args:
            dbapi_connection: 数据库API连接对象，用于与数据库进行底层交互
            connection_record: 连接记录对象，用于存储连接的相关信息
        """
        print(f"[{datetime.now()}] 第一次建立数据库连接。")
        log_pool_status(engine)
        log_connection_id(dbapi_connection)

def log_pool_status(engine):
    """
    记录数据库连接池状态（调试用）

    Args:
        engine: SQLAlchemy引擎对象，用于获取连接池信息
    """
    pool = engine.pool
    checkedin = pool.checkedin()
    checkedout = pool.checkedout()
    size = pool.size()
    overflow = pool.overflow()
    print(
        f"[{datetime.now()}] 连接池状态 - 总大小: {size}, 已使用: {checkedout}, 空闲: {checkedin}, 溢出: {overflow}"
    )


def log_connection_id(dbapi_connection):
    """
    获取并记录数据库连接的ID（调试用）

    Args:
        dbapi_connection: 数据库API连接对象，用于与数据库进行底层交互
    """
    # 获取连接ID（假设使用的是MySQL）
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("SELECT CONNECTION_ID()")
        connection_id = cursor.fetchone()[0]
        cursor.close()
        print(f"[{datetime.now()}] 连接ID: {connection_id}")
    except Exception as e:
        print(f"[{datetime.now()}] 获取连接ID失败: {e}")


# 可选：内存监控（调试时使用）
def log_memory_usage():
    """记录内存使用情况（调试用）"""
    if DB_Config.DEBUG_MEMORY:
        import psutil

        process = psutil.Process()
        mem_info = process.memory_info()
        print(f"内存使用量: {mem_info.rss / 1024 / 1024:.2f} MB")


# 在需要的地方调用内存监控
log_memory_usage()
# 启用连接池监控（根据配置决定）
if DB_Config.MONITOR_POOL:
    configure_pool_monitoring(engine)
