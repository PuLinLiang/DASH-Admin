import time
import dash
from dash import set_props, dcc
from flask import request
from flask_login import login_user
import feffery_antd_components as fac
from dash.dependencies import Input, Output, State
from flask_principal import identity_changed, Identity

# 自定义 包
from server import app, BaseConfig, LoginUser, get_db, dash_logger
from models.system.service import UserService
from tools.sys import TokenManager


@app.callback(
    [Output("login-form", "helps"), Output("login-form", "validateStatuses")],
    [Input("login-button", "nClicks"), Input("login-password", "nSubmit")],
    [State("login-form", "values"), State("login-remember-me", "checked")],
    running=[
        [Output("login-button", "loading"), True, False],
    ],
    prevent_initial_call=True,
)
def handle_login(nClicks, nSubmit, values, remember_me):
    """处理用户登录逻辑"""

    time.sleep(0.25)

    values = values or {}
    # 若表单必要信息不完整
    if not (values.get("login-user-name") and values.get("login-password")):
        dash_logger.info(
            f"登录信息不完整,登录用户:{values.get('login-user-name')},ip:{request.remote_addr}",
            logmodule=dash_logger.logmodule.SYSTEM,
            operation=dash_logger.operation.LOGIN,
        )
        set_props(
            "global-message",
            {
                "children": fac.AntdMessage(
                    type="error",
                    content="请完善登录信息",
                )
            },
        )

        return [
            # 表单帮助信息
            {
                "用户名": "请输入用户名" if not values.get("login-user-name") else None,
                "密码": "请输入密码" if not values.get("login-password") else None,
            },
            # 表单帮助状态
            {
                "用户名": "error" if not values.get("login-user-name") else None,
                "密码": "error" if not values.get("login-password") else None,
            },
        ]

    # 校验用户登录信息
    # 根据用户名尝试查询用户
    with get_db() as db:
        match_user = UserService.get_user_by_username(db, values["login-user-name"])
        # 若用户不存在
        if not match_user:
            dash_logger.warning(
                f"登录用户不存在,登录用户:{values.get('login-user-name')},ip:{request.remote_addr}",
                logmodule=dash_logger.logmodule.SYSTEM,
                operation=dash_logger.operation.LOGIN,
            )
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="用户不存在",
                    )
                },
            )

            return [
                # 表单帮助信息
                {"用户名": "用户不存在"},
                # 表单帮助状态
                {"用户名": "error"},
            ]
        elif match_user.del_flag:
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="用户已被删除",
                    )
                },
            )
            return [
                # 表单帮助信息
                {"用户名": "用户已被删除"},
                # 表单帮助状态
                {"用户名": "error"},
            ]
        elif not match_user.status:
            set_props(
                "global-message",
                {
                    "children": fac.AntdMessage(
                        type="error",
                        content="用户已被停用",
                    )
                },
            )
            return [
                # 表单帮助信息
                {"用户名": "用户已被停用"},
                # 表单帮助状态
                {"用户名": "error"},
            ]

        else:
            # 校验密码

            # 若密码不正确
            if not UserService.check_user_password(
                match_user.password_hash, values["login-password"]
            ):
                dash_logger.warning(
                    f"登录密码错误,登录用户:{values.get('login-user-name')},ip:{request.remote_addr}",
                    logmodule=dash_logger.logmodule.SYSTEM,
                    operation=dash_logger.operation.LOGIN,
                )
                set_props(
                    "global-message",
                    {
                        "children": fac.AntdMessage(
                            type="error",
                            content="密码错误",
                        )
                    },
                )

                return [
                    # 表单帮助信息
                    {"密码": "密码错误"},
                    # 表单帮助状态
                    {"密码": "error"},
                ]

            # 更新用户信息表 session_token 字段
            try:
                new_session_token = TokenManager.generate_token(match_user.id)
                user = UserService.login(
                    db, match_user, token=new_session_token, ip=request.remote_addr
                )

                if not user:
                    dash_logger.error(
                        f"登录失败,登录用户:{values.get('login-user-name')},ip:{request.remote_addr}",
                        logmodule=dash_logger.logmodule.SYSTEM,
                        operation=dash_logger.operation.LOGIN,
                    )
                    set_props(
                        "global-message",
                        {
                            "children": fac.AntdMessage(
                                type="error",
                                content="登录失败",
                            )
                        },
                    )
                    return [
                        # 表单帮助信息
                        {"密码": "登录失败"},
                        # 表单帮助状态
                        {"密码": "error"},
                    ]

                # 保存用户对象到 上下文 中
                new_user = LoginUser.load(db, match_user.id)
                # 会话登录状态切换
                login_user(new_user, remember=remember_me)
                # 设置安全 Cookie
                dash.ctx.response.set_cookie(
                    BaseConfig.session_token_cookie_name,
                    new_session_token,
                    httponly=True,
                    secure=True,  # 如果使用 HTTPS
                    samesite="Lax",
                    max_age=3600,  # 可从配置中读取
                )

                # 更新用户身份信息
                identity_changed.send(app.server, identity=Identity(new_user.id))
                # 重定向至首页
                dash_logger.info(
                    f"登录成功,登录用户:{values.get('login-user-name')},ip:{request.remote_addr}",
                    logmodule=dash_logger.logmodule.SYSTEM,
                    operation=dash_logger.operation.LOGIN,
                )
                set_props(
                    "global-redirect",
                    {"children": dcc.Location(pathname="/", id="global-redirect")},
                )
                return [{}, {}]
            except Exception as e:
                dash_logger.error(
                    f"登录异常,登录用户:{values.get('login-user-name')},ip:{request.remote_addr},错误信息:{e}",
                    logmodule=dash_logger.logmodule.SYSTEM,
                    operation=dash_logger.operation.LOGIN,
                )
                dash_logger.error(
                        f"登录失败,登录用户:{values.get('login-user-name')},ip:{request.remote_addr}",
                        logmodule=dash_logger.logmodule.SYSTEM,
                        operation=dash_logger.operation.LOGIN,
                    )
                set_props(
                        "global-message",
                        {
                            "children": fac.AntdMessage(
                                type="error",
                                content="登录异常",
                            )
                        },
                    )
                return [{}, {}]