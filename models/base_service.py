from typing import TypeVar, Generic, List, Optional, Type, Any, Dict, Set
from datetime import datetime

# 第三方包
from sqlalchemy.orm import Session, selectinload, aliased
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, func, exists

# 自定义包
from models.base import Base
from tools.sys_log.logger import dash_logger
from .system import (
    UserModel,
    RoleModel,
    DeptModel,
    role_to_dept,
    PostModel,
    PermissionsModel,
    role_to_permission,
)
from tools.public.enum import DataScopeType, OperationType
from .dele_model_config import (
    DeleConfigManager,
)  # 导入删除数据时,需要检查关联数据的配置文件
from .dele_column_manager import (
    DeleColumnManager,
)  # 导入数据表敏感字段配置文件,用于数据脱敏

T = TypeVar("T", bound=Base)


class BaseService(Generic[T]):
    """
    基础服务类

    该类是所有服务类的基类，使用泛型 `T` 约束为 `Base` 模型子类，提供通用的数据库操作方法。
    包含用户上下文获取、权限校验、数据范围过滤、基础查询构建等功能，支持数据的创建、查询、更新等操作。

    主要功能：
    1. 初始化时校验模型和参数的有效性
    2. 获取当前用户的完整上下文信息
    3. 生成和校验权限标识
    4. 构建基础查询和应用数据范围过滤
    5. 提供基础的增删改查操作方法

    Attributes:
        model (Type[T]): 当前操作的数据模型类
        db (Session): SQLAlchemy 数据库会话对象
        current_user_id (int): 当前操作的用户 ID
        current_user (Optional[UserModel]): 当前用户对象
        logger: 日志记录器

    Generic:
        T: 数据模型类型，需继承自 `models.base.Base`
    """

    def __init__(self, model: Type[T], db: Session, current_user_id: int):
        if not issubclass(model, Base):
            raise TypeError("传入的不是有效数据模型")
        if not current_user_id or not db:
            raise TypeError("传入的参数为空")
        self.model = model
        self.db = db
        self.current_user_id = current_user_id
        self.current_user = None
        self.logger = dash_logger

    def _get_user_context(self):
        """
        获取当前用户的完整上下文（带角色和部门）

        返回:
            user: 用户对象
            roles: 角色对象列表
            dept: 部门对象列表
            is_admin: 是否为管理员
            data_scope_type: 数据范围类型
        """
        if not self.current_user_id or not self.db:
            return None, None, None, None,None
        if self.current_user is None:
            try:
                user = self.db.scalar(
                    select(UserModel)
                    .options(
                        selectinload(
                            UserModel.roles.and_(
                                RoleModel.status == 1, RoleModel.del_flag == 0
                            )
                        ).selectinload(RoleModel.depts)
                    )
                    .where(UserModel.id == self.current_user_id)
                    .where(UserModel.status == 1)
                    .where(UserModel.del_flag == 0)
                )
                if not user:
                    self.logger.warning(
                        f"上下文用户不存在或者禁用:user_id={self.current_user_id}",
                        logmodule=self.logger.logmodule.BASE_SERVICE,
                        operation=self.logger.operation.QUERY,
                    )
                    raise PermissionError("用户或角色信息不存在")
                # 检查是否有管理员角色
                is_admin = any(role.is_admin for role in user.roles)
                # 计算 数据范围最大权限
                data_scope_type = (
                    DataScopeType.DEPT_WITH_CHILD
                    if is_admin
                    else min(role.data_scope_type for role in user.roles)
                )
                self.current_user = (
                    user,
                    user.roles,
                    user.dept,
                    is_admin,
                    data_scope_type,
                )
            except SQLAlchemyError as e:
                self.logger.error(
                    f"用户上下文查询失败: {str(e)}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.QUERY,
                )
                raise PermissionError("用户信息查询失败")
        return self.current_user

    def _get_permission_tag(self, action: str) -> str:
        """
        根据模型和操作类型  生成 权限标识

        Args:
            action: 操作类型(query/create/update/delete)

        Returns:
            str: 权限标识符 (如  user:query)
        """
        # 将模型类名转换为蛇形命名（如UserModel -> user）
        try:
            model_name = self.model.__name__.replace("Model", "").lower()
            if model_name.startswith("sys"):
                model_name = model_name[3:]
        except Exception as e:
            self.logger.error(
                f"权限标识符生成失败: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.PERMISSION_TAG,
            )
            raise ValueError("权限标识符生成失败")
        return f"{model_name}:{action}"

    def check_permission(
        self,
        action: str | None = None,
        permission_tag: str | None = None,
        raise_exception: bool = False,
    ) -> bool:
        """
        权限校验双模式方法

        Args:
            action: 操作类型(query/create/update/delete)，与permission_tag二选一
            permission_tag: 完整权限标识符 (如user:delete)，与action二选一
            raise_exception: 校验失败时是否抛出异常(默认False)

        Returns:
            bool: 当raise_exception=False时返回校验结果
        """
        # 参数互斥校验
        try:
            if bool(action) == bool(permission_tag):
                err_msg = "必须且只能指定action或permission_tag中的一个参数"
                self.logger.warning(
                    err_msg,
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.PERMISSION_TAG,
                )
                if raise_exception:
                    raise ValueError(err_msg)
                return False
            _, roles, _, is_admin,_ = self._get_user_context()

            if is_admin:
                return True
            # 生成最终权限标识
            final_tag = (
                permission_tag if permission_tag else self._get_permission_tag(action)
            )

            # 权限校验核心逻辑
            allowed_permissions = {
                perm.key for role in roles for perm in (role.permissions or [])
            }
            has_permission = final_tag in allowed_permissions
            if not has_permission and raise_exception:
                self.logger.warning(
                    f"权限校验失败: {final_tag},缺少权限",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.PERMISSION_CHECK,
                )
                raise PermissionError(f"缺少权限: {final_tag}")
            return has_permission
        except Exception as e:
            self.logger.error(
                f"权限校验异常: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.PERMISSION_CHECK,
            )
            raise e

    def _build_base_query(self) -> select:
        """构建基础查询（包含软删除和状态过滤）"""
        return select(self.model).where(
            self.model.del_flag == 0, self.model.status.in_([0, 1])
        )

    def _apply_data_scope(self, stmt):
        """
        应用数据权限范围过滤

        Args:
            stmt (Select): SQLAlchemy 的查询语句对象，用于后续添加数据权限过滤条件

        Returns:
            Select: 应用了数据权限范围过滤后的查询语句对象

        Notes:
            1. 如果模型没有 dept_id 字段，并且模型不是 DeptModel 或 RoleModel,直接返回原查询语句
            2. 如果当前用户是管理员，则直接返回原查询语句
            3. 对于 RoleModel 和 DeptModel 模型有特殊的处理逻辑
            4. 其他普通模型通过 dept_id 字段进行数据范围过滤
        """
        # 判断模型是否有部门id字段，若没有且模型不是 DeptModel 或 RoleModel，则无需进行数据范围过滤，直接返回原查询语句
        if not hasattr(self.model, "dept_id") and self.model.__name__ not in [
            "DeptModel",
            "RoleModel",
        ]:
            return stmt
        # 获取当前用户的上下文信息，包含用户对象、角色列表、部门对象、数据范围权限和是否为管理员
        user, roles, dept, is_admin,_ = self._get_user_context()

        # 如果当前用户是管理员 或者 数据权限是全部数据，则无需进行数据范围过滤，直接返回原查询语句
        if is_admin:
            return stmt

        # 构建当前用户可访问的部门 ID 集合
        dept_ids = self._build_data_scope_condition(roles)

        # 特殊模型处理（角色/部门）
        if self.model.__name__ == "RoleModel":
            # 获取与指定部门关联的角色 ID 子查询
            role_ids_subquery = self._get_roles_by_depts(dept_ids)
            # 通过子查询过滤出符合数据权限的角色
            return stmt.where(
                exists().where(self.model.id == role_ids_subquery.c.role_id)
            )
        elif self.model.__name__ == "DeptModel":
            # 对于部门模型，直接通过部门 ID 进行过滤
            return stmt.where(self.model.id.in_(dept_ids))

        # 返回普通表查询条件，通过 dept_id 字段进行数据范围过滤
        return stmt.where(self.model.dept_id.in_(dept_ids))

    def _get_roles_by_depts(self, dept_ids: set[int]) -> select:
        """
        通过给定的部门 ID 集合，构建一个 SQLAlchemy 查询语句，用于获取与这些部门关联的角色 ID。

        该方法会对传入的部门 ID 集合进行校验，若集合为空则返回空列表；
        若集合非空，则会构建一个 SQL 查询，从 `role_to_dept` 关联表中查询出所有关联的角色 ID，
        并对结果进行去重处理。

        Args:
            dept_ids (set[int]): 部门 ID 集合，用于筛选关联的角色 ID。

        Returns:
            Union[set, Select]:
                - 当传入的 `dept_ids` 为空列表时，返回空列表 `[]`；
                - 当 `dept_ids` 非空时，返回一个 SQLAlchemy 的 `Select` 查询对象，
                该对象可用于查询与给定部门关联的角色 ID，且结果会进行去重处理。

        Notes:
            - 该方法仅构建查询语句，不会实际执行数据库查询操作。
            - 返回的 `Select` 对象可传递给 SQLAlchemy 的会话对象进行执行。
        """
        if not dept_ids:
            return set()
        return (
            select(role_to_dept.c.role_id)
            .where(role_to_dept.c.dept_id.in_(dept_ids))
            .distinct()
        )

    def _build_field_condition(
        self, cls: Type[T], field_name: str, field_value: Any
    ) -> Optional[select]:
        """
        构建单个字段的查询条件，用于 SQLAlchemy 查询。

        该方法会对输入的字段进行有效性检查，包括空值检查、字段存在性检查和类型安全校验。
        对于符合条件的字段，会根据字段名和字段值的特点构建相应的查询条件表达式。
        对于特殊字段（如列表或名称为 'name' 的字段），会采用特殊的查询策略。

        Args:
            cls (Type[T]): SQLAlchemy 模型类，用于指定查询的目标模型。
            field_name (str): 字段名称，需在模型类中存在。
            field_value (Any): 字段值，用于构建查询条件。

        Returns:
            Optional[ColumnElement]: 查询条件表达式。
                - 若字段无效（如为空、不存在或类型不匹配），则返回 None。
                - 对于特殊字段，会返回相应的特殊查询条件（如 IN 条件、模糊查询条件）。
                - 对于普通字段，返回等值查询条件。

        日志记录:
            - 当字段值为空时，记录调试日志。
            - 当字段不存在时，记录警告日志。
            - 当字段类型不匹配时，记录错误日志。
        """
        try:
            if field_name == "create_time_start" and field_value:
                return self.model.create_time >= field_value
            elif field_name == "create_time_end" and field_value:
                return self.model.create_time <= field_value
            # 字段存在性校验（优先执行）
            if not hasattr(cls, field_name):
                self.logger.warning(
                    f"当前用户[{self.current_user_id}],动态字段查询,模型[{cls.__name__}]无字段: {field_name}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.FIELD_VALIDATION,
                )
                return None
            # 获取字段元数据
            field = getattr(cls, field_name)
            # 处理空值逻辑
            if field_value is None:
                self.logger.warning(
                    f"当前用户[{self.current_user_id}],动态字段查询所有数据,模型[{cls.__name__}],字段: {field_name}值为{field_value}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.FIELD_VALIDATION,
                )
                return None

            # 处理列表类型参数
            if isinstance(field_value, list):
                return field.in_(field_value)
            # 字符串模糊查询
            if field_name == "name" and isinstance(field_value, str):
                return field.like(f"%{field_value}%")

            if field_value is not None and not isinstance(
                field_value, field.type.python_type
            ):
                self.logger.error(
                    f"字段类型校验失败: {field_name}={field_value}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.FIELD_VALIDATION,
                )
                raise TypeError(
                    f"字段[{field_name}]类型不匹配，预期{field.type.python_type.__name__}"
                )

            # 默认等值查询
            return field == field_value
        except Exception as e:
            print(str(e))
            self.logger.error(
                f"构建单个字段的查询条件异常: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.FIELD_VALIDATION,
            )

    def _build_data_scope_condition(self, roles):
        """
        根据用户角色构建数据范围查询所需的部门 ID 集合
        Args:
            roles (list): 用户角色列表，每个元素为角色对象，需包含 `depts` 属性

        Returns:
            Set[int]: 所有关联部门的ID集合

        Raises:
            Exception: 当处理过程中出现异常时，会将异常原样抛出
        """
        dept_ids: Set[int] = set()
        recursive_dept_ids: Set[int] = set()
        try:
            # 直接收集所有角色关联的部门ID
            for role in roles:
                match role.data_scope_type:
                    case DataScopeType.DEPT:
                        dept_ids.update(dept.id for dept in role.depts)
                    case DataScopeType.DEPT_WITH_CHILD:
                        recursive_dept_ids.update(dept.id for dept in role.depts)
            # 单次递归查询获取所有子部门
            if recursive_dept_ids:
                dept_ids.update(self.get_descendant_dept_ids(recursive_dept_ids))
            return dept_ids
        except Exception as e:
            self.logger.error(
                f"数据范围过滤异常: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.DATA_SCOPE_FILTER,
            )
            raise e



    def _build_dept_tree(self, depts: list[DeptModel]) -> list[dict]:
        """
        将部门列表转换为树形结构

        Args:
            depts: 部门模型列表

        Returns:
            list[dict]: 树形结构数据
        """
        # 创建ID到节点的映射
        node_map = {
            dept.id: {
                "id": str(dept.id),
                "title": dept.name,
                "name": dept.name,
                "parent_id": dept.parent_id,
                "key": str(dept.id),
                "order_num": dept.order_num,
                "status": {"tag": "正常", "color": "cyan"}
                if dept.status
                else {"tag": "停用", "color": "orange"},
                "create_time": dept.create_time.isoformat(),
                "children": [],
                "operation": [
                    {"content": "修改", "type": "link", "icon": "antd-edit"},
                    {"content": "删除", "type": "link", "icon": "antd-delete"},
                ]
                if dept.id != 1
                else [{"content": "新增", "type": "link", "icon": "antd-plus"}],
            }
            for dept in depts
        }

        # 构建树结构
        root_nodes = []
        for dept in depts:
            node = node_map[dept.id]
            if dept.parent_id == 0 or dept.parent_id not in node_map:
                root_nodes.append(node)
            else:
                parent_node = node_map.get(dept.parent_id)
                if parent_node:
                    parent_node["children"].append(node)

        # 按order_num排序
        def sort_children(node):
            node["children"].sort(key=lambda x: x["order_num"])
            for child in node["children"]:
                sort_children(child)

        for root in root_nodes:
            sort_children(root)

        return root_nodes
    def get_descendant_dept_ids(self, dept_ids: Set[int]) -> Set[int]:
        """
        获取指定部门及其所有子部门ID集合

        通过单向递归CTE查询，仅向下遍历部门树结构

        Args:
            dept_ids (Set[int]): 初始部门ID集合

        Returns:
            Set[int]: 包含以下两类部门的ID集合:
                1. 初始部门ID
                2. 所有下级部门ID(直到末级部门)

        Raises:
            SQLAlchemyError: 数据库查询异常
        """
        if not dept_ids:
            return set()
        try:
            # 构建递归CTE查询
            dept_cte = (
                select(DeptModel.id, DeptModel.parent_id)
                .where(DeptModel.id.in_(dept_ids))
                .cte(recursive=True, name="descendant_dept")
            )

            parent_alias = aliased(dept_cte, name="p")
            child_alias = aliased(DeptModel, name="c")

            # 仅向下递归查询子部门
            dept_cte = dept_cte.union_all(
                select(child_alias.id, child_alias.parent_id).join(
                    parent_alias, child_alias.parent_id == parent_alias.c.id
                )
            )

            # 单次查询获取所有子部门ID
            all_ids = self.db.scalars(
                select(dept_cte.c.id)
                .join(DeptModel, DeptModel.id == dept_cte.c.id)
                .where(DeptModel.status == 1)
                .where(DeptModel.del_flag == 0)
            ).all()
            return set(all_ids)
        except SQLAlchemyError as e:
            self.logger.error(
                f"部门ID递归查询异常: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise e

    # 比较当前部门id集合是否全在 当前用户数据范围内,有一个不在就返回false
    def check_dept_ids_in_data_scope(self, dept_ids: set[int]) -> bool:
        """
        比较当前部门id集合是否全在 当前用户数据范围内,有一个不在就返回false
        """
        _, roles, _, is_admin,_ = self._get_user_context()
        if is_admin:
            return True
        user_depts = self._build_data_scope_condition(roles)  # 获取当前用户的部门
        if not user_depts or not dept_ids:
            return False
        return dept_ids.issubset(user_depts)

    def get(self, obj_id: int) -> Optional[T]:
        """
        根据对象 ID 获取单条数据记录，并进行权限校验和数据范围过滤。

        此方法会先验证当前用户是否具备查看数据的权限，若有权限则构建基础查询，
        并应用数据范围过滤条件，最后从数据库中获取对应的单条数据记录。

        Args:
            obj_id (int): 需要获取的数据对象的 ID。

        Returns:
            Optional[T]: 获取到的数据对象，若查询失败、无权限或数据不存在则返回 None。

        Raises:
            PermissionError: 当用户无权限查看数据时抛出。
            SQLAlchemyError: 当数据库查询出现错误时抛出。
        """
        try:
            if not self.check_permission(action=OperationType.QUERY.code):
                self.logger.warning(
                    f"无权限查询数据,当前用户:{self.current_user_id},目标数据表:{self.model.__name__},目标id:{obj_id}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.PERMISSION_CHECK,
                )
                raise PermissionError("无权限查看数据")
            # 构建基础查询
            stmt = self._build_base_query().where(self.model.id == obj_id)
            # 数据范围过滤
            stmt = self._apply_data_scope(stmt)
            # 返回查询结果
            return self.db.scalar(stmt)
        except PermissionError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(
                f"数据查询失败,当前用户:{self.current_user_id},目标数据表:{self.model.__name__},目标id:{obj_id},数据库查询异常: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise
        except Exception as e:
            self.logger.error(
                f"查询数据异常,非数据库异常信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise

    @dash_logger.log_operation(
        "创建数据",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.CREATE,
    )
    def create(self, **kwargs) -> T:
        """
        创建数据记录，并自动设置审计字段。

        该方法会进行一系列验证，包括权限校验、字段存在性验证、必填字段验证、部门ID存在性验证等。
        若所有验证通过，则创建新的数据对象并添加到数据库会话中，最后刷新会话返回创建的对象。

        Args:
            **kwargs: 要创建的数据字段及对应的值。

        Returns:
            T: 创建成功的数据对象。

        Raises:
            PermissionError: 当用户无权限创建数据、未提供当前用户或无权限操作指定部门时抛出。
            ValueError: 当传入无效字段、缺失必填字段或部门ID不存在时抛出。
            SQLAlchemyError: 当数据库操作失败时抛出。
            Exception: 处理过程中出现其他异常时抛出。
        """
        try:
            if not self.check_permission(action=OperationType.CREATE.code):
                self.logger.warning(
                    f"无权限创建数据,当前用户:{self.current_user_id},创建数据表:{self.model.__name__}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.PERMISSION_CHECK,
                )
                raise PermissionError("无权限创建数据")
            # 字段存在性验证
            model_fields = {c.name for c in self.model.__table__.columns}
            invalid_fields = set(kwargs) - model_fields
            if invalid_fields:
                raise ValueError(f"无效字段: {', '.join(invalid_fields)}")

            # 必填字段验证
            required_fields = [
                c.name
                for c in self.model.__table__.columns
                if not c.nullable
                and not c.default
                and c.name not in ("id", "create_time")
            ]
            missing = [f for f in required_fields if f not in kwargs]
            if missing:
                raise ValueError(f"缺失必填字段: {', '.join(missing)}")
            if "dept_id" in kwargs:
                dept_id = kwargs.get("dept_id", None)
                if not dept_id:
                    raise ValueError(f"部门id为空: {dept_id}")
                if not self.check_dept_ids_in_data_scope(set([int(dept_id)])):
                    raise ValueError(f"部门不在当前用户数据权限范围内: {dept_id}")
            # 创建对象
            obj = self.model(**kwargs)
            self.db.add(obj)
            self.db.flush()
            return obj

        except SQLAlchemyError as e:
            self.db.rollback()
            self.logger.error(
                f"数据创建失败,当前用户:{self.current_user_id},目标数据表:{self.model.__name__},异常信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.CREATE,
            )
            raise
        except Exception as e:
            self.db.rollback()
            self.logger.error(
                f"创建数据异常,当前用户:{self.current_user_id},目标数据表:{self.model.__name__},异常信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.CREATE,
            )
            raise

    @dash_logger.log_operation(
        "更新数据{obj_id}",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.UPDATE,
    )
    def update(self, obj_id: int, **kwargs) -> T:
        """
        更新指定 ID 的数据记录，并进行权限校验。

        该方法会先验证当前用户是否具备更新数据的权限，再尝试获取目标数据对象。
        若对象存在且有权限操作 并且目标数据再当前用户数据范围内，则更新对象的指定字段，并自动设置更新人及更新时间。
        若更新过程中出现异常，会根据异常类型进行不同的日志记录和错误处理。

        Args:
            obj_id (int): 需要更新的数据记录的 ID。
            **kwargs: 需要更新的字段及对应的值。

        Returns:
            T: 更新后的数据对象。

        Raises:
            PermissionError: 当用户无权限查看、修改数据或数据不存在时抛出。
            SQLAlchemyError: 当数据库操作失败时抛出。
            Exception: 处理过程中出现其他异常时抛出。
        """
        try:
            if not self.check_permission(action=OperationType.UPDATE.code):
                raise PermissionError("无权限修改数据")
            obj = self.get(obj_id)
            if not obj:
                raise PermissionError(f"无权限或目标id:{obj_id}不存在")
            if "dept_id" in kwargs:
                dept_id = kwargs.get("dept_id", None)
                if not dept_id:
                    raise ValueError(f"部门id为空: {dept_id}")
                if not self.check_dept_ids_in_data_scope(set([int(dept_id)])):
                    raise ValueError(f"部门不在当前用户数据权限范围内: {dept_id}")
                # 自动设置更新字段
            update_data = {
                "update_by": self.current_user_id,
                "update_time": datetime.now(),
                **kwargs,
            }

            # 更新字段
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            return obj
        except PermissionError as e:
            self.logger.warning(
                f"用户{self.current_user_id}无权限更新数据表{self.model.__name__},目标id:{obj_id},{e}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.PERMISSION_CHECK,
            )
            raise
        except SQLAlchemyError as e:
            self.logger.critical(
                f"当前用户:{self.current_user_id},数据表:{self.model.__name__},目标id:{obj_id}数据更新失败: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.UPDATE,
            )
            raise
        except Exception as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},数据表:{self.model.__name__},目标id:{obj_id}更新数据异常: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.UPDATE,
            )
            raise

    @dash_logger.log_operation(
        "删除数据{obj_id}",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.DELETE,
    )
    def delete(
        self,
        obj_id: int,
    ) -> dict[str, Any] | None:
        """
        软删除数据（带权限校验和关联检查）

        该方法用于对指定ID的数据进行软删除操作，在删除前会进行权限校验，
        并检查数据是否存在关联关系。若存在关联数据，则禁止删除。

        Args:
            obj_id (int): 需要软删除的数据ID

        Returns:
            Dict[str, Any]: 操作结果字典，包含以下字段：
                - status (str): 操作状态，"success" 或 "error"
                - message (str): 操作结果描述信息
                - relations (Dict[str, int]): 关联数据统计信息，键为显示名称，值为关联数量
                - name (str): 被删除对象的名称

        Raises:
            PermissionError: 无权限时抛出
            SQLAlchemyError: 数据库操作失败时抛出
        """
        try:
            # 1. 权限校验
            if not self.check_permission(action=OperationType.DELETE.code):
                self.logger.warning(
                    f"无权限删除数据,当前用户:{self.current_user_id},目标id:{obj_id},删除数据表:{self.model.__name__}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.PERMISSION_CHECK,
                )
                raise PermissionError("无权限执行删除操作")

            # 2. 获取待删除对象
            obj = self.get(obj_id)
            if not obj:
                raise ValueError("数据不存在或已被删除")

            # 3. 调用配置类检查关联数据情况
            result = DeleConfigManager.check_associations(
                db=self.db, model=self.model, obj_id=obj_id
            )
            # 4. 存在关联数据 就返回
            if result["has_relation"]:
                raise ValueError(result["message"])

            # 6. 执行软删除
            obj.del_flag = True
            obj.update_by = self.current_user_id
            obj.update_time = datetime.now()
            self.db.commit()

            # 7. 返回成功结果
            return obj
        except PermissionError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},数据表:{self.model.__name__},目标id:{obj_id},删除数据失败,数据库错误: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.DELETE,
            )
            raise
        except Exception as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},数据表:{self.model.__name__},目标id:{obj_id},删除操作异常: {str(e)}",
                logmodule=dash_logger.logmodule.BASE_SERVICE,
                operation=dash_logger.operation.DELETE,
            )
            raise

    @dash_logger.log_operation(
        "获取下拉列表",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.QUERY,
    )
    def get_options(self) -> List[Dict[str, Any]]:
        """
        获取当前模型对应数据的下拉列表选项。

        此方法会先进行权限校验，确保当前用户有权限查看数据。
        随后调用 `get_all` 方法获取所有数据，将其转换为适合下拉选择器使用的格式。
        每个选项包含 `label` 和 `value` 两个字段，分别对应数据的名称和 ID。

        返回:
            List[Dict[str, Any]]: 下拉列表选项列表，每个选项为包含 `label` 和 `value` 的字典。
                                如果查询失败或无权限，返回空列表。

        异常:
            SQLAlchemyError: 当数据库查询出现错误时抛出。
        """
        try:
            if not self.check_permission(action=OperationType.QUERY.code):
                self.logger.warning(
                    f"当前用户:{self.current_user_id}无权限查看数据表,下拉选项列表数据表:{self.model.__name__}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.QUERY,
                )
                raise PermissionError("无权限查看数据")
            data, total = self.get_all()
            return [{"label": item.name, "value": item.id} for item in data or []]
        except SQLAlchemyError as e:
            self.logger.error(
                f"下拉列表查询失败,数据表:{self.model.__name__},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise
        except PermissionError:
            raise
        except Exception as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},下拉列表查询异常,数据表:{self.model.__name__},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise

    @dash_logger.log_operation(
        "获取所有数据",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.QUERY,
    )
    def get_all(
        self, page: int | None = None, page_size: int | None = None
    ) -> tuple[List[Type[T]] | None, int | None]:
        """
        带分页和数据范围的列表查询

        参数:
            session: 数据库会话
            current_user_id: 当前用户ID
            page: 页码（从1开始）
            page_size: 每页数量

        返回:
            tuple[结果列表, 总记录数]
        """
        try:
            if not self.check_permission(action=OperationType.QUERY.code):
                self.logger.warning(
                    f"当前用户:{self.current_user_id}无权限查看数据,{self.model.__name__}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.QUERY,
                )
                raise PermissionError("无权限查看数据")
            # 基础查询
            strm = self._build_base_query()
            # 应用数据范围 过滤
            strm = self._apply_data_scope(strm)

            # 总数查询
            count_query = select(func.count()).select_from(strm.subquery())
            # 分页查询
            # 判断是否分页,如果没有就返回所有数据
            if page is not None and page_size is not None:
                # 分页查询
                paginated_query = strm.offset((page - 1) * page_size).limit(page_size)
                results = self.db.scalars(paginated_query).unique().all()
                return list(results), self.db.scalar(count_query)
            else:
                # 不分页查询
                results = self.db.scalars(strm).unique().all()
                return list(results), self.db.scalar(count_query)
        except PermissionError:
            raise
        except SQLAlchemyError as e:
            self.logger.critical(
                f"当前用户:{self.current_user_id},查询所有数据查询失败,数据表:{self.model.__name__},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise
        except Exception as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},获取所有数据异常,数据表:{self.model.__name__},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise

    @dash_logger.log_operation(
        "根据多个字段条件获取所有匹配的数据",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.QUERY,
    )
    def get_all_by_fields(
        self,
        page: int | None = None,
        page_size: int | None = None,
        **kwargs: Any,
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

    @dash_logger.log_operation(
        "根据多个字段条件获取单条匹配的数据",
        logmodule=dash_logger.logmodule.BASE_SERVICE,
        operation=dash_logger.operation.QUERY,
    )
    def get_by_fields(self, **kwargs) -> Any:
        """
        根据动态字段查询单条数据

        参数:
            **kwargs: 查询字段键值对，如name='张三', dept_id=1

        返回:
            数据对象 或 None（无权限或不存在时）
        """
        try:
            if not self.check_permission(action=OperationType.QUERY.code):
                self.logger.warning(
                    f"当前用户:{self.current_user_id}无权限查看数据,查询表:{self.model.__name__},查询字段:{kwargs}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.QUERY,
                )
                raise PermissionError("无权限查看数据")
            # 基础查询条件
            conditions = []

            # 动态添加字段条件
            for field_name, field_value in kwargs.items():
                # 统一使用校验方法
                con = self._build_field_condition(
                    cls=self.model, field_name=field_name, field_value=field_value
                )
                if con is not None:
                    conditions.append(con)
            # 基础查询
            stmt = self._build_base_query().where(*conditions)

            # 应用数据范围
            strm = self._apply_data_scope(stmt)
            # 执行查询
            return self.db.scalar(strm)

        except PermissionError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(
                f"当前用户:{self.current_user_id}动态字段查询单条数据失败,数据表:{self.model.__name__},查询信息:{kwargs},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise
        except Exception as e:
            self.logger.error(
                f"当前用户:{self.current_user_id}动态字段查询单条数据异常,数据表:{self.model.__name__},查询信息:{kwargs},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise

    def get_user_permissions(self) -> List[PermissionsModel]:
        """
        获取当前用户关联的所有有效权限集合

        该方法利用已有的用户上下文信息，获取当前用户所有角色对应的权限，
        并过滤掉状态异常或已删除的权限，返回去重后的权限列表。

        Returns:
            List[PermissionModel]: 权限对象列表，已去重且过滤了状态和删除标志
        """
        # 获取用户上下文信息（包含已过滤的有效角色）
        user, roles, dept, is_admin,_ = self._get_user_context()
        if not roles:
            return []
        if is_admin:
            # 查询所有有效权限
            permissions = (
                self.db.query(PermissionsModel)
                .filter(
                    PermissionsModel.status == 1,  # 权限状态正常
                    PermissionsModel.del_flag == 0,  # 权限未删除
                )
                .order_by(PermissionsModel.page_id.asc())
                .distinct()
                .all()
            )
            return permissions
        # 提取所有有效角色ID
        role_ids = [role.id for role in roles]

        # 查询这些角色关联的所有有效权限
        permissions = (
            self.db.query(PermissionsModel)
            .join(
                role_to_permission,
                PermissionsModel.id == role_to_permission.c.permission_id,
            )
            .filter(
                role_to_permission.c.role_id.in_(role_ids),
                PermissionsModel.status == 1,  # 权限状态正常
                PermissionsModel.del_flag == 0,  # 权限未删除
            )
            .order_by(PermissionsModel.page_id.asc())
            .distinct()
            .all()
        )

        return permissions

