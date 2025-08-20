from re import T
from typing import List, Union, Callable,Literal
import os
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件

class DB_Config:
    """
    数据库配置类，支持从环境变量读取配置
    
    属性:
        URL (str): 数据库连接URL
        ECHO (bool): 是否输出SQL日志
        ...其他配置参数
    """
    # 从环境变量读取配置，无则使用默认值
    URL: str = os.getenv('DB_URL', 'sqlite:///dash_admin.db')  # 数据库连接URL，默认使用SQLite内存数据库
    ECHO: bool = os.getenv('DB_ECHO', 'False').lower() == 'true'  # 是否输出SQL日志，默认不输出
    POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '50'))  # 数据库连接池大小，默认50
    MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '80'))  # 连接池最大溢出连接数，默认80
    POOL_TIMEOUT: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))  # 连接池获取连接的超时时间(秒)，默认30秒
    POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '1800'))  # 连接池连接回收时间(秒)，默认1800秒
    MONITOR_POOL: bool = os.getenv('DB_MONITOR_POOL', 'False').lower() == 'true'  # 是否监控连接池，默认不监控
    DEBUG_MEMORY: bool = os.getenv('DB_DEBUG_MEMORY', 'False').lower() == 'true'  # 是否调试内存使用，默认不调试



class BaseConfig:
    """应用基础配置参数"""

    # 应用基础标题
    app_title: str = "DASH-Admin"

    # 应用版本
    app_version: str = "0.0.2"

    # 应用密钥
    app_secret_key: str = "magic-dash-pro-demo"

    # 核心页面侧边栏像素宽度
    core_side_width: int = 230

    # 登录页面左侧内容形式，可选项有'image'（图片内容）、'video'（视频内容）
    login_left_side_content_type: Literal["image", "video"] = "video"

    # 核心页面呈现类型，可选项有'single'（单页面形式）、'tabs'（多标签页形式）
    core_layout_type: Literal["single", "tabs"] = "tabs"

    # 是否在页首中显示页面搜索框
    show_core_page_search: bool = True

    # 请为各个项目设置不同的session_token_cookie_name
    session_token_cookie_name: str = "session_token"

    # -------------------------------------------------------全局 水印配置--------------------------------------------------------------------
    # 是否开启全屏额外水印功能
    enable_fullscreen_watermark: bool = False

    # 当开启了全屏额外水印功能时，用于动态处理实际水印内容输出
    fullscreen_watermark_generator: Callable = (
        lambda current_user: current_user.user_name
    )

    #----------------------------------------------------------全局 日志配置--------------------------------------------------------------------
    # 日志总开关
    ENABLE_LOGGING = False  # 全局日志开关，设置为 True 表示开启日志功能
    LOG_LEVEL = "WARNING"  # 全局日志级别，当前设置为 INFO 级别
    LOG_SENSITIVE_FIELDS = ['password', 'token']  # 需要脱敏的敏感字段


    # 控制台日志配置
    LOG_TO_CONSOLE = True  # 是否将日志输出到控制台，设置为 True 表示开启控制台日志
    LOG_CONSOLE_LEVEL = "DEBUG"  # 控制台日志级别，当前设置为 DEBUG 级别

    # 文件日志配置
    LOG_TO_FILE = True  # 是否将日志输出到文件，设置为 True 表示开启文件日志
    LOG_FILE_PATH = "logs/app.log"  # 日志文件的存储路径
    LOG_FILE_LEVEL = "INFO"  # 文件日志级别，当前设置为 INFO 级别
    LOG_FILE_BACKUP_COUNT = 30  # 日志文件的备份数量
    LOG_ROTATE_WHEN = "midnight"  # 日志文件轮转的时间点，设置为午夜
    LOG_ROTATE_INTERVAL = 1  # 日志文件轮转的间隔，单位根据 LOG_ROTATE_WHEN 确定
    LOG_FILE_ENCODING = "utf-8"  # 日志文件的编码格式
    LOG_FILE_MAX_BYTES = 10485760  # 单个日志文件最大大小(10MB)
    LOG_FILE_COMPRESS = True  # 是否压缩历史日志

    # 数据库日志配置
    LOG_TO_DB = True  # 是否将日志输出到数据库，设置为 True 表示开启数据库日志
    LOG_DB_LEVEL = "WARNING"  # 数据库日志级别，当前设置为 WARNING 级别
    LOG_DB_BATCH_SIZE = 500  # 数据库日志批量写入的数量 
    LOG_DB_FLUSH_INTERVAL = 10.0  # 数据库日志刷新的间隔时间，单位为秒
    LOG_QUEUE_MAX_SIZE = 8000  # 日志队列最大长度，防止内存溢出
    LOG_DB_RETRY_MAX = 3  # 数据库写入最大重试次数
    LOG_DB_RETRY_DELAY = 1.0  # 重试间隔(秒)
    LOG_EMERGENCY_PATH = "logs/emergency"  # 应急日志文件存储路径
    #----------------------------------------------------------全局 浏览器限制配置--------------------------------------------------------------------
    # 浏览器最低版本限制规则
    min_browser_versions: List[dict] = [
        {"browser": "Chrome", "version": 88},
        {"browser": "Firefox", "version": 78},
        {"browser": "Edge", "version": 100},
    ]

    # 是否基于min_browser_versions开启严格的浏览器类型限制
    # 不在min_browser_versions规则内的浏览器将被直接拦截
    strict_browser_type_check: bool = False


    # ---------------------------------------------------登录状态验证配置---------------------------------------------------------
    # 是否启用重复登录辅助检查
    enable_duplicate_login_check: bool = True

    # 重复登录辅助检查轮询间隔时间，单位：秒
    duplicate_login_check_interval: Union[int, float] = 10


class SecurityConfig():
    """
    企业级安全策略配置
    
    Attributes:
        PASSWORD_ALGORITHM (str): 密码哈希算法 (argon2/bcrypt)
        ARGON2_TIME_COST (int): 迭代次数
        ARGON2_MEMORY_COST (int): 内存消耗(KB)
        PASSWORD_MIN_LENGTH (int): 密码最小长度
        PASSWORD_COMPLEXITY (dict): 密码复杂度规则
    """
    
    # 算法选择
    PASSWORD_ALGORITHM: str = 'argon2'
    
    # Argon2 参数
    ARGON2_TIME_COST: int = 3  # 迭代次数
    ARGON2_MEMORY_COST: int = 65536  # 64MB，内存消耗(KB)
    ARGON2_PARALLELISM: int = 4  # 并行线程数
    ARGON2_HASH_LENGTH: int = 32  # 哈希值长度(字节)
    ARGON2_SALT_LENGTH: int = 16  # 盐值长度(字节)
    

    # 密码最小长度，要求用户密码至少包含 12 个字符
    PASSWORD_MIN_LENGTH: int = 12
    # 密码复杂度规则配置
    PASSWORD_COMPLEXITY: dict = {
        'require_uppercase': True,  # 是否要求密码包含大写字母
        'require_lowercase': True,  # 是否要求密码包含小写字母
        'require_digit': True,      # 是否要求密码包含数字
        'require_symbol': True,     # 是否要求密码包含特殊字符
        'allowed_symbols': '@$!%*?&+-',  # 允许使用的特殊字符
        'max_retries': 5,           # 密码输入最大重试次数
        'lockout_minutes': 30       # 密码输入失败达到最大重试次数后锁定账户的分钟数
    }

