from typing import List, Dict, Any
from .permission_config import permissionConfig
# # 路由配置参数
class RouterConfig:
    """路由配置参数配置说明:
    一、基础配置结构
    标准路由配置应包含以下核心字段：
    - `component`: 组件类型（SubMenu/Item）
    - `props`: 属性对象，包含 key/title/icon/href/page_type/view 等字段
    - `children`: 子菜单列表（仅限 SubMenu）

    二、配置要求
    - URL路径必须以斜杠开头（如 "/index", "/system/users"）
    - 页面标题应使用可读性强的字符串（如 "用户管理", "部门设置"）
    - 菜单图标推荐使用 feffery_antd_components 支持的图标名称
    - 所有路径应保持唯一性和一致性，避免冲突


    三、菜单组件字段规范
    ### component 字段
    - 类型: str
    - 取值: \"SubMenu\"（父级菜单）或 \"Item\"（子菜单项）

    ### props 字段说明

    | 字段名     | 类型   | 描述                     | 特殊要求                  |
    |------------|--------|--------------------------|---------------------------|
    | key        | str    | 页面唯一标识符（URL路径）| 必须以斜杠开头            |
    | title      | str    | 菜单标题                 |                           |
    | icon       | str    | 菜单图标                 | 默认值: \"antd-file\"       |
    | href       | str    | 页面链接地址             | 必须与 key 保持一致       |
    | page_type  | str    | 页面类型                 | public/independent/standard |
    | view       | str    | view 函数模块路径        | 格式: \"views.module_name.render\" |
    |show_sidebar| bool   | 控制是否渲染侧边栏        | 格式: "show_sidebar": True ,只需要设置"Item\"（子菜单项） |
    |permissions | str    | 关联权限模块 字符         | 格式: permissions:user 表示当前页面关联用户模块相关权限，user 来源于权限表模块名称|

    ### children 字段
    - 类型: list
    - 限制: 仅当 `component` 为 \"SubMenu\" 时才允许存在

    四、多级菜单配置规则

    ### SubMenu（父级菜单）
    - 必填字段: key, title, icon
    - 不应直接包含 href 字段
    - 使用 children 字段包含子菜单项
    - 支持通过 children 包含子菜单项

    ### Item（子菜单项）
    - 必填字段: key, title, icon, href, page_type, view
    - 支持三种页面类型:
    - public: 公共页面（无需登录即可访问）
    - independent: 独立页面（新标签页打开）
    - standard: 标准页面（主框架内渲染）
    """

    # 与应用首页对应的pathname地址
    index_pathname: str = "/index"
    # 核心页面侧边菜单完整结构
    core_side_menu: List[Dict[str, Any]] = [
        {
            "component": "Item",
            "props": {
                "title": "首页",
                "key": "/",
                "icon": "antd-home",
                "href": "/",
                "view": "views.index.render",
                "page_type": "standard",
                "show_sidebar": True,
            },
        },
        {
            "component": "SubMenu",
            "props": {
                "key": "system",
                "title": "系统管理",
                "icon": "antd-setting",
            },
            "children": [
                {
                    "component": "Item",
                    "props": {
                        "key": "/system/user",
                        "title": "用户管理",
                        "href": "/system/user",
                        "icon": "antd-user",
                        "view": "views.system.sys_user.render",
                        "page_type": "standard",
                        "show_sidebar": True,
                        "permissions": permissionConfig.permissions["user"],
                    },
                },
                { 
                    "component": "Item",
                    "props": {
                        "key": "/system/dept",
                        "title": "部门管理",
                        "href": "/system/dept",
                        "icon": "antd-team",
                        "view": "views.system.sys_dept.render",
                        "page_type": "standard",
                        "show_sidebar": True,
                        "permissions": permissionConfig.permissions["dept"],
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/system/post",
                        "title": "岗位管理",
                        "href": "/system/post",
                        "icon": "antd-idcard",
                        "view": "views.system.sys_post.render",
                        "page_type": "standard",
                        "show_sidebar": True,
                        "permissions": permissionConfig.permissions["post"],
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/system/role",
                        "title": "角色管理",
                        "href": "/system/role",
                        "icon": "antd-setting",
                        "view": "views.system.sys_role.render",
                        "page_type": "standard",
                        "show_sidebar": True,
                        "permissions": permissionConfig.permissions["role"],
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/system/permissions",
                        "title": "权限字符",
                        "href": "/system/permissions",
                        "icon": "antd-setting",
                        "view": "views.system.sys_permissions.render",
                        "page_type": "standard",
                        "show_sidebar": True,
                        "permissions": permissionConfig.permissions["permissions"],
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/system/syslog",
                        "title": "系统日志",
                        "href": "/system/syslog",
                        "icon": "antd-setting",
                        "view": "views.system.sys_log.render",
                        "page_type": "standard",
                        "show_sidebar": True,
                        "permissions": permissionConfig.permissions["log"],
                    },
                },
            ],
        },
        {
            "component": "SubMenu",
            "props": {
                "key": "system_",
                "title": "系统公开页面",
                "icon": "antd-setting",
                "show_sidebar": False,
            },
            "children": [
                {
                    "component": "Item",
                    "props": {
                        "key": "/login",
                        "title": "用户登录",
                        "href": "/login",
                        "icon": "antd-user",
                        "view": "views.login.render",
                        "page_type": "public",
                        "show_sidebar": False,
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/403",
                        "title": "403页面",
                        "href": "/403",
                        "icon": "antd-user",
                        "view": "views.status_pages._403.render",
                        "page_type": "public",
                        "show_sidebar": False,
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/404",
                        "title": "404页面",
                        "href": "/404",
                        "icon": "antd-user",
                        "view": "views.status_pages._404.render",
                        "page_type": "public",
                        "show_sidebar": False,
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/500",
                        "title": "500页面",
                        "href": "/500",
                        "icon": "antd-user",
                        "view": "views.status_pages._500.render",
                        "page_type": "public",
                        "show_sidebar": False,
                    },
                },
                {
                    "component": "Item",
                    "props": {
                        "key": "/logout",
                        "title": "用户退出",
                        "href": "/logout",
                        "icon": "antd-user",
                        "view": "",
                        "page_type": "public",
                        "show_sidebar": False,
                    },
                },
            ],
        },
    ]
