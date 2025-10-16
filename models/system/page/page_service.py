from sqlalchemy.orm import Session
from models.base_service import BaseService,T
from models.system.page.page_model import PageModel


class PageService(BaseService[PageModel]):
    def __init__(self, db: Session, current_user_id: int):
        super().__init__(model=PageModel, db=db, current_user_id=current_user_id)
        self.current_user_id = current_user_id

