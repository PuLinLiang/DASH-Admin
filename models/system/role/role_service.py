from typing import Any
from sqlalchemy.orm import Session
from models.base_service import (
    BaseService,
    exists,
    select,
    SQLAlchemyError,
    OperationType,
    func,
)
from models.system.dept.dept_service import DeptService
from models.system.permissions.permissons_service import PermissionsService

from . import RoleModel


class RoleService(BaseService[RoleModel]):
    def __init__(self, db: Session, current_user_id: int):
        super().__init__(model=RoleModel, db=db, current_user_id=current_user_id)

    def get_all_by_fields(
        self, page: int | None = None, page_size: int | None = None, **kwargs: Any
    ) -> tuple[list[dict] | None, int | None]:
        """
        根据多个字段条件获取所有匹配的数据（带权限校验）

        参数:
            page: 页码
            page_size: 每页数量
            **fields: 字段条件字典（如name='张三', dept_id=1）

        返回:
            数据对象列表 或 空列表（无权限或无匹配时）,
            总记录数
        """

        try:
            if not self.check_permission(action=OperationType.QUERY.code):
                self.logger.warning(
                    f"当前用户:{self.current_user_id}无权限查看数据表:{self.model.__name__},查询字段:{kwargs}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.QUERY,
                )
                raise PermissionError("无权限查看数据")
            # 构建查询条件 存储
            conditions = []

            # 动态添加字段条件
            for field_name, field_value in kwargs.items():
                con = self._build_field_condition(
                    cls=self.model, field_name=field_name, field_value=field_value
                )
                if con is not None:
                    conditions.append(con)
            # 构建基础查询
            stmt = self._build_base_query().where(*conditions)
            # 过滤部门查询
            if "dept_id" in kwargs and isinstance(kwargs["dept_id"], list):
                dept_id = set(kwargs.get("dept_id", []))
                role_ids_subquery = self._get_roles_by_depts(dept_id)
                stmt = stmt.where(
                    exists().where(self.model.id == role_ids_subquery.c.role_id)
                )
            # 应用数据范围权限
            stmt = self._apply_data_scope(stmt)
            # 总数查询
            count_query = select(func.count()).select_from(stmt.subquery())

            if page is not None and page_size is not None:
                # 分页查询
                paginated_query = stmt.offset((page - 1) * page_size).limit(page_size)
                # 执行查询
                results = self.db.scalars(paginated_query).unique().all()
                total_count = self.db.scalar(count_query)
                return results, total_count
            else:
                # 不分页查询
                results = self.db.scalars(stmt).unique().all()
                total_count = self.db.scalar(count_query)
                return results, total_count
        except SQLAlchemyError as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},动态字段查询所有数据失败,查询数据表:{self.model.__name__} ,查询字段:{kwargs},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise
        except PermissionError:
            raise
        except Exception as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},动态字段查询所有数据异常,查询数据表:{self.model.__name__} ,查询字段:{kwargs},,错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise

    def get_role_dept_tree(self, role_id: int) -> list[dict] | None:
        """
        获取角色部门树

        参数:
            role_id: 角色ID

        返回:
            角色部门树
        """
        role = self.get(role_id)
        if not role:
            return None
        tree_data = self._build_dept_tree(role.depts)
        return tree_data

    def create(self, **kwargs) -> RoleModel:
        """
        创建角色

        参数:
            **kwargs: 角色字段字典

        返回:
            角色对象
        """
        if "dept_id" not in kwargs:
            raise ValueError("部门ID 字段无效或者未传入")
        if "dept_id" in kwargs:
            dept_id = kwargs.get("dept_id", None)
            if dept_id is None:
                raise ValueError("部门ID不能为空")
            dept_id = [int(d) for d in dept_id]

            """ 判断当前角色是否在 当前用户范围内 """
            if not self.check_dept_ids_in_data_scope(set(dept_id)):
                raise PermissionError("您权限不足，部门不在权限范围内")

        """获取部门 """
        dept_service = DeptService(db=self.db, current_user_id=self.current_user_id)
        depts, _ = dept_service.get_all_by_fields(id=dept_id)
        if not depts:
            raise ValueError("部门不存在")

        kwargs.pop("dept_id")
        role = super().create(**kwargs)
        role.depts = depts
        return role

    def update(self, obj_id: int, **kwargs) -> RoleModel:
        """
        更新角色

        参数:
            obj_id: 角色ID
            **kwargs: 角色字段字典

        返回:
            角色对象
        """
        if "dept_id" not in kwargs:
            raise ValueError("部门ID 字段无效或者未传入")
        if "dept_id" in kwargs:
            dept_id = kwargs.get("dept_id", None)
            if dept_id is None:
                raise ValueError("部门ID不能为空")
            dept_id = [int(d) for d in dept_id]
            """ 判断当前角色是否在 当前用户范围内 """
            if not self.check_dept_ids_in_data_scope(set(dept_id)):
                raise PermissionError("您权限不足，部门不在权限范围内")

        """获取部门 """
        dept_service = DeptService(db=self.db, current_user_id=self.current_user_id)
        depts, _ = dept_service.get_all_by_fields(id=dept_id)
        if not depts:
            raise ValueError("部门不存在")

        kwargs.pop("dept_id")
        role = super().update(obj_id=obj_id, **kwargs)
        role.depts = depts
        return role

    def configure_permissions(
        self, role_id: int, permission_keys: list[str], dept_ids: list[int],data_scope_type
    ) -> tuple[int | None, int | None]:
        """
        配置角色的权限和数据范围

        参数:
            role_id: 角色ID
            permission_keys: 权限标识列表
            dept_ids: 部门ID列表
            data_scope_type: 数据范围类型

        返回:
            tuple[int, int]: 权限数量和部门数量

        异常:
            PermissionError: 无权限时抛出
            ValueError: 角色不存在或参数无效时抛出
        """
        # 权限校验
        if not self.check_permission(action=OperationType.UPDATE.code):
            raise PermissionError("无权限配置角色权限")
        if not data_scope_type or not role_id or not permission_keys or not dept_ids:
            raise ValueError("数据范围类型、角色ID、权限标识列表、部门ID列表不能为空")
        # 获取角色
        role = self.get(role_id)
        if not role:
            raise ValueError(f"角色ID不存在: {role_id}")

        # 获取权限服务和部门服务
        per_service = PermissionsService(self.db, self.current_user_id)
        dept_service = DeptService(self.db, self.current_user_id)
        # 查询权限对象
        per_objs, per_total = per_service.get_all_by_fields(key=permission_keys)
        if not per_objs and permission_keys:
            raise ValueError(f"权限不存在: {permission_keys}")

    
        # 查询部门对象
        dept_objs, dept_total = dept_service.get_all_by_fields(id=dept_ids)
        if not dept_objs and dept_ids:
            raise ValueError(f"部门不存在: {dept_ids}")

        # 更新 数据范围
        role.data_scope_type = data_scope_type
        # 更新角色关联
        role.permissions = per_objs
        role.depts = dept_objs

        return per_total, dept_total
