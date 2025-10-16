# 导入第三方包
import dash
from flask import request
from dash import html, set_props, dcc
import feffery_antd_components as fac
import feffery_utils_components as fuc
from dash.dependencies import Input, Output, State
from flask_principal import identity_changed, AnonymousIdentity
from flask_login import current_user, logout_user, AnonymousUserMixin

from server import app, get_db, dash_logger, route_menu
from models.system.service import UserService
from tools.sys import TokenManager

from . import core
from ..status_pages import _403, _404, _500
from .. import login
from config.base_config import BaseConfig

render = lambda: fuc.FefferyTopProgress(
    [
        # 全局消息提示
        fac.Fragment(id="global-message"),
        # 全局重定向
        fac.Fragment(id="global-redirect"),
        # 全局页面刷新
        fuc.FefferyReload(id="global-reload"),
        *(
            [
                # 重复登录辅助检查轮询
                dcc.Interval(
                    id="duplicate-login-check-interval",
                    interval=BaseConfig.duplicate_login_check_interval * 1000,
                )
            ]
            # 若开启了重复登录辅助检查
            if BaseConfig.enable_duplicate_login_check
            else []
        ),
        # 根节点url监听
        fuc.FefferyLocation(id="root-url"),
        # 应用根容器
        html.Div(
            id="root-container",
        ),
    ],
    listenPropsMode="include",
    includeProps=["root-container.children", "core-container.children"],
    minimum=0.33,
    color="#1677ff",
)


def handle_root_router_error(e):
    """处理根节点路由错误"""

    set_props(
        "root-container",
        {
            "children": _500.render(e),
        },
    )


@app.callback(
    Output("root-container", "children"),
    Input("root-url", "pathname"),
    State("root-url", "trigger"),
    prevent_initial_call=True,
    on_error=handle_root_router_error,
)
def root_router(pathname, trigger):
    """根节点路由控制"""
    # 在动态路由切换时阻止根节点路由更新
    if trigger != "load":
        return dash.no_update
    # 无需校验登录状态的公共页面
    if pathname in route_menu.public_pages:
        if pathname == "/logout":
            # 注销当前用户登录状态
            with get_db() as db:
                UserService.logout(db, current_user.id)
            # 当前用户登出
            logout_user()

            # 重置当前用户身份
            identity_changed.send(
                app.server,
                identity=AnonymousIdentity(),
            )
            # 清除登录时设置的特定会话令牌Cookie
            dash.ctx.response.set_cookie(
                BaseConfig.session_token_cookie_name,
                '',
                expires=0,
                path='/',
                httponly=True,
                secure=True,
                samesite="Lax"
            )
            # 清除Flask默认会话Cookie
            dash.ctx.response.set_cookie('session', '', expires=0, path='/')
            # 重定向至登录页面
            set_props(
                "global-redirect",
                {"children": dcc.Location(pathname="/login", id="global-redirect")},
            )
            
            return dash.no_update
        elif pathname == "/login":
            if current_user.is_authenticated:
                # 已登录用户，重定向至首页
                set_props(
                    "global-redirect",
                    {"children": dcc.Location(pathname="/", id="global-redirect")},
                )
                return dash.no_update
            return login.render()
        elif pathname == "/403":
            return _403.render()
        else:
            return route_menu.render_by_url(pathname)

    # 登录状态校验：若当前用户未登录
    if not current_user.is_authenticated:
        # 重定向至登录页面
        set_props(
            "global-redirect",
            {"children": dcc.Location(pathname="/login", id="global-redirect")},
        )
        return dash.no_update

    # 检查当前访问目标pathname是否为有效页面
    if (  # 硬编码页面地址
        pathname in route_menu.routes.keys()
        # 通配模式页面地址
        # any(
        #     pattern.match(pathname)
        #     for pattern in RouterConfig.valid_pathnames.keys()
        #     if isinstance(pattern, re.Pattern)
        # )
    ):
        # 校验当前用户是否具有针对当前访问目标页面的权限
        if pathname not in current_user.role_urls:
            # 首页不受权限控制影响
            if pathname not in route_menu.index_pathname:
                # 重定向至403页面
                set_props(
                    "global-redirect",
                    {
                        "children": dcc.Location(
                            pathname="/403", id="global-redirect"
                        )
                    },
                )
                return dash.no_update
        # 处理核心功能页面渲染
        # 返回带水印的页面内容
        if BaseConfig.enable_fullscreen_watermark:
            return fac.AntdWatermark(
                core.render(current_pathname=pathname, current_user=current_user),
                # 处理水印内容生成
                content=BaseConfig.fullscreen_watermark_generator(current_user),
            )
        # 返回不带水印的页面内容
        return core.render(
            current_pathname=pathname,
            current_user=current_user,
        )
    # 返回404状态页面
    return _404.render()


@app.callback(
    Input("duplicate-login-check-interval", "n_intervals"),
    State("root-url", "pathname"),
)
def duplicate_login_check(n_intervals, pathname):
    """重复登录辅助轮询检查"""

    # 若当前页面属于无需校验登录状态的公共页面，结束检查
    if pathname in route_menu.public_pages:
        return
    # 若当前用户身份未知
    if isinstance(current_user, AnonymousUserMixin):
        # 重定向到登出页
        set_props(
            "global-redirect",
            {"children": dcc.Location(pathname="/logout", id="global-redirect")},
        )

    # 若当前用户已登录
    elif current_user.is_authenticated:
        with get_db() as db:
            match_user = UserService.get_user(db, current_user.id)
        # 若当前回调请求携带cookies中的session_token，当前用户数据库中的最新session_token不一致
        @TokenManager.prevent_duplicate_login
        def check_token():
            pass
        check_token()
