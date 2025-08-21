# 系统包

# 第三方包
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Boolean, String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class BaseMixin:
    """
    CRUD操作和审计字段基类，集成数据范围权限控制

    包含字段:
    - status: 状态（True正常 False停用）
    - del_flag: 删除标志（True删除 False未删除）
    - create_by: 创建人ID
    - create_time: 创建时间
    - update_by: 更新人ID
    - update_time: 更新时间
    - description: 描述
    - remark: 备注
    """

    # 安全字段
    status: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="状态（True正常 False停用）"
    )
    del_flag: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="删除标志（True删除 False未删除）"
    )

    # 审计字段
    create_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("sys_user.id"), nullable=False, comment="创建者"
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False, comment="创建时间"
    )
    update_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sys_user.id"), comment="更新者"
    )
    update_time: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=datetime.now, comment="更新时间"
    )
    description: Mapped[str | None] = mapped_column(String(500), comment="描述")
    remark: Mapped[str | None] = mapped_column(String(500), comment="备注")


class BaseCrud(BaseMixin):
    # 权限控制字段（所有业务表都需要）
    dept_id: Mapped[int] = mapped_column(
        ForeignKey("sys_dept.id"),nullable=False, comment="部门ID"
    )
