# tools/token_manager.py
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from config.base_config import BaseConfig
from typing import Union
import logging
from functools import wraps
from flask import request
from dash import set_props, dcc
from models.system.user.user_service import UserService
from models.base import get_db


class TokenManager:
    # 使用类变量存储共享资源
    serializer = URLSafeTimedSerializer(
        secret_key=BaseConfig.app_secret_key,
        salt="user-login"
    )
    logger = logging.getLogger(__name__)

    @classmethod
    def generate_token(cls, user_id: int) -> str:
        """生成 JWT 风格的加密 Token"""
        token = cls.serializer.dumps(user_id)
        cls.logger.info(f"Token generated for user {user_id}")
        return token

    @classmethod
    def verify_token(cls, token: str, max_age_seconds: int = 3600) -> Union[int, None]:
        """验证并解析 Token，返回用户 ID 或 None"""
        try:
            user_id = cls.serializer.loads(token, max_age=max_age_seconds)
            cls.logger.info(f"Token verified for user {user_id}")
            return user_id
        except SignatureExpired:
            cls.logger.warning("Token expired")
            return None
        except BadSignature:
            cls.logger.error("Invalid token signature")
            return None
        except Exception as e:
            cls.logger.error(f"Token verification failed: {str(e)}")
            return None

    @classmethod
    def refresh_token(cls, old_token: str, additional_time: int = 3600) -> str:
        """刷新 Token，延长其有效期"""
        try:
            user_id = cls.serializer.loads(old_token, max_age=additional_time)
            return cls.generate_token(user_id)
        except Exception as e:
            cls.logger.warning(f"Failed to refresh token: {str(e)}")
            return cls.generate_token(cls.serializer.loads(old_token, max_age=None))

    @staticmethod
    def prevent_duplicate_login(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get(BaseConfig.session_token_cookie_name)
            if not token:
                return
            token_manager = TokenManager()
            user_id = token_manager.verify_token(token)
            if not user_id:
                set_props("global-redirect", {"children": dcc.Location(pathname="/logout", id="global-redirect")})
                return

            with get_db() as db:
                match_user = UserService.get_user(db, int(user_id))

            if not match_user or match_user.session_token != token:
                set_props("global-redirect", {"children": dcc.Location(pathname="/logout", id="global-redirect")})
            return f(*args, **kwargs)

        return decorated_function
