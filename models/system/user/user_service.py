from typing import Optional
from datetime import datetime
# 第三方包
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from tools.security.password_service import password_security
# 自定义包
from models.base_service import BaseService,UserModel,RoleModel
class UserService(BaseService[UserModel]):
    def __init__(self, db: Session, current_user_id:int):
        super().__init__(model=UserModel, db=db, current_user_id=current_user_id)

    @classmethod
    def get_user(cls, db: Session, user_id: int) -> Optional['UserModel']:
        """
        根据用户ID查询用户信息。

        参数:
            user_id (int): 要查询的用户ID。

        返回:
            Optional[Users]: 如果找到匹配的用户，则返回该用户对象；否则返回 None。
        """

        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.status == 1, UserModel.del_flag == 0).options(
            joinedload(UserModel.roles).joinedload(RoleModel.pages))
        return db.scalars(stmt).first()

    @classmethod
    def get_user_by_username(cls, db: Session, username: str) -> Optional[UserModel]:
        """
        根据用户名获取用户对象

        参数:
            username: 用户账号

        返回:
            UserModel 或 None
        """
        stmt = select(UserModel).where(UserModel.user_name == username)
        return db.scalar(stmt)
    @classmethod
    def create_password_hash(cls, password: str) -> str:
        """
        生成密码哈希值

        参数:
            password: 明文密码

        返回:
            密码哈希值
        """
        if not password:
            raise ValueError("密码不能为空")
        try:
            return password_security.generate_hash(password)
        except Exception as e:
            raise e
    @classmethod
    def check_user_password(cls, password_hash: str, password: str):
        """
        验证用户密码是否正确

        参数:
            user: 用户对象
            password: 明文密码

        返回:
            bool
        """
        if not password_hash or not password:
            return False
        pwd = password_security.verify_password(password_hash, password)
        if pwd[0]:
            return True
        return False

    @classmethod
    def login(cls, db: Session, user: UserModel, ip: str, token: str) -> UserModel:
        """
        更新用户登录信息（IP、时间、Token）

        参数:
            user: 用户对象
            ip: 登录 IP
            token: 登录 Token

        返回:
            更新后的用户对象
        """
        if not user:
            raise ValueError("用户不存在")
        if not ip or not token:
            raise ValueError("ip或者token不能为空")
        try:
            # 根据用户名查询用户
            user = cls.get_user(db, user.id)
            user.login_ip = ip
            user.login_date = datetime.now()
            user.session_token = token
            return user
        except Exception as e:
            raise e

    @classmethod
    def logout(cls, db: Session, user_id: int):
        """
        用户登出
        """
        if not user_id or not db:
            raise ValueError("用户id为空,或者数据库回话为空")
        user = cls.get_user(db, user_id)
        try:
            user.session_token = None
            return user
        except Exception as e:
            raise e
