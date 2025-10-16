from typing import TYPE_CHECKING
# 导入第三方包
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.system import UserModel
# 导入自定义包
from ...base import Base
from ...base_crud import BaseCrud

if TYPE_CHECKING:
    from ..dept import DeptModel

class PostModel(Base, BaseCrud):
    __tablename__ = 'sys_post'
    __table_args__ = {'comment': '岗位表'}

    # 主键和外键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='岗位ID')

    # 岗位信息字段
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment='岗位名称')
    post_code: Mapped[str] = mapped_column(String(64), unique=True,nullable=False, comment='岗位编码')

    # 状态字段--继承

    # 审计字段--继承

    # 关系定义
    # 岗位与用户的关联关系
    users: Mapped[list['UserModel']] = relationship(
        'UserModel',
        back_populates='post',
        foreign_keys='[UserModel.post_id]',  # 明确指定外键字段
        lazy='selectin'
    )
    # 岗位与部门的关联关系
    dept: Mapped['DeptModel'] = relationship(
        'DeptModel',
        back_populates='posts',
        lazy='selectin'
    )
