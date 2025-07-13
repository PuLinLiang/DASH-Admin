from typing import TYPE_CHECKING

# 导入第三方包
from sqlalchemy import Integer, String, Enum, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 导入自定义包
from ...base import Base
from ...base_crud import BaseCrud
from tools.pubilc import PageType, ComponentType


if TYPE_CHECKING:
    from ..role import RoleModel
    from ..permissions import PermissionsModel

    pass


class PageModel(Base, BaseCrud):
    __tablename__ = "sys_page"
    __table_args__ = {"comment": "页面权限表"}

    # 主键和外键
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="页面权限ID"
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("sys_page.id"),
        index=True,
        comment="父菜单ID（空为顶级菜单）",
    )

    # 页面字段
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="页面名称")
    key: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="页面标识key"
    )
    url: Mapped[str | None] = mapped_column(
        String(256), nullable=True, unique=True, comment="页面URL"
    )
    icon: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="页面图标"
    )
    view: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="页面视图 模块位置"
    )
    page_type: Mapped[PageType] = mapped_column(Enum(PageType), comment="页面类型")
    sort: Mapped[int] = mapped_column(Integer, nullable=False, comment="页面排序")
    # 菜单类型
    component: Mapped[ComponentType] = mapped_column(
        Enum(ComponentType),
        default=ComponentType.Item,
        comment="组件类型（SubMenu/Item）",
    )
    show_sidebar: Mapped[bool] = mapped_column(
        Boolean, default=ComponentType.Item, comment="是否渲染侧边栏菜单"
    )

    # 状态字段--继承
    # 审计字段--继承

    # 父菜单
    parent: Mapped["PageModel"] = relationship(remote_side=[id], lazy="selectin")
    # 子菜单列表
    children: Mapped[list["PageModel"]] = relationship(
        back_populates="parent",
        lazy="selectin",
        order_by="PageModel.sort",
        cascade="all, delete-orphan",
    )
    # 当前页面的权限列表
    permissions: Mapped[list["PermissionsModel"]] = relationship(back_populates="page")

    # 当前页面的角色列表sys_role_to_sys_page
    roles: Mapped[list["RoleModel"]] = relationship(
        "RoleModel",
        secondary="sys_role_to_sys_page",
        back_populates="pages",
        lazy="joined",
    )
