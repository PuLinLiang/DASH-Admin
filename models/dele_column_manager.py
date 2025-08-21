class DeleColumnManager:
    """
    敏感字段排除配置管理器

    配置说明：
    - key为模型类名
    - value为要排除的字段列表
    """

    _exclude_config = {
        "UserModel": ["password_hash", "session_token", "login_ip"],
        "RoleModel": ["permissions", "data_scope_type"],
        "DeptModel": ["ancestors", "leader_id"],
        "PostModel": ["code"],
    }

    @classmethod
    def update_config(cls, model_name: str, fields: list[str]):
        """动态更新排除配置"""
        cls._exclude_config[model_name] = fields

    @classmethod
    def get_exclude_fields(cls, model_name: str) -> set[str]:
        """获取排除字段集合"""
        return set(cls._exclude_config.get(model_name, []))
