from sqlalchemy import text
from models.system import PageModel, PermissionsModel
from ..public.enum import  ComponentType,PageType
class RouteFactoryDB:
    
    def __init__(self, db_session):
        self.db = db_session

    def _create_page(self, route, parent_id=None):
        """创建页面记录"""

        props = route.get("props", {})
        component = route.get("component")

        # 验证必需字段
        required_fields = ["key", "title", "icon"]
        if component == "Item":
            required_fields.extend(["href", "page_type", "view"])
        elif component == "SubMenu":
            invalid_fields = ["href", "page_type", "view",]
            found_invalid = [field for field in invalid_fields if field in props]
            if found_invalid:
                raise ValueError(
                    f"路由导入数据表失败:父级菜单 [{props['key']}] 不应包含以下字段: {', '.join(found_invalid)}，请移除这些字段")
        # 创建Page记录
        page = PageModel(
            parent_id=parent_id,
            dept_id=1,
            name=props["title"],
            key=props["key"],
            url=props.get("href", None),
            icon=props.get("icon", None),
            view=props.get("view", None),  # 添加view字段
            component=ComponentType.get_by_code(component),  # 使用 ComponentType 枚举
            page_type=PageType[props.get("page_type", "standard").upper()],  # 使用 PageType 枚举
            show_sidebar=props.get("show_sidebar", True),  # 使用布尔值
            sort=props.get("sort", 0),
            create_by=1  # 假设默认创建者ID为1
        )

        self.db.add(page)
        self.db.flush()  # 获取生成的ID
        return page

    def _create_permissions(self,permissions:dict):
        """创建权限记录"""
        if not permissions:
            return []
        db_permissions = []
        for perm in permissions:
            if not isinstance(perm, dict) or "key" not in perm or "name" not in perm:
                raise ValueError(f"权限项必须为字典且包含 key 和 name 字段: {perm}")

            permission = PermissionsModel(
                dept_id=1,
                name=f"{perm['name']}",
                key=f"{perm['key']}",
                create_by=1
            )
            self.db.add(permission)
            db_permissions.append(permission)

        self.db.flush()  # 批量提交所有权限
        return db_permissions

    def create_routes(self, routes, parent_id=None):
        """创建路由"""
        for route in routes:
            # 创建当前页面
            page = self._create_page(route, parent_id)

            # 递归处理子路由
            if "children" in route and isinstance(route["children"], list):
                self.create_routes(route["children"], page.id)

        return True
    def create_permissions(self,permissions:dict):
        """创建权限字符"""
        for module_key,module_permissions in permissions.items():
            # 模块权限字符 存入数据库
            self._create_permissions(module_permissions)

# 初始化路由函数
def init_routes(db, config:list[dict],permissions:dict):
    """初始化 数据库路由"""
    try:
        # 1) 断开页面树的父子关系，避免自引用外键阻塞删除
        db.execute(text("UPDATE sys_page SET parent_id = NULL"))

        # 2) 先清空多对多关联表，避免外键阻塞
        # 角色-页面关联
        # db.execute(text("DELETE FROM sys_role_to_sys_page"))
        # # 角色-权限关联（如果存在）
        # db.execute(text("DELETE FROM sys_role_to_permission"))

        # 3) 再清空主表（顺序：先权限，再页面，避免潜在引用）
        db.execute(text("DELETE FROM sys_permission"))
        db.execute(text("DELETE FROM sys_page"))
        db.commit()
    except Exception:
        db.rollback()
        raise

    # 4) 重建：先生成页面，再生成权限
    route_factory = RouteFactoryDB(db)
    route_factory.create_routes(config)
    route_factory.create_permissions(permissions)
    print("菜单路由信息,初始化数据库成功")


