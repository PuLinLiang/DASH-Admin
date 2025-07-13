from flask_login import UserMixin
from sqlalchemy.orm import Session


from ..pubilc.enum import OperationType
from models.system.service import UserService


class LoginUser(UserMixin):
    # 添加缓存存储和线程锁
    def __init__(self):
        # 默认属性为空
        self.id = None
        self.user_name = None
        self.name = None
        self.post = None
        self.role_urls = []
        self.is_admin = False
        self.data_scope_type = None
        self.session_token = None
        self.dept_id = None
        self.user = None
        self.avatar = None

    def _load(self, db: Session, user_id: int):
        """
        加载用户数据到当前实例中
        """

        user_service = UserService(db, user_id)
        # 加载用户上下文
        user, roles, dept, is_admin, data_scope_type = user_service._get_user_context()
        # 加载用户权限
        permissions = user_service.get_user_permissions()
        urls = set()
        for per in permissions:
            _, op_code = per.key.split(":", 1)
            op_type = OperationType.get_by_code(op_code)
            if op_type == OperationType.ACCESS:
                urls.add(per.page.url)
        self.id = user.id
        self.user_name = user.user_name
        self.name = user.name
        self.post = getattr(user.post, "name", None)
        self.role_urls = urls
        self.is_admin = is_admin
        self.session_token = user.session_token
        self.dept_id = user.dept_id
        self.user = UserService(db, user_id)
        self.avatar = user.avatar
        self.data_scope_type = data_scope_type

    def check_permission(self, permission_tag: str, raise_exception: bool = False):
        """
        权限校验方法

        Args:
            permission_tag: 完整权限标识符 (如user:delete)
            raise_exception: 校验失败时是否抛出异常(默认False)

        Returns:
            bool: 当raise_exception=False时返回校验结果
        """
        if self.is_admin:
            return True
        if self.user:
            return self.user.check_permission(
                permission_tag=permission_tag, raise_exception=raise_exception
            )
        return False

    @classmethod
    def load(cls, db: Session, user_id: int):
        """
        工厂方法：加载用户数据并返回已初始化的对象
        """
        instance = cls()
        instance._load(db, user_id)
        return instance
