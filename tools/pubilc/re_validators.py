import re
class RegexPatterns:
    """
    常用正则表达式集合
    
    Attributes:
        EMAIL: 邮箱格式验证
        PHONE: 中国大陆手机号
        ID_CARD: 身份证号（简易版）
        PASSWORD: 密码强度（8-20位含大小写和数字）
    """
    EMAIL = r'^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$'
    PHONE = r'^1[3-9]\d{9}$'
    ID_CARD = r'^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$'
    PASSWORD = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[\s\S]{8,20}$'
    USERNAME = r'^[^\u4e00-\u9fa5]+$'

class FieldValidator:
    @staticmethod
    def validate_by_regex(value: str, pattern: str) -> bool:
        """
        通用正则验证方法
        
        Args:
            value: 待验证值
            pattern: 正则表达式（从RegexPatterns获取）
            
        Returns:
            bool: 是否通过验证
        """
        return re.match(pattern, value) is not None