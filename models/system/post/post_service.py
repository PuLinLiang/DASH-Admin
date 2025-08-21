

# 第三方包
from sqlalchemy.orm import Session
# 自定义包
from models.base_service import BaseService,PostModel
class PostService(BaseService[PostModel]):
    def __init__(self, db: Session, current_user_id:int):
        super().__init__(model=PostModel, db=db, current_user_id=current_user_id)