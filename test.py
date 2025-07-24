from sqlalchemy.exc import IntegrityError
from models.system import (
    UserModel,
    PostModel,
    RoleModel,
    DeptModel,
)
from sqlalchemy.orm import Session
from models.base import Base, get_db, engine
from tools.public.enum import DataScopeType
from tools.security import password_security
from models.system.service import UserService

with get_db() as db:
    print("开始")
    # 初始化基础数据
    # init_base_data(db)
    user_service = UserService(db, 1)
    # 加载用户权限
    url = user_service.get_user_page_keys()
    print(url)
    a =set(u.url for u in url)
    print(a)
    print("完成")
