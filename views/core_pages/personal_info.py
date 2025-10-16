import uuid
import time
import dash
from dash import set_props
from flask_login import current_user
import feffery_antd_components as fac
from feffery_dash_utils.style_utils import style
from dash.dependencies import Input, Output, State

from server import app
from models.system.service import UserService
from models.base import get_db
from tools.global_message import global_message
from tools.security import password_security
from tools.sys_log import dash_logger


def render():
    """渲染个人信息模态框"""

    return fac.AntdModal(
        id="personal-info-modal",
        title=fac.AntdSpace([fac.AntdIcon(icon="antd-user"), "个人信息"]),
        renderFooter=True,
        okClickClose=False,
    )


@app.callback(
    [
        Output("personal-info-modal", "children"),
        Output("personal-info-modal", "loading", allow_duplicate=True),
    ],
    Input("personal-info-modal", "visible"),
    prevent_initial_call=True,
)
def render_personal_info_modal(visible):
    """每次个人信息模态框打开后，动态更新内容"""

    if visible:
        time.sleep(0.5)
        try:
            with get_db() as db:
                # 查询当前用户信息
                user = UserService.get_user(db, current_user.id)
        except Exception as e:
            global_message("error", f"查询个人资料失败：{e}")
            dash_logger.error(
                f"查询个人资料失败：{e}",
                dash_logger.logmodule.USER,
                dash_logger.operation.QUERY,
            )
            return dash.no_update
        return [
            fac.AntdForm(
                [
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="personal-info-user-name",
                            placeholder="请输入用户名",
                            allowClear=True,
                        ),
                        label="用户名",
                        required=True,
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="personal-info-current-password",
                            placeholder="请输入当前密码",
                            mode="password",
                            allowClear=True,
                        ),
                        label="当前密码",
                        required=True,
                        tooltip="修改用户名或密码时需验证当前密码",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="personal-info-user-password",
                            placeholder="请输入新密码（至少12位，包含大小写字母、数字和特殊字符）",
                            mode="password",
                            allowClear=True,
                        ),
                        label="新密码",
                        tooltip="留空则不修改密码",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="personal-info-user_confirm-password",
                            placeholder="确认新密码",
                            mode="password",
                            allowClear=True,
                        ),
                        label="确认密码",
                        tooltip="留空则不修改密码",
                    ),
                ],
                id="personal-info-form",
                key=str(uuid.uuid4()),  # 强制刷新表单
                enableBatchControl=True,
                layout="vertical",
                values={"personal-info-user-name": user.name},
                style=style(marginTop=32),
            ),
            False,
        ]

    return dash.no_update


@app.callback(
    Input("personal-info-modal", "okCounts"),
    [State("personal-info-form", "values")],
    prevent_initial_call=True,
)
def handle_personal_info_update(okCounts, values):
    """处理个人信息更新逻辑"""

    # 获取表单数据
    values = values or {}
    user_name = values.get("personal-info-user-name")
    current_password = values.get("personal-info-current-password")
    new_password = values.get("personal-info-user-password")
    confirm_password = values.get("personal-info-user_confirm-password")

    # 基本验证
    if not user_name:
        global_message("error", "用户名不能为空")
        return

    if not current_password:
        global_message("error", "当前密码不能为空")
        return

    # 验证当前密码
    try:
        with get_db() as db:
            user = UserService.get_user(db, current_user.id)
            if not UserService.check_user_password( user.password_hash,current_password):
                global_message("error", "当前密码验证失败")
                return
    except Exception as e:
        global_message("error", f"密码验证失败：{e}")
        dash_logger.error(
            f"密码验证失败：{e}",
            dash_logger.logmodule.USER,
            dash_logger.operation.UPDATE,
        )
        return

    # 用户名修改验证
    if user_name != user.name:
        try:
            with get_db() as db:
                match_user = UserService.get_user_by_username(db, user_name)
                if match_user and match_user.id != current_user.id:
                    global_message("error", "用户名已存在")
                    return 
        except Exception as e:
            global_message("error", f"查询用户名失败：{e}")
            dash_logger.error(
                f"检查用户名重复失败：{e}",
                dash_logger.logmodule.USER,
                dash_logger.operation.QUERY,
            )
            return 

    # 密码修改验证
    if new_password or confirm_password:
        # 检查密码是否一致
        if new_password != confirm_password:
            global_message("error", "两次输入的新密码不一致")
            return 
        try:
            # 密码复杂度验证
            if not UserService.create_password_hash(new_password):
                global_message(
                    "error", "密码复杂度不足，需至少8位并包含大小写字母、数字和特殊字符"
                )
                return 
        except Exception as e:
            global_message("error", f"密码复杂度验证失败：{e}")
            return 
    # 执行更新操作
    try:
        with get_db() as db:
            user_service = UserService(db, current_user.id)
            update_data = {"name": user_name}

            # 如果提供了新密码，则更新密码
            if new_password and confirm_password and new_password == confirm_password:
                update_data["password_hash"] = password_security.generate_hash(
                    new_password
                )

            # 执行更新
            user_service.update(obj_id=current_user.id, **update_data)

        global_message("success", "用户信息更新成功")
        dash_logger.info(
            f"用户{current_user.id}更新个人信息成功",
            dash_logger.logmodule.USER,
            dash_logger.operation.UPDATE,
        )

        # 页面延时刷新
        set_props(
            "global-reload",
            {"reload": True, "delay": 2000},
        )
    except Exception as e:
        global_message("error", f"更新用户信息失败：{e}")
        dash_logger.error(
            f"更新用户信息失败：{e}",
            dash_logger.logmodule.USER,
            dash_logger.operation.UPDATE,
        )

