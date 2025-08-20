from typing import Any
from sqlalchemy.orm import Session
from models.base_service import (
    BaseService,
    SQLAlchemyError,
    OperationType,
    select,
    func


)
from . import PermissionsModel


class PermissionsService(BaseService[PermissionsModel]):
    def __init__(self, db: Session, current_user_id: int):
        super().__init__(model=PermissionsModel, db=db, current_user_id=current_user_id)
    def get_all_by_fields(self, page: int | None = None, page_size: int | None = None, **kwargs: Any) -> tuple[list[dict] | None, int | None]:
        """
        根据字段获取权限列表
        :param page: 页码
        :param page_size: 每页数量
        :param kwargs: 过滤字段
        :return: 权限列表
        """
        try:
            if not self.check_permission(action=OperationType.QUERY.code):
                self.logger.warning(
                    f"当前用户:{self.current_user_id}无权限查看数据表:{self.model.__name__},查询字段:{kwargs}",
                    logmodule=self.logger.logmodule.BASE_SERVICE,
                    operation=self.logger.operation.QUERY,
                )
                raise PermissionError("无权限查看数据")
            # 构建查询条件 存储
            conditions = []

            # 动态添加字段条件
            for field_name, field_value in kwargs.items():
                con = self._build_field_condition(
                    cls=self.model, field_name=field_name, field_value=field_value
                )
                if con is not None:
                    conditions.append(con)
            # 构建基础查询
            stmt = self._build_base_query().where(*conditions)
            # 应用数据范围权限
            # stmt = self._apply_data_scope(stmt)
            # 总数查询
            count_query = select(func.count()).select_from(stmt.subquery())

            if page is not None and page_size is not None:
                # 分页查询
                paginated_query = stmt.offset((page - 1) * page_size).limit(page_size)
                # 执行查询
                results = self.db.scalars(paginated_query).unique().all()
                total_count = self.db.scalar(count_query)
                return results, total_count
            else:
                # 不分页查询
                results = self.db.scalars(stmt).unique().all()
                total_count = self.db.scalar(count_query)
                return results, total_count
        except SQLAlchemyError as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},动态字段查询所有数据失败,查询数据表:{self.model.__name__} ,查询字段:{kwargs},错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise
        except PermissionError:
            raise
        except Exception as e:
            self.logger.error(
                f"当前用户:{self.current_user_id},动态字段查询所有数据异常,查询数据表:{self.model.__name__} ,查询字段:{kwargs},,错误信息: {str(e)}",
                logmodule=self.logger.logmodule.BASE_SERVICE,
                operation=self.logger.operation.QUERY,
            )
            raise