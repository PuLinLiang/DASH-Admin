from sqlalchemy import (
    Integer,
    String,
    Boolean,
    ForeignKey,
    Table,
    Column,
    JSON,
    Enum,
)
from sqlalchemy.orm import Mapped, relationship, backref, mapped_column
from typing import  TYPE_CHECKING

# 自定义包
from...base import Base
from ...base_crud import BaseMixin
from tools.public import DataScopeType
if TYPE_CHECKING:
    from ..user import UserModel
    from ..page import PageModel
    from .. import PermissionsModel
    from ..dept import DeptModel

# 角色-权限 多对多关联表
role_to_permission = Table(
    "sys_role_to_permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("sys_role.id"), primary_key=True, comment="角色ID"),
    Column("permission_id", Integer, ForeignKey("sys_permission.id"), primary_key=True, comment="权限ID"),
    comment="角色-权限，关联表",
)

# 角色-用户 多对多关联表
role_to_user = Table(
    "sys_role_to_sys_user",
    Base.metadata,
    Column(
        "role_id",
        Integer,
        ForeignKey("sys_role.id"),
        primary_key=True,
        comment="角色ID",
    ),
    Column(
        "user_id",
        Integer,
        ForeignKey("sys_user.id"),
        primary_key=True,
        comment="用户ID",
    ),
    comment="角色-用户，关联表",
)


# 角色 和 页面关联表
role_to_page = Table(
    "sys_role_to_sys_page",
    Base.metadata,
    Column(
        "role_id",
        Integer,
        ForeignKey("sys_role.id"),
        primary_key=True,
        comment="角色ID",
    ),
    Column(
        "page_id",
        Integer,
        ForeignKey("sys_page.id"),
        primary_key=True,
        comment="页面ID",
    ),
    comment="角色-页面，关联表",
)

# 角色和 部门关联表
role_to_dept = Table(
    "sys_role_to_sys_dept",
    Base.metadata,
    Column(
        "role_id",
        Integer,
        ForeignKey("sys_role.id"),
        primary_key=True,
        comment="角色ID",
    ),
    Column(
        "dept_id",
        Integer,
        ForeignKey("sys_dept.id"),
        primary_key=True,
        comment="部门ID",
    )
)

class RoleModel(Base, BaseMixin):
    """
    角色表模型

    属性:
        id: 角色ID
        name: 角色名称
        role_key: 角色标识符
        parent_id: 父角色ID
        status: 状态
        del_flag: 删除标志
        remark: 备注
        create_by: 创建者
        create_time: 创建时间
        update_by: 更新者
        update_time: 更新时间
    """

    __tablename__ = "sys_role"
    __table_args__ = {"comment": "角色信息表"}

    # 主键外键
    id: Mapped[int] = mapped_column(Integer,primary_key=True, autoincrement=True, comment="角色ID")

    # 角色信息字段
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, comment="角色名称")
    role_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="角色权限字符串")
    parent_id: Mapped[int | None] = mapped_column(Integer,ForeignKey("sys_role.id"), comment="父角色ID，用于权限继承")
    # 超级管理员
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment="是否为超级管理员")
    # 数据范围类型
    data_scope_type: Mapped[DataScopeType] = mapped_column(Enum(DataScopeType), nullable=False,comment="数据范围类型: dept|dept_with_child")
    # 审计，状态字段，删除标志字段-----继承

    # -------------------------------------------------------------关系定义-------------------------------

    # 当前角色关联的权限
    permissions: Mapped[list["PermissionsModel"]] = relationship(
        secondary=role_to_permission, back_populates="roles", lazy="selectin"
    )

    # 当前角色关联的用户
    users: Mapped[list["UserModel"]] = relationship(
        secondary=role_to_user, back_populates="roles", lazy="selectin"
    )
    # 角色继承关系（自引用）
    parent: Mapped["RoleModel"] = relationship(
        remote_side=[id],
        backref=backref("children", lazy="selectin"),
        lazy="joined",
    )
    # 当前角色关联部门
    depts: Mapped[list["DeptModel"]] = relationship(
        secondary=role_to_dept,
        back_populates="roles",
        lazy="selectin",
    )
    # 当前角色关联的页面
    pages: Mapped[list["PageModel"]] = relationship(

        secondary=role_to_page,
        back_populates="roles",
        lazy="selectin",
    )