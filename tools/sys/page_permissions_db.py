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
    # 清空数据库的  页面 和权限字符
    db.query(PageModel).delete()
    db.query(PermissionsModel).delete()
    db.commit()
    # 初始化数据库 页面表  和权限表
    route_factory = RouteFactoryDB(db)
    # 页面信息存入数据库
    route_factory.create_routes(config)
    # 权限字符信息存入数据库
    route_factory.create_permissions(permissions)
    print("菜单路由信息,初始化数据库成功")


