# 系统包

# 第三方包
import dash
from flask import request
from user_agents import parse
from flask_principal import Principal, RoleNeed, identity_loaded
from flask_login import LoginManager, current_user, AnonymousUserMixin

# 应用基础参数
from config.base_config import BaseConfig
from config.router_config import RouterConfig
from tools.sys import LoginUser, route_menu, page_permissions_db
from tools.sys_log.logconfig import setup_logging
from tools.sys_log import dash_logger
from tools.global_message import global_message
from models.base import get_db

app = dash.Dash(
    __name__,
    title=BaseConfig.app_title,
    suppress_callback_exceptions=True,
    compress=True,  # 隐式依赖flask-compress
    update_title=None,
)
# 创建应用路由
server = app.server
# 设置应用密钥
app.server.secret_key = BaseConfig.app_secret_key

# 设置session
app.server.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,  # 如果使用 HTTPS
    SESSION_COOKIE_SAMESITE="Lax",
    REMEMBER_COOKIE_DURATION=3600,  # 可选 remember me 时间
)

# 初始化日志系统
log_setup = setup_logging(server)
dash_logger.warning(
    "系统启动中...",
    logmodule=dash_logger.logmodule.SYSTEM,
    operation=dash_logger.operation.SYSTEM_START,
)

# 为当前应用添加flask-login用户登录管理
login_manager = LoginManager()
login_manager.init_app(app.server)

# 为当前应用添加flask-principal权限管理
principals = Principal(app.server)
# 加载路由配置,初始化侧边栏导航,和页面映射

dash_logger.warning(
    "加载路由配置,初始化菜单导航,路由映射",
    logmodule=dash_logger.logmodule.SYSTEM,
    operation=dash_logger.operation.SYSTEM_START,
)
route_menu.load_config(RouterConfig.core_side_menu)
# 初始化路由信息,权限配置 到数据库
with get_db() as db:
    page_permissions_db.init_routes(db, RouterConfig.core_side_menu)


@login_manager.user_loader
def user_loader(user_id):
    """flask-login内部专用用户加载函数"""
    # 避免非关键请求触发常规用户加载逻辑
    if any(
        [
            request.path in ["/_reload-hash", "/_dash-layout", "/_dash-dependencies"],
            request.path.startswith("/assets/"),
            request.path.startswith("/_dash-component-suites/"),
        ]
    ):
        return AnonymousUserMixin()

    # 根据当前要加载的用户id，从数据库中获取匹配用户信息
    with get_db() as db:
        match_user = LoginUser.load(db, int(user_id))
    # 处理未匹配到有效用户的情况
    if not match_user:
        return AnonymousUserMixin()
    # 当前用户实例化
    return match_user


# 定义不同用户角色
# user_permissions = {role: Permission(RoleNeed(role)) for role in AuthConfig.roles}


@identity_loaded.connect_via(app.server)
def on_identity_loaded(sender, identity):
    """flask-principal身份加载回调函数"""

    identity.user = current_user

    if hasattr(current_user, "user_role"):
        identity.provides.add(RoleNeed(current_user.user_role))


@app.server.before_request
def check_browser():
    """检查浏览器版本是否符合最低要求"""

    # 提取当前请求对应的浏览器信息
    user_agent = parse(str(request.user_agent))

    # 若浏览器版本信息有效
    if user_agent.browser.version != ():
        # IE相关浏览器直接拦截
        if user_agent.browser.family == "IE":
            return (
                "<div style='font-size: 16px; color: red; position: fixed; top: 40%; left: 50%; transform: translateX(-50%);'>"
                "请不要使用IE浏览器，或开启了IE内核兼容模式的其他浏览器访问本应用</div>"
            )
        # 基于BaseConfig.min_browser_versions配置，对相关浏览器最低版本进行检查
        for rule in BaseConfig.min_browser_versions:
            # 若当前请求对应的浏览器版本，低于声明的最低支持版本
            if (
                user_agent.browser.family == rule["browser"]
                and user_agent.browser.version[0] < rule["version"]
            ):
                return (
                    "<div style='font-size: 16px; color: red; position: fixed; top: 40%; left: 50%; transform: translateX(-50%);'>"
                    "您的{}浏览器版本低于本应用最低支持版本（{}），请升级浏览器后再访问</div>"
                ).format(rule["browser"], rule["version"])

        # 若开启了严格的浏览器类型限制
        if BaseConfig.strict_browser_type_check:
            # 若当前浏览器不在声明的浏览器范围内
            if user_agent.browser.family not in [
                rule["browser"] for rule in BaseConfig.min_browser_versions
            ]:
                return (
                    "<div style='font-size: 16px; color: red; position: fixed; top: 40%; left: 50%; transform: translateX(-50%);'>"
                    "当前浏览器类型不在支持的范围内，支持的浏览器类型有：{}</div>"
                ).format(
                    "、".join(
                        [rule["browser"] for rule in BaseConfig.min_browser_versions]
                    )
                )
