# 导入系统包
# 导入第三方包
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import logging
# 导入自定义包
from config.db_config import DB_Config, configure_pool_monitoring, log_memory_usage
log = logging.getLogger(__name__)



# 创建数据库连接引擎
engine = create_engine(
    url=DB_Config.get_url(),
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


# 启用数据库连接池监控 和 内存监控 （根据配置决定）
if DB_Config.MONITOR_POOL or DB_Config.DEBUG_MEMORY:
    configure_pool_monitoring(engine)
    log_memory_usage()