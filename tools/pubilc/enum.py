from enum import Enum as pyEnum
from typing import Optional

# 角色数据范围类型
class DataScopeType(pyEnum):
    """数据范围枚举类

    用于定义系统中角色可访问的数据范围类型，主要应用于数据权限控制。

    枚举值说明:
        ALL (1): 全部数据权限 - 可访问所有部门数据
        DEPT_WITH_CHILD (2): 本部门及以下数据 - 可访问所属部门及其子部门数据
        DEPT (3): 本部门数据 - 仅可访问所属部门数据
        CUSTOM (4): 自定义数据权限 - 根据角色配置的特定数据范围访问
    """

    ALL = 1
    DEPT_WITH_CHILD = 2
    DEPT = 3
    CUSTOM = 4

    @classmethod
    def get(cls, value):
        display_map = {
            cls.ALL: "全部",
            cls.DEPT_WITH_CHILD: "本部门及以下",
            cls.DEPT: "本部门",
            cls.CUSTOM: "自定义",
        }
        return display_map.get(value, str(value))
    
    @property
    def code(self) -> str:
        """获取模块编码"""
        return str(self.value)


    @classmethod
    def get_by_code(cls, code: str) -> Optional["DataScopeType"]:
        """
        根据模块编码获取枚举实例
        :param code: 模块编码
        :return: 对应的枚举实例或None
        """
        for item in cls:
            if item.code == code:
                return item
        return None


class PageType(pyEnum):
    """ 页面类型枚举类
    定义系统中所有可能的页面类型，用于页面分类和筛选
    """
    PUBLIC = "public"
    INDEPENDENT = "independent"
    STANDARD = "standard"


class ComponentType(pyEnum):
    """
    导航菜单组件类型
    """

    SubMenu = "SubMenu"
    Item = "Item"
    @property
    def code(self) -> str:
        """获取模块编码"""
        return self.value


    @classmethod
    def get_by_code(cls, code: str) -> Optional["ComponentType"]:
        """
        根据模块编码获取枚举实例
        :param code: 模块编码
        :return: 对应的枚举实例或None
        """
        for item in cls:
            if item.code == code:
                return item
        return None


class LogModule(pyEnum):
    """
    日志模块枚举类
    定义系统中所有可能的日志记录模块，用于日志分类和筛选
    """

    SYSTEM = ("system", "系统模块")
    DATABASE = ("database", "数据库模块")
    PERMISSION = ("permission", "权限模块")
    BUSINESS = ("business", "业务模块")
    BASE_SERVICE = ("base_service", "基础服务模块")
    CUSTOM = ("custom", "其他")
    
    AUTH = ("auth", "认证授权模块")
    USER = ("user", "用户管理模块")
    ROLE = ("role", "角色管理模块")
    DEPT = ("dept", "部门管理模块")
    MENU = ("menu", "菜单管理模块")
    POST = ("post", "岗位管理模块")
    CACHE = ("cache", "缓存模块")
    TASK = ("task", "任务调度模块")
    FILE = ("file", "文件操作模块")
    API = ("api", "接口服务模块")
    WEB = ("web", "Web请求模块")
    SECURITY = ("security", "安全审计模块")
    MONITOR = ("monitor", "系统监控模块")
    @property
    def code(self) -> str:
        """获取模块编码"""
        return self.value[0]

    @property
    def description(self) -> str:
        """获取模块描述"""
        return self.value[1]

    @classmethod
    def get_by_code(cls, code: str) -> Optional["LogModule"]:
        """
        根据模块编码获取枚举实例
        :param code: 模块编码
        :return: 对应的枚举实例或None
        """
        for item in cls:
            if item.code == code:
                return item
        return None


# 新增操作类型枚举
class OperationType(pyEnum):
    """
    操作类型枚举类
    定义系统中所有可能的操作类型，用于日志记录和权限控制
    """
    ACCESS = ("access", "页面访问")
    QUERY = ("query", "数据查询")
    CREATE = ("create", "数据创建")
    UPDATE = ("update", "数据更新")
    DELETE = ("delete", "数据删除")
    BATCH_DELETE = ("batch_delete", "批量数据删除")
    PARTIAL_UPDATE = ("partial_update", "部分数据更新")
    STATUS_CHANGE = ("status_change", "状态变更操作")
    BATCH_UPDATE = ("batch_update", "批量更新操作")
    IMPORT = ("import", "导入操作")
    EXPORT = ("export", "导出操作")
    LOGIN = ("login", "登录操作")
    LOGOUT = ("logout", "登出操作")

    PERMISSION_TAG = ("permission_check", "权限字符")
    PERMISSION_CHECK = ("permission_check", "权限检查")
    DATA_SCOPE_FILTER = ("data_scope_filter", "数据范围过滤")
    FIELD_VALIDATION = ("field_validation", "字段验证")

    SYSTEM_START = ("system_start", "系统启动")
    SYSTEM_SHUTDOWN = ("system_shutdown", "系统关闭")
    EXCEPTION = ("exception", "异常操作")

    TASK_EXECUTE = ("task_execute", "任务执行操作")
    LOCK = ("lock", "资源锁定操作")
    UNLOCK = ("unlock", "资源解锁操作")
    RATE_LIMIT = ("rate_limit", "限流触发操作")
    SENSITIVE_ACCESS = ("sensitive_access", "敏感数据访问")
    CUSTOM = ("custom", "其他")
    

    @property
    def code(self) -> str:
        """获取操作编码"""
        return self.value[0]

    @property
    def description(self) -> str:
        """获取操作描述"""
        return self.value[1]

    @classmethod
    def get_by_code(cls, code: str) -> Optional["OperationType"]:
        """
        根据操作编码获取枚举实例
        :param code: 操作编码
        :return: 对应的枚举实例或None
        """
        for item in cls:
            if item.code == code:
                return item
        return None
class Status(pyEnum):
    """
    状态枚举类
    定义系统中所有可能的状态，用于表示操作的成功或失败状态
    """
    SUCCESS = ("success", "成功")
    FAIL = ("fail", "失败")
    ERROR = ("error", "错误")
    INFO = ("info", "信息")
    WARNING = ("warning", "警告")
    DEBUG = ("debug", "调试")
    TRACE = ("trace", "跟踪")
    NOTICE = ("notice", "通知")
    ALERT = ("alert", "警告")
    CRITICAL = ("critical", "严重")
    FATAL = ("fatal", "致命")
    UNKNOWN = ("unknown", "未知")

