from datetime import datetime
from typing import TYPE_CHECKING

# 导入第三方包
from sqlalchemy import String, DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, relationship, mapped_column
from flask_login import UserMixin

# 导入自定义包
from ...base import Base
from ...base_crud import BaseCrud

if TYPE_CHECKING:
    from ..role import RoleModel
    from ..post import PostModel
    from ..dept import DeptModel
from sqlalchemy import event
from sqlalchemy.orm import Mapper


class UserModel(Base, BaseCrud, UserMixin):
    """
    用户表模型

    属性:
        id: 用户ID
        dept_id: 部门ID
        post_id: 岗位ID
        leader_id: 领导ID
        user_name: 用户账号
        name: 用户昵称
        email: 邮箱
        phonenumber: 手机号
        sex: 性别
        password_hash: 密码
        status: 状态
        del_flag: 删除标志
        login_ip: 最后登录IP
        login_date: 最后登录时间
        session_token: 最后一次登录token
        create_by: 创建者
        create_time: 创建时间
        update_by: 更新者
        update_time: 更新时间
    """

    __tablename__ = "sys_user"
    __table_args__ = (
        Index("idx_dept_post_role", "dept_id", "post_id"),
        {"comment": "用户表"},
    )

    # 主键和关联字段
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="用户ID"
    )
    # 用户信息字段
    user_name: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, comment="用户账号"
    )
    avatar: Mapped[str | None] = mapped_column(String(255), comment="头像")
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="用户昵称")
    email: Mapped[str | None] = mapped_column(String(50), comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(11), comment="手机号")
    sex: Mapped[str | None] = mapped_column(String(10), comment="性别（男 女 未知）")
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_post.id"),
        default=0,
        nullable=False,
        index=True,
        comment="岗位ID",
    )
    leader_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id"), index=True, comment="领导ID"
    )

    # 安全相关字段
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码"
    )

    # 登录信息
    login_ip: Mapped[str | None] = mapped_column(String(128), comment="最后登录IP")
    login_date: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=datetime.now, comment="最后登录时间"
    )
    session_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="最后一次登录token"
    )

    # -----------------------------------------------关系定义------------------------------------
    # 部门对象
    dept: Mapped["DeptModel"] = relationship(
        back_populates="users",
        lazy="selectin",
        foreign_keys="UserModel.dept_id",  # 明确指定使用的外键
    )
    # 岗位对象
    post: Mapped["PostModel"] = relationship(
        back_populates="users", foreign_keys="UserModel.post_id", lazy="selectin"
    )
    # 管理的部门 对象,是哪些部门的管理者
    led_depts: Mapped[list["DeptModel"]] = relationship(
        back_populates="leader",
        foreign_keys="DeptModel.leader_user_id",
        lazy="selectin",  # 添加明确的加载策略
    )
    # 上级领导对象
    leader: Mapped["UserModel"] = relationship(
        foreign_keys=[leader_id],
        remote_side=[id],
        back_populates="led_users",
        lazy="selectin",
    )

    # 管理的用户对象列表,是哪些用户的上级领导
    led_users: Mapped[list["UserModel"]] = relationship(
        back_populates="leader",
        lazy="selectin",
        foreign_keys="UserModel.leader_id",
        cascade="all, delete-orphan",
    )

    # 角色列表
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary="sys_role_to_sys_user",
        back_populates="users",
        lazy="selectin",
        order_by="RoleModel.id",
    )

@event.listens_for(UserModel, 'before_insert')
@event.listens_for(UserModel, 'before_update')
def validate_user_name(mapper: Mapper, connection, target: UserModel):
    """校验用户名不能包含中文字符"""
    if target.user_name and any('\u4e00' <= char <= '\u9fff' for char in target.user_name):
        raise ValueError("用户名不能包含中文字符")
