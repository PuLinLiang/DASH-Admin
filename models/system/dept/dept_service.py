from models.base_service import BaseService, DeptModel, OperationType
from sqlalchemy.orm import Session


class DeptService(BaseService[DeptModel]):
    def __init__(self, db: Session, current_user_id: int):
        super().__init__(db=db, model=DeptModel, current_user_id=current_user_id)

    def get_dept_tree(self) -> list[dict] | None:
        """
        获取当前用户权限范围内的部门树结构

        Returns:
            list[dict]: 树形结构数据，包含以下字段：
                - id: 部门ID
                - name: 部门名称
                - parent_id: 父部门ID
                - order_num: 显示顺序
                - children: 子部门列表
        """
        if not self.check_permission(
            action=OperationType.QUERY.code, raise_exception=False
        ):
            return None
        # 构建基础查询并应用数据范围
        stmt = self._build_base_query()
        stmt = self._apply_data_scope(stmt)

        # 添加排序条件
        stmt = stmt.order_by(DeptModel.order_num.asc())

        # 执行查询
        depts = self.db.scalars(stmt).all()

        return self._build_dept_tree(depts)

    def get_dept_tree_select(self) -> list[dict] | None:
        """
        获取当前用户权限范围内的部门树结构（用于下拉选择）

        Returns:
            list[dict]: 树形结构数据，包含以下字段：
                - id: 部门ID
                - name: 部门名称
                - parent_id: 父部门ID
                - order_num: 显示顺序
                - children: 子部门列表
        """
        depts, _ = self.get_all()
        if not depts:
            return None
        return [
            {"key": "1", "value": "1", "title": "集团总公司"},
            *[
                {
                    "key": f"{dept.id}",
                    "value": f"{dept.id}",
                    "title": f"{dept.name}",
                    "parent": f"{dept.parent_id}",
                }
                for dept in depts
                if dept.id != 1
            ],
        ]

    def create(self, **kwargs) -> DeptModel | None:
        """
        创建部门

        Args:
            **kwargs: 部门属性

        Returns:
            DeptModel | None: 创建后的部门对象或 None（如果创建失败）
        """
        if "parent_id" not in kwargs:
            raise ValueError("parent_id 不能为空")
        # 检查当前用户是否有创建部门的权限
        if not self.check_dept_ids_in_data_scope(set([int(kwargs["parent_id"])])):
            raise ValueError("您权限不足，上级部门不在权限范围内")
        return super().create(**kwargs)

    def update(self, obj_id: int, **kwargs) -> DeptModel | None:
        """
        更新部门信息

        Args:
            obj_id (int): 部门ID
            **kwargs: 更新字段

        Returns:
            DeptModel | None: 更新后的部门对象或 None（如果更新失败）
        """
        # 检查当前用户是否有更新部门的权限
        dept = self.get(int(obj_id))
        if not dept:
            raise ValueError("部门不存在")
        if "parent_id" not in kwargs:
            raise ValueError("parent_id 不能为空")
        if dept.parent_id != int(kwargs["parent_id"]):
            if not self.check_dept_ids_in_data_scope(set([int(kwargs["parent_id"])])):
                raise ValueError("您权限不足，上级部门不在权限范围内")
        return super().update(obj_id, **kwargs)
