from sqlalchemy.orm import Session
from app.database.models.models import User
from datetime import datetime
import uuid

class UserRepository:
    def __init__(self, db: Session):
        self.db = db


    def get_user(self, telegram_id: int):
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()
    
    def add_user(self, telegram_id: int, username: str):
        new_user = User(
            id=str(uuid.uuid4()),
            telegram_id=telegram_id,
            username=username
        )
        self.db.add(new_user)
        self.db.commit()
        return new_user
    
    def update_subscription(self, telegram_id: int, new_date: datetime):
        user = self.get_user(telegram_id)
        if user:
            user.subscription_end = new_date
            self.db.commit()
            return True
        return False
