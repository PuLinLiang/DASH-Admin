from .syslog import LogModel
from .user import UserModel
from .dept import DeptModel
from .post import PostModel
from .role import RoleModel,role_to_dept,role_to_permission,role_to_user
from .page import PageModel
from .permissions import PermissionsModel

__all__ = [
    'LogModel',
    'UserModel',
    'DeptModel',
    'PageModel',
    'PostModel',
    'RoleModel',
    'PermissionsModel',
    'role_to_dept',
    'role_to_permission',
    'role_to_user'
]
