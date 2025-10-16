from .user.user_service import UserService
from .role.role_service import RoleService
from .dept.dept_service import DeptService
from .post.post_service import PostService
from .page.page_service import PageService
from .permissions.permissons_service import PermissionsService
from .syslog.logs_server import LogService


__all__ = [
    'UserService',
    'RoleService',
    'DeptService',
    'PostService',
    'PageService',
    'PermissionsService',
    'LogService'
]
