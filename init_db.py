from sqlalchemy.exc import IntegrityError
from models.system import (
    UserModel,
    PageModel,
    PostModel,
    RoleModel,
    PermissionsModel,
    DeptModel,
)
from sqlalchemy.orm import Session
from models.base import Base, get_db, engine
from tools.pubilc.enum import DataScopeType
from tools.pubilc.install import init_routes
from tools.security import password_security
from config.router_config import RouterConfig


# 初始化用户
def init_base_data(db: Session):
    """
    初始化基础数据（包含事务管理和回滚机制）

    参数:
        db: 数据库会话对象
    """
    try:
        # ====================== 初始化根部门 ======================``
        root_dept = DeptModel(name="集团总公司", order_num=0, create_by=0, parent_id=0)
        db.add(root_dept)
        db.flush()  # 立即生成ID
        # ====================== 初始化岗位 ======================
        post1 = PostModel(
            name="未分配", post_code="none", create_by=1, dept_id=root_dept.id
        )
        db.add(post1)
        db.flush()
        post1.dept = root_dept
        # ====================== 初始化权限 ======================
        permin = PermissionsModel(
            page_id=1,
            name="首页查看权限",
            key="index:view",
            create_by=1,
            dept_id=root_dept.id,
        )
        db.add(permin)
        db.flush()
        # ====================== 初始化角色 ======================
        admin_role = RoleModel(
            name="超级管理员",
            role_key="admin",
            is_admin=True,
            create_by=1,
            data_scope_type=DataScopeType.ALL,
        )
        db.add(admin_role)
        db.flush()
        admin_role.permissions.append(permin)

        # ====================== 初始化管理员用户 ======================
        admin_user = UserModel(
            dept_id=root_dept.id,
            post_id=post1.id,
            user_name="admin",
            name="系统管理员",
            password_hash=password_security.generate_hash( "admin123"),
            create_by=1,
        )
        db.add(admin_user)
        db.flush()
        admin_user.roles.append(admin_role)
        db.commit()
        print("\033[92m基础数据初始化成功！\033[0m")

    except IntegrityError as e:
        db.rollback()
        print(f"\033[91m数据唯一性冲突: {str(e)}\033[0m")
    except Exception as e:
        db.rollback()
        print(f"\033[91m初始化失败: {str(e)}\033[0m")
        raise

if __name__ == "__main__":
    # 创建所有模型的表
    Base.metadata.create_all(bind=engine)
    # 获取数据库连接
    with get_db() as db:
        print("开始")
        # 初始化页面
        init_routes(db, RouterConfig.core_side_menu)
        # 初始化基础数据
        # init_base_data(db)
