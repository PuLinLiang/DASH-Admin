import re
from typing import Tuple, Optional
from argon2 import PasswordHasher, exceptions
from werkzeug.security import check_password_hash  # 添加PBKDF2支持
from config.base_config import SecurityConfig
import logging


class PasswordSecurity:
    """
    企业级密码安全服务（支持混合算法验证）

    Attributes:
        config (SecurityConfig): 安全配置实例
        hasher (PasswordHasher): Argon2哈希处理器实例
    """

    def __init__(self):
        self.config = SecurityConfig()
        self.hasher = PasswordHasher(
            time_cost=self.config.ARGON2_TIME_COST,
            memory_cost=self.config.ARGON2_MEMORY_COST,
            parallelism=self.config.ARGON2_PARALLELISM,
            hash_len=self.config.ARGON2_HASH_LENGTH,
            salt_len=self.config.ARGON2_SALT_LENGTH,
        )

    def generate_hash(self, password: str) -> str:
        """
        生成安全密码哈希

        Args:
            password: 明文密码

        Returns:
            str: 哈希后的密码字符串

        Raises:
            ValueError: 密码不符合复杂度要求时抛出
            RuntimeError: 哈希生成系统错误时抛出
        """
        self._validate_complexity(password)
        try:
            return self.hasher.hash(password)
        except exceptions.HashingError as e:
            logging.critical(f"密码哈希生成失败: {str(e)}")
            raise RuntimeError("系统安全服务暂时不可用") from e

    def verify_password(self, password_hash: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        安全验证密码哈希（支持混合算法）

        Args:
            password_hash: 数据库存储的密码哈希值
            password: 用户输入的明文密码

        Returns:
            Tuple[bool, Optional[str]]: 
                - 验证结果
                - 使用的算法类型（Argon2/PBKDF2）

        Raises:
            SecurityException: 当发生系统级安全错误时抛出
        """
        try:
            algorithm = self._detect_algorithm(password_hash)
            
            if algorithm == "Argon2":
                return self._verify_argon2(password_hash, password), algorithm
            elif algorithm == "PBKDF2-SHA256":
                return self._verify_pbkdf2(password_hash, password), algorithm
            else:
                logging.warning(f"未知哈希格式: {password_hash[:16]}...")
                return False, None
        except exceptions.VerificationError as e:
            logging.error(f"密码验证系统错误 | 算法: {algorithm} | 错误: {e.__class__.__name__}")
            return False, None

    def _verify_argon2(self, password_hash: str, password: str) -> bool:
        """执行Argon2算法验证"""
        try:
            return self.hasher.verify(password_hash, password)
        except (exceptions.VerifyMismatchError, exceptions.InvalidHashError):
            return False

    def _verify_pbkdf2(self, password_hash: str, password: str) -> bool:
        """执行PBKDF2-SHA256算法验证"""
        try:
            return check_password_hash(password_hash, password)
        except Exception as e:
            logging.error(f"PBKDF2验证异常: {str(e)}")
            return False

    def _detect_algorithm(self, password_hash: str) -> str:
        """识别密码哈希算法类型"""
        if password_hash.startswith('$argon2'):
            return 'Argon2'
        elif password_hash.startswith('pbkdf2:sha256:'):
            return 'PBKDF2-SHA256'
        return 'Unknown'

    def _validate_complexity(self, password: str):
        """执行动态密码复杂度校验"""
        comp = self.config.PASSWORD_COMPLEXITY

        # 基础长度校验
        if len(password) < self.config.PASSWORD_MIN_LENGTH:
            raise ValueError(f"密码长度不得少于{self.config.PASSWORD_MIN_LENGTH}位")

        # 动态构建正则规则
        rules = []
        if comp.get("require_uppercase",False):
            rules.append(r"(?=.*[A-Z])")
        if comp.get("require_lowercase",False):
            rules.append(r"(?=.*[a-z])")
        if comp.get("require_digit",False):
            rules.append(r"(?=.*\d)")
        if comp.get("require_symbol",False):
            escaped_symbols = re.escape(comp.get("allowed_symbols",""))
            rules.append(rf"(?=.*[{escaped_symbols}])")

        # 组合正则表达式
        # 组合正则表达式
        if rules:
            pattern = f"^{''.join(rules)}.*$"
            if not re.search(pattern, password):
                missing_rules = [
                    desc
                    for desc, rule in zip(
                        ["大写字母", "小写字母", "数字", "特殊字符"], rules
                    )
                    if rule
                ]
                raise ValueError(f"密码必须包含：{', '.join(missing_rules)}")


password_security = PasswordSecurity()
