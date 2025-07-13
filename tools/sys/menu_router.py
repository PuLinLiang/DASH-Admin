from typing import List, Dict, Any
from importlib import import_module

from ..pubilc.enum import PageType


class RouteFactory:
    def __init__(self):
        self.index_pathname = ["/", "/index"]
        self.key_set = set()  # 用于存储所有key值，确保唯一性
        self.routes = {}  # 存储所有有效路由路径
        self.public_pages: List[str] = []  # 公共页面列表
        self.menu_items = []  # 构建后的菜单项
        self.breadcrumb_map = {}  # 面包屑导航映射
        self.open_keys_map = {}  # 子菜单展开状态
        self.url_to_view_map = {}  # URL到view函数字符串映射
        self.independent_pages: List[str] = []  # 独立渲染页面映射
        self.config = None

    def load_config(self, config: List[Dict[str, Any]]):
        """加载并验证配置，然后初始化路由和菜单"""
        if not config:
            raise ValueError("配置不能为空")

        if not self._validate_config(config):
            raise ValueError("配置校验失败")
        self.config = config
        # 初始化菜单,菜单项,公共页面,独立渲染页面,面包屑导航,子菜单展开状态,url映射
        self._initialize_routes(config)
        # 初始化侧边菜单
        self._initialize_menu(config)

    def _validate_config(self, config: List[Dict[str, Any]]) -> bool:
        """校验传入的菜单配置是否符合规范"""
        try:
            for item in config:
                self._validate_menu_item(item)
            return True
        except ValueError as e:
            raise ValueError(f"[ERROR] 配置校验失败: {e}")

    def _validate_menu_item(self, item: Dict[str, Any], parent_key: str = None):
        """验证单个菜单项是否符合要求"""
        component = item.get("component")
        props = item.get("props", {})

        required_fields = ["key", "title", "icon"]
        if component == "Item":
            required_fields.extend(["href", "page_type", "view"])
        elif component == "SubMenu":
            invalid_fields = ["href", "page_type", "view", "permissions"]
            found_invalid = [field for field in invalid_fields if field in props]
            if found_invalid:
                raise ValueError(
                    f"父级菜单 [{props['key']}] 不应包含以下字段: {', '.join(found_invalid)}，请移除这些字段")

        for field in required_fields:
            if field not in props:
                raise ValueError(f"菜单项缺少必要字段 '{field}':在此菜单项中 {item}")

        key = props["key"]
        if key in self.key_set:
            raise ValueError(f"发现重复的 key '{key}'，请确保所有 key 值唯一")
        self.key_set.add(key)
        if component == "Item":
            page_type = props["page_type"]
            valid_types = [pt.value for pt in PageType]
            if page_type not in valid_types:
                raise ValueError(
                    f"菜单配置校验失败：无效的页面类型 [{page_type}]，必须为 {valid_types} 中的一种。路径：'{key}'")

            if props["href"] != key:
                raise ValueError(f"Key '{key}' 与 href '{props['href']}' 不匹配，请保持一致")

        if "children" in item:
            if component != "SubMenu":
                raise ValueError(f"只有 SubMenu 可以包含子菜单: {item}")
            for child in item["children"]:
                self._validate_menu_item(child, parent_key=key)

    def _initialize_routes(self, config: List[Dict[str, Any]]):
        """根据配置文件,初始化有效路由和公共页面等"""
        for item in config:
            self._process_menu_item(item)
            # 构建 面包屑
            self._update_breadcrumb(item)
            if "children" in item:
                if item["component"] != "SubMenu":
                    raise ValueError(f"只有 SubMenu 可以包含子菜单: {item}")
                for child in item["children"]:
                    # 构建子菜单的 对应展开的 父级菜单key
                    self._update_open_keys(child, [item["props"]["key"]])
                    # 构建子菜单 面包屑
                    self._update_breadcrumb(child, parent_key=[item["props"]["key"]])

    def _process_menu_item(self, item: Dict[str, Any]):
        """处理单个菜单项，包括 SubMenu 和 Item"""
        component = item.get("component")
        props = item.get("props", {})
        key = props["key"]
        title = props["title"]
        icon = props.get("icon", "antd-file")
        view_str = props.get("view")  # 只保存字符串，不立即解析

        if component == "Item":
            href = props["href"]
            page_type = props["page_type"]

            # 注册路由
            self.routes[key] = title
            # 存储 view 函数路径字符串，而非实际函数引用
            self.url_to_view_map[key] = view_str

            # 提取公共页面
            if page_type == PageType.PUBLIC.value:
                self.public_pages.append(key)

            # 提取独立渲染页面
            if page_type == PageType.INDEPENDENT.value:
                self.independent_pages.append(key)

        # 如果有 children，则递归处理
        if "children" in item:
            if component != "SubMenu":
                raise ValueError(f"只有 SubMenu 可以包含子菜单: {item}")
            for child in item["children"]:
                # 递归 继续处理侧边栏菜单
                self._process_menu_item(child)

    def _initialize_menu(self, config: List[Dict[str, Any]]):
        """根据配置初始化侧边栏菜单"""
        self.menu_items = []
        for item in config:
            component = item.get("component")
            props = item.get("props", {}).copy()
            show_sidebar = props.get("show_sidebar", True)
            menu_entry = {
                "component": component,
                "props": props
            }

            if component == "SubMenu" and "children" in item:
                menu_entry["children"] = []
                for child in item["children"]:
                    child_component = child.get("component")
                    child_props = child.get("props", {}).copy()
                    sidebar = child_props.get("show_sidebar", True)
                    if sidebar:
                        menu_entry["children"].append({
                            "component": child_component,
                            "props": child_props
                        })
            if show_sidebar:
                self.menu_items.append(menu_entry)

    def _update_breadcrumb(self, child: dict, parent_key: list = None):
        """更新面包屑导航"""
        path = child["props"]["key"]
        if parent_key is None:
            parent_key = []

        def find_menu_title(key):
            """递归查找菜单项的标题"""

            def recursive_search(items, target_key):
                for item in items:
                    if item["props"]["key"] == target_key:
                        return item["props"]["title"]
                    if "children" in item:
                        result = recursive_search(item["children"], target_key)
                        if result:
                            return result
                return None

            return recursive_search(self.config, key)

        breadcrumb_items = []

        # 只有当路径不是根路径 '/' 时才添加首页
        if path != "/":
            breadcrumb_items.append({"title": "首页", "key": "/", "href": "/"})

        # 添加父级路径的标题
        current_keys = parent_key.copy()
        while current_keys:
            key = current_keys.pop(0)
            title = find_menu_title(key)
            if title:
                breadcrumb_items.append({"title": title, "key": key})

        # 添加当前路径的 title（不管是否是 Item）
        current_title = find_menu_title(path)
        if current_title:
            breadcrumb_items.append({"title": current_title, "key": path})

        # 如果当前节点是 Item 或者是根路径 /，才缓存面包屑
        if child["component"] == "Item" or path == "/":
            self.breadcrumb_map[path] = breadcrumb_items.copy()

        # 如果有子菜单，继续递归处理
        if "children" in child:
            if child["component"] != "SubMenu":
                raise ValueError(f"只有 SubMenu 可以包含子菜单: {child}")
            for item in child["children"]:
                new_parent_key = parent_key + [path]  # 创建新的父级路径副本
                self._update_breadcrumb(item, new_parent_key)

    def _update_open_keys(self, child: dict, parent_key: list = None):
        """记录子菜单展开路径（支持多级）"""
        if parent_key is None:
            parent_key = []

        child_key = child["props"]["key"]

        if child["component"] == "Item":
            # 使用 setdefault 避免重复判断
            if child_key in self.open_keys_map:
                self.open_keys_map[child_key].extend(parent_key)
            else:
                self.open_keys_map[child_key] = parent_key.copy()

        if "children" in child:
            if child["component"] != "SubMenu":
                raise ValueError(f"只有 SubMenu 可以包含子菜单: {child}")
            for item in child["children"]:
                parent_key.append(child_key)
                self._update_open_keys(item, parent_key)

    def _resolve_view_function(self, view_str: str):
        """按需解析字符串形式的 view 函数（如 'views.index.render'）"""
        if not view_str:
            return None

        try:
            module_path, func_name = view_str.rsplit('.', 1)
            module = import_module(module_path)
            return getattr(module, func_name)
        except (ImportError, AttributeError, ValueError) as e:
            raise ValueError(f"无法解析 view 函数 [{view_str}]，请检查是否正确导入模块。") from e

    def _get_error_response(self, message: str):
        """返回统一格式的错误响应"""
        try:
            module = import_module("views.status_pages._500")
            view_func = getattr(module, "render", None)
            if callable(view_func):
                return view_func(message)
        except (ImportError, AttributeError):
            pass
        # 如果默认错误页也无法加载，返回基础 JSON 响应
        return {"error": message}

    def render_by_url(self, path: str, *args, **kwargs):
        """根据 URL 调用对应的 view 函数进行渲染（延迟解析）"""
        view_str = self.url_to_view_map.get(path)
        if not view_str:
            view_str = "views.status_pages.not_html.render"

        try:
            view_func = self._resolve_view_function(view_str)
            if view_func:
                return view_func(*args, **kwargs)
            else:
                return self._get_error_response("404 - 页面未找到，请检查是否有 render 函数。")
        except ImportError as e:
            print(f"[ERROR] 模块导入失败: {e}")
            return self._get_error_response("404 - 页面未找到，请检查模块路径是否正确。")
        except AttributeError as e:
            print(f"[ERROR] 找不到 render 函数: {e}")
            return self._get_error_response("404 - 页面未找到，请检查是否有 render 函数。")
        except Exception as e:
            print(f"[ERROR] 页面渲染失败: {e}")
            return self._get_error_response(f"500 - 内部服务器错误：{str(e)}")

    def get_valid_routes(self) -> dict:
        """获取有效路由"""
        return self.routes

    def get_public_pages(self) -> list:
        """获取公共页面列表"""
        return self.public_pages

    def get_sidebar_menu(self) -> list:
        """获取侧边栏菜单"""
        return self.menu_items

    def get_breadcrumb(self, path: str) -> list:
        """获取指定路径的面包屑导航"""
        return self.breadcrumb_map.get(path, [])

    def get_open_keys(self, path: str) -> list:
        """获取指定路径的子菜单展开键"""
        return self.open_keys_map.get(path, [])

# 创建 RouteFactory 实例
route_menu = RouteFactory()


