# 验证用户当前页面 指定操作权限""
from sqlalchemy import select, and_

from models.base import get_db
# from models.system import Role


def check_permission(user_id: int, url: str, action_key: str):
    """
    页面操作权限验证
    db: 数据库连接对象，用于访问数据库
    user_id: 用户ID，整型，用于标识用户
    url: 用户请求的页面URL，字符串类型
    action_key: 用户请求的操作键，字符串类型，用于标识具体操作

    返回值:
    根据用户权限和请求的操作，返回相应的结果
    """
    return None
    # 使用上下文管理器确保数据库连接的正确打开和关闭
    with get_db() as db:
        # 调用Role类中的has_page_permission方法获取用户的权限URLs
        return Role.has_page_permission(db, user_id, url, action_key)

