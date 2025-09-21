from sqlalchemy import Integer, String, ForeignKey, Index, event, select, update
from sqlalchemy.orm import Mapped, relationship, mapped_column
from typing import TYPE_CHECKING

# 导入自定义包
from ...base import Base, log
from ...base_crud import BaseMixin

if TYPE_CHECKING:
    from ...system import RoleModel, PostModel, UserModel


class DeptModel(Base, BaseMixin):
    """
    部门表模型

    属性:
        dept_id: 部门ID
        parent_id: 父部门ID
        leader_user_id: 负责人用户ID
        dept_name: 部门名称
        ancestors: 祖级路径
        order_num: 显示顺序
        status: 状态
        del_flag: 删除标志
        create_by: 创建者
        create_time: 创建时间
        update_by: 更新者
        update_time: 更新时间
    """

    __tablename__ = "sys_dept"
    __table_args__ = (
        Index("idx_parent_id", "parent_id"),
        Index("idx_ancestors", "dept_path"),
        {"comment": "部门表"},
    )

    # 主键和关联字段
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="部门ID"
    )
    # 部门信息字段
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="部门名称")
    dept_path: Mapped[str] = mapped_column(
        String(500),
        index=True,
        comment="部门路径，格式：.父部门ID.当前部门ID. 例如：.1.3.5.",
        nullable=False,
        default=".",
    )
    parent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sys_dept.id"),
        nullable=True,
        index=True,
        comment="直属上级部门ID(0表示根部门)",
    )
    leader_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "sys_user.id",
            name="fk_sys_dept_leader_user_id",
            use_alter=True,         # 关键：避免循环建表时的顺序问题
            ondelete="SET NULL",    # 删除用户时自动置空，避免级联删除部门
        ),
        index=True,
        comment="负责人用户ID",
    )
    order_num: Mapped[int] = mapped_column(Integer, default=0, comment="显示顺序")

    # 状态字段
    # 审计字段--继承

    # 关系定义----------------------------------------------------------

    # 父部门对象
    parent: Mapped["DeptModel"] = relationship(
        remote_side=[id],
        lazy="selectin",
        back_populates="children",
        foreign_keys="DeptModel.parent_id",
    )

    # 子部门列表
    children: Mapped[list["DeptModel"]] = relationship(
        back_populates="parent",
        lazy="selectin",  # 添加明确的加载策略
        cascade="all, delete-orphan",  # 添加级联删除
        foreign_keys="DeptModel.parent_id",
    )

    # 部门负责人用户对象
    leader: Mapped["UserModel"] = relationship(
        back_populates="led_depts",
        foreign_keys="DeptModel.leader_user_id",
        lazy="selectin",  # 添加明确的加载策略
        post_update=True,  # 关键：分两步更新，解决循环依赖刷新
    )
    # 部门 成员列表
    users: Mapped[list["UserModel"]] = relationship(
        back_populates="dept",
        lazy="selectin",
        foreign_keys="UserModel.dept_id",
        cascade="all, delete-orphan",
    )
    # 部门下的岗位列表
    posts: Mapped[list["PostModel"]] = relationship(
        foreign_keys="PostModel.dept_id", back_populates="dept", lazy="selectin"
    )
    # 部门下的角色列表
    roles: Mapped[list["RoleModel"]] = relationship(
        secondary="sys_role_to_sys_dept",
        back_populates="depts",
        lazy="selectin",
    )


@event.listens_for(DeptModel, "after_insert")
def handle_dept_path(mapper, connection, target):
    """
    处理部门路径更新
    新增时: 生成部门路径
    """
    try:
        if target.parent_id == target.id:
            # 设置父部门为1
            connection.execute(
                update(DeptModel.__table__)
                .where(DeptModel.id == target.id)
                .values(parent_id=1)
            )
        dept_path = "."
        if target.parent_id is None:
            dept_path = "."
        else:
            dept_path = connection.scalar(
                select(DeptModel.dept_path).where(DeptModel.id == target.parent_id)
            )
            if not dept_path:
                dept_path = "."
        dept_path = f"{dept_path}{target.id}."
        # 设置dept_id为当前ID
        connection.execute(
            update(DeptModel.__table__)
            .where(DeptModel.id == target.id)
            .values(dept_path=dept_path)
        )
    except Exception as e:
        log.error(f"更新部门路径失败: {str(e)}", extra={"action": "系统.部门模型"})


@event.listens_for(DeptModel, "before_update")
def before_update_dept_path(mapper, connection, target):
    """
    部门更新事件监听器 - 在部门数据更新前自动执行路径维护

    功能特性:
    1. 父部门变更时自动更新部门路径
    2. 防止循环依赖的部门结构
    3. 维护部门树形结构的完整性
    4. 支持递归更新所有后代部门（包括孙部门等）

    参数:
        mapper: SQLAlchemy映射器对象
        connection: 数据库连接对象
        target: 正在更新的Dept实例

    触发时机:
        任何对Dept表的update操作提交前
    """
    try:
        # 获取数据库数据
        new_parent_id = int(target.parent_id)
        new_id = int(target.id)
        old_parent_id = connection.scalar(
            select(DeptModel.parent_id).where(DeptModel.id == target.id)
        )

        if new_parent_id == new_id:
            # 禁止自己是自己的父部门
            target.parent_id = old_parent_id
        if isinstance(target, DeptModel) and (
            old_parent_id != new_parent_id and new_parent_id != new_id
        ):
            # 获取旧路径
            old_path = connection.scalar(
                select(DeptModel.dept_path).where(DeptModel.id == target.id)
            )

            # 生成新的部门路径
            if target.parent_id is None:  # 根部门
                new_path = f".{target.id}."
            else:
                parent_path = connection.scalar(
                    select(DeptModel.dept_path).where(DeptModel.id == target.parent_id)
                )
                if not parent_path:
                    raise ValueError(f"父部门 {target.parent_id} 的路径不存在")
                new_path = f"{parent_path}{target.id}."

            # 更新当前部门路径
            connection.execute(
                update(DeptModel)
                .where(DeptModel.id == target.id)
                .values(dept_path=new_path)
            )

            # 如果存在旧路径，则批量更新所有后代部门路径
            if old_path:
                # 查询所有后代部门
                descendants = (
                    connection.execute(
                        select(DeptModel.id, DeptModel.dept_path)
                        .where(DeptModel.dept_path.like(f"{old_path}%"))
                        .where(DeptModel.id != target.id)
                    )
                    .mappings()
                    .all()
                )

                for dept in descendants:
                    # 替换路径前缀
                    new_child_path = dept["dept_path"].replace(old_path, new_path, 1)
                    connection.execute(
                        update(DeptModel)
                        .where(DeptModel.id == dept["id"])
                        .values(dept_path=new_child_path)
                    )

    except Exception as e:
        raise ValueError(f"更新部门路径失败: {str(e)}")
