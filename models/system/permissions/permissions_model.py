from typing import  TYPE_CHECKING
# 第三方包
from sqlalchemy import (
    Integer,
    ForeignKey, String

)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# 自定义包
from models.base import Base
from models.base_crud import BaseCrud

if TYPE_CHECKING:
    from ..role import RoleModel
    from ..page import PageModel

class PermissionsModel(Base, BaseCrud):
    """
    权限表

    属性:
        id: 权限ID
        page_id: 页面唯一标识
        key: 权限字符标识
        name: 权限名称
        create_by: 创建者
        create_time: 创建时间
        update_by: 更新者
        update_time: 更新时间
    """

    __tablename__ = "sys_permission"
    __table_args__ = {"comment": "权限表"}

    # 主键 外键 字段
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="权限ID")
    page_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_page.id"),nullable=False,   comment="当前权限对应的页面ID")
    # 操作权限字段
    key: Mapped[str] = mapped_column(String(50),  comment="操作权限字符如 uer:view ")
    name: Mapped[str] = mapped_column(String(50), comment="权限名称")
    # 审计字段-----继承

    # --------------------------------------------关系定义
    # 关联的角色
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary="sys_role_to_permission",
        back_populates="permissions",
        lazy="selectin",  # 添加明确的加载策略
    )
    page: Mapped["PageModel"] = relationship(
        back_populates="permissions",
        lazy="selectin",  # 添加明确的加载策略
    )
