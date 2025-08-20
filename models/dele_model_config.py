from typing import Type, List, Tuple, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from models.base import Base
from .system import (
    DeptModel,
    UserModel,
    RoleModel,
    PostModel,
    role_to_dept,
    role_to_user,
    role_to_permission,
    PermissionsModel,
)


class DeleConfigManager:
    """
    删除关联配置管理器
    功能：提供模型删除前的关联关系检查配置与格式化输出
    """

    # 核心配置：模型 -> 关联关系列表
    _DELE_RELATIONS = {
        DeptModel: [
            (UserModel, "dept_id", "部门关联用户", None),
            # 多对多关系配置：(关联模型, 关系属性, 显示名称, 关联表信息)
            (
                RoleModel,
                "depts",
                "部门关联角色",
                {
                    "association_table": role_to_dept,
                    "local_id": "dept_id",
                    "remote_id": "role_id",
                },
            ),
            (PostModel, "dept_id", "部门关联岗位", None),
            (DeptModel, "parent_id", "部门子部门", None),
        ],
        UserModel: [
            (DeptModel, "leader_user_id", "管理的部门", None),
            (
                UserModel,
                "roles",
                "用户关联角色",
                {
                    "association_table": role_to_user,
                    "local_id": "user_id",
                    "remote_id": "role_id",
                },
            ),
            (PostModel, "user_id", "用户关联岗位", None),
        ],
        PostModel: [
            (UserModel, "post_id", "岗位关联用户", None),
        ],
        RoleModel: [
            (UserModel, "roles", "角色关联用户", {
                "association_table": role_to_user,
                "local_id": "role_id",
                "remote_id": "user_id",
            }),
            (DeptModel, "roles", "角色关联部门", {
                "association_table": role_to_dept,
                "local_id": "role_id",
                "remote_id": "dept_id",
            }),
            (PermissionsModel, "roles", "角色关联权限", {
                "association_table": role_to_permission,
                "local_id": "role_id",
                "remote_id": "permission_id",
            }),
        ],
        # 其他模型配置...
    }

    @classmethod
    def get_relation_config(
        cls, model: Type[Base]
    ) -> List[Tuple[Type[Base], str, str]]:
        """
        获取模型的关联关系配置（数据层）

        参数：
            model: 主模型类
        返回：
            关联配置列表，格式[(关联模型类, 外键字段, 显示名称), ...]
        """
        return cls._DELE_RELATIONS.get(model, [])

    @classmethod
    def format_relation_output(
        cls, model: Type[Base], counts: Dict[str, int]
    ) -> List[str]:
        """
        格式化关联关系输出（表现层）

        参数：
            model: 主模型类
            counts: 关联数据数量字典，格式{'模型类名.字段名': 数量}
        返回：
            格式化提示列表，如["部门用户: 5", "关联角色: 2"]
        """
        config = cls.get_relation_config(model)
        return [
            f"{display_name}: {counts.get(f'{rel_model.__name__}.{field}', 0)}"
            # 使用 * 忽略多余参数，兼容普通外键(3元组)和多对多(4元组)配置
            for rel_model, field, display_name, *_ in config
            if counts.get(f"{rel_model.__name__}.{field}", 0) > 0
        ]

    @classmethod
    def check_associations(
        cls, db: Session, model: Type[Base], obj_id: int
    ) -> Dict[str, Any]:
        """
        检查模型关联数据（统一入口）
        :param db: 数据库会话
        :param model: 模型类
        :param obj_id: 记录ID
        :return: {has_relation: bool, relations: dict, message: str}
        """
        # 1. 获取关联配置
        config = cls.get_relation_config(model)
        if not config:
            return {"has_relation": False, "relations": {}, "message": ""}

        # 2. 查询关联数据
        counts = cls._query_associations(db, model, obj_id, config)

        # 3. 格式化结果
        formatted = cls.format_relation_output(model, counts)
        has_relation = len(formatted) > 0

        return {
            "has_relation": has_relation,
            "relations": counts,
            "message": f"存在关联数据，禁止删除: {', '.join(formatted)}"
            if has_relation
            else "",
        }

    @classmethod
    def _query_associations(
        cls, db: Session, model: Type[Base], obj_id: int, config: list
    ):
        """内部查询方法（封装SQL逻辑）"""
        counts = {}
        for rel_model, field, display_name, assoc_config in config:
            if assoc_config and "association_table" in assoc_config:
                # 多对多查询
                table = assoc_config["association_table"]
                local_id = assoc_config["local_id"]
                count = db.scalar(
                    select(func.count()).where(getattr(table.c, local_id) == obj_id)
                )
            else:
                # 普通外键查询
                count = db.scalar(
                    select(func.count()).where(getattr(rel_model, field) == obj_id)
                )
            counts[f"{rel_model.__name__}.{field}"] = count
        return counts
