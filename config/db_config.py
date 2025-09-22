import os
from datetime import datetime
import importlib.util
from typing import Any
from sqlalchemy.engine import URL
from sqlalchemy import event,Engine

try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载.env文件
except ImportError:
    # 如果没有安装python-dotenv，忽略错误
    pass

class DB_Config:
    """
    数据库配置类，支持从环境变量读取配置
    支持 SQLite、MySQL、PostgreSQL 数据库
    
    属性:
        URL: 数据库连接URL对象
        ECHO (bool): 是否输出SQL日志
        ECHO_POOL (bool): 是否输出连接池日志
        POOL_SIZE (int): 连接池大小
        MAX_OVERFLOW (int): 连接池最大溢出连接数
        POOL_TIMEOUT (int): 连接池获取连接的超时时间
        POOL_RECYCLE (int): 连接池连接回收时间
        MONITOR_POOL (bool): 是否监控连接池
        DEBUG_MEMORY (bool): 是否调试内存使用
    """
    
    # ===========================================
    # 数据库基本配置 Database Basic Configuration
    # ===========================================
    
    # 数据库类型，从环境变量读取，默认为 sqlite
    DB_TYPE: str = os.getenv('DB_TYPE', 'sqlite').lower()
    
    # 数据库驱动，从环境变量读取，如果未设置则使用默认驱动
    DB_DRIVER: str = os.getenv('DB_DRIVER', '').strip()
    
    # ===========================================
    # SQLite 数据库配置 SQLite Configuration
    # ===========================================
    
    # SQLite 数据库文件路径，默认为 ./data/dash_admin.db
    SQLITE_DATABASE: str = os.getenv('SQLITE_DATABASE', './dash_admin.db')
    
    # ===========================================
    # MySQL 数据库配置 MySQL Configuration
    # ===========================================
    
    # MySQL 服务器地址，默认为 localhost
    MYSQL_HOST: str = os.getenv('MYSQL_HOST', 'localhost')
    # MySQL 服务器端口，默认为 3306
    MYSQL_PORT: int = int(os.getenv('MYSQL_PORT', '3306'))
    # MySQL 用户名，默认为 root
    MYSQL_USER: str = os.getenv('MYSQL_USER', 'root')
    # MySQL 密码，默认为空
    MYSQL_PASSWORD: str = os.getenv('MYSQL_PASSWORD', '')
    # MySQL 数据库名，默认为 dash_admin
    MYSQL_DATABASE: str = os.getenv('MYSQL_DATABASE', 'dash_admin')
    # MySQL 字符集，默认为 utf8mb4
    MYSQL_CHARSET: str = os.getenv('MYSQL_CHARSET', 'utf8mb4')
    
    # ===========================================
    # PostgreSQL 数据库配置 PostgreSQL Configuration
    # ===========================================
    
    # PostgreSQL 服务器地址，默认为 localhost
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    # PostgreSQL 服务器端口，默认为 5432
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', '5432'))
    # PostgreSQL 用户名，默认为 postgres
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    # PostgreSQL 密码，默认为空
    POSTGRES_PASSWORD: str = os.getenv('POSTGRES_PASSWORD', '')
    # PostgreSQL 数据库名，默认为 dash_admin
    POSTGRES_DATABASE: str = os.getenv('POSTGRES_DATABASE', 'dash_admin')
    
    # ===========================================
    # 数据库连接池配置 Database Pool Configuration
    # ===========================================
    
    # 连接池大小，默认为 5
    POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))
    # 连接池最大溢出连接数，默认为 10
    MAX_OVERFLOW: int = int(os.getenv('DB_POOL_MAX_OVERFLOW', '10'))
    # 连接池获取连接的超时时间(秒)，默认为 30 秒
    POOL_TIMEOUT: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    # 连接池连接回收时间(秒)，默认为 3600 秒 (1小时)
    POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    
    # ===========================================
    # 数据库调试配置 Database Debug Configuration
    # ===========================================
    
    # 是否输出SQL语句到控制台，默认为 False
    ECHO: bool = os.getenv('DB_ECHO', 'false').lower() == 'true'
    # 是否输出连接池日志，默认为 False
    ECHO_POOL: bool = os.getenv('DB_ECHO_POOL', 'false').lower() == 'true'
    # 是否监控连接池，默认为 False
    MONITOR_POOL: bool = os.getenv('DB_MONITOR_POOL', 'false').lower() == 'true'
    # 是否调试内存使用，默认为 False
    DEBUG_MEMORY: bool = os.getenv('DB_DEBUG_MEMORY', 'false').lower() == 'true'



    @classmethod
    def check_required_fields(cls, db_type: str) -> None:
        """
        检查数据库配置的必要字段是否已配置
        
        Args:
            db_type: 数据库类型
            
        Raises:
            ValueError: 当必要字段未配置时抛出异常
        """
        if db_type == 'sqlite':
            if not cls.SQLITE_DATABASE:
                raise ValueError("SQLite数据库路径未配置")
        
        elif db_type == 'mysql':
            required_fields = [
                ('MYSQL_HOST', cls.MYSQL_HOST),
                ('MYSQL_USER', cls.MYSQL_USER),
                ('MYSQL_DATABASE', cls.MYSQL_DATABASE)
            ]
            
            missing_fields = []
            for field_name, field_value in required_fields:
                if not field_value:
                    missing_fields.append(field_name)
            
            if missing_fields:
                raise ValueError(f"MySQL配置缺少必要字段: {', '.join(missing_fields)}")
        
        elif db_type == 'postgresql':
            required_fields = [
                ('POSTGRES_HOST', cls.POSTGRES_HOST),
                ('POSTGRES_USER', cls.POSTGRES_USER),
                ('POSTGRES_DATABASE', cls.POSTGRES_DATABASE)
            ]
            
            missing_fields = []
            for field_name, field_value in required_fields:
                if not field_value:
                    missing_fields.append(field_name)
            
            if missing_fields:
                raise ValueError(f"PostgreSQL配置缺少必要字段: {', '.join(missing_fields)}")

    @classmethod
    def check_driver_installed(cls, driver_name: str) -> bool:
        """
        检查指定的数据库驱动是否已安装
        
        Args:
            driver_name: 驱动名称
            
        Returns:
            bool: 驱动是否已安装
        """
        if not driver_name:
            raise ValueError(f"数据库驱动未配置,请检查!")


        # 使用 importlib 检查模块是否存在
        spec = importlib.util.find_spec(driver_name)
        return spec is not None
    
    @classmethod
    def create_database_url(cls) -> URL:
        """
        根据配置创建数据库连接URL
        
        Returns:
            sqlalchemy.URL: 数据库连接URL对象
            
        Raises:
            ValueError: 当数据库类型不支持时抛出异常
        """
        db_type = cls.DB_TYPE
        
        # 检查必要字段配置
        cls.check_required_fields(db_type)
        
        # 检查驱动是否安装
        if db_type in ['mysql', 'postgresql']:
            if not cls.check_driver_installed(cls.DB_DRIVER):
                raise ValueError(f"数据库驱动 '{cls.DB_DRIVER}' 未安装。请检查")
        
        if db_type == 'sqlite':
            # SQLite 数据库配置
            return URL.create(
                drivername='sqlite',
                database=cls.SQLITE_DATABASE
            )
        
        elif db_type == 'mysql':
            # MySQL 数据库配置
            # 确定驱动名称
            driver = cls.DB_DRIVER or 'pymysql'
            drivername = f'mysql+{driver}'
            
            # 构建查询参数
            query = {}
            if cls.MYSQL_CHARSET:
                query['charset'] = cls.MYSQL_CHARSET
            
            return URL.create(
                drivername=drivername,
                username=cls.MYSQL_USER,
                password=cls.MYSQL_PASSWORD or None,
                host=cls.MYSQL_HOST,
                port=cls.MYSQL_PORT,
                database=cls.MYSQL_DATABASE,
                query=query
            )
        
        elif db_type == 'postgresql':
            # PostgreSQL 数据库配置
            # 确定驱动名称
            driver = cls.DB_DRIVER or 'psycopg2'
            drivername = f'postgresql+{driver}'
            
            return URL.create(
                drivername=drivername,
                username=cls.POSTGRES_USER,
                password=cls.POSTGRES_PASSWORD or None,
                host=cls.POSTGRES_HOST,
                port=cls.POSTGRES_PORT,
                database=cls.POSTGRES_DATABASE
            )
        
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}。支持的类型: sqlite, mysql, postgresql")


    @classmethod
    def get_url(cls) -> URL:
        return cls.create_database_url()

    @classmethod
    def get_database_info(cls) -> dict[str, Any]:
        """
        获取当前数据库配置信息
        
        Returns:
            dict: 数据库配置信息字典
        """
        return {
            '数据库类型': cls.DB_TYPE,
            '数据库驱动': cls.DB_DRIVER or '默认驱动',
            '连接池大小': cls.POOL_SIZE,
            '最大溢出连接': cls.MAX_OVERFLOW,
            '连接超时时间': f'{cls.POOL_TIMEOUT}秒',
            '连接回收时间': f'{cls.POOL_RECYCLE}秒',
            'SQL日志': '开启' if cls.ECHO else '关闭',
            '连接池日志': '开启' if cls.ECHO_POOL else '关闭',
            '连接池监控': '开启' if cls.MONITOR_POOL else '关闭',
            '内存调试': '开启' if cls.DEBUG_MEMORY else '关闭'
        }

def configure_pool_monitoring(engine: Engine):
    """配置连接池监控事件"""

    @event.listens_for(engine, "connect")
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
    import psutil
    process = psutil.Process()
    mem_info = process.memory_info()
    print(f"内存使用量: {mem_info.rss / 1024 / 1024:.2f} MB")


