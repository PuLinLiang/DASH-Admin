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
            
    def _process_routes_incremental(self, routes, existing_pages, parent_id=None):
        """增量处理路由信息"""
        for route in routes:
            props = route.get("props", {})
            route_key = props.get("key")
            
            # 检查页面是否已存在
            if route_key in existing_pages:
                # 如果页面已存在，更新必要的字段
                page = existing_pages[route_key]
                page.name = props.get("title", page.name)
                page.icon = props.get("icon", page.icon)
                page.url = props.get("href", page.url)
                page.view = props.get("view", page.view)
                page.sort = props.get("sort", page.sort)
                page.parent_id = parent_id
                # 更新其他可能变化的字段
            else:
                # 如果页面不存在，则创建新页面
                page = self._create_page(route, parent_id)
            
            # 递归处理子路由
            if "children" in route and isinstance(route["children"], list):
                self._process_routes_incremental(route["children"], existing_pages, page.id)

    def _process_permissions_incremental(self, permissions_dict, existing_permissions):
        """增量处理权限信息"""
        for module_key, module_permissions in permissions_dict.items():
            if not module_permissions:
                continue
                
            new_permissions = []
            for perm in module_permissions:
                if not isinstance(perm, dict) or "key" not in perm or "name" not in perm:
                    raise ValueError(f"权限项必须为字典且包含 key 和 name 字段: {perm}")
                    
                perm_key = perm["key"]
                
                # 检查权限是否已存在
                if perm_key in existing_permissions:
                    # 如果权限已存在，更新名称
                    permission = existing_permissions[perm_key]
                    permission.name = perm["name"]
                else:
                    # 如果权限不存在，则创建新权限
                    permission = PermissionsModel(
                        dept_id=1,
                        name=perm["name"],
                        key=perm_key,
                        create_by=1
                    )
                    self.db.add(permission)
                    new_permissions.append(permission)
            
            # 对于新权限，执行flush以获取ID
            if new_permissions:
                self.db.flush()

# 初始化路由函数
def init_routes(db, config:list[dict],permissions:dict):
    """初始化 数据库路由"""
    # 不再清空现有数据，而是采用增量更新的方式
    # 1) 创建新的路由工厂实例
    route_factory = RouteFactoryDB(db)
    
    # 2) 获取现有的页面和权限信息
    existing_pages = {page.key: page for page in db.query(PageModel).all()}
    existing_permissions = {perm.key: perm for perm in db.query(PermissionsModel).all()}
    
    # 3) 处理页面路由的增量更新
    route_factory._process_routes_incremental(config, existing_pages)
    
    # 4) 处理权限的增量更新
    route_factory._process_permissions_incremental(permissions, existing_permissions)
    
    db.commit()
    print("菜单路由信息和权限字符初始化成功")
