from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database.connection import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    subscription_end = Column(DateTime, nullable=True)  # Изменено с Date на DateTime
    status = Column(String, default='inactive')
    server_id = Column(String, nullable=True)  


class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True) 
    server_address = Column(String, nullable=False)
    server_port = Column(Integer)
    server_sub = Column(String, nullable=False)
    current_users = Column(Integer, default=0)
    max_users = Column(Integer, nullable=False)
    login = Column(String, nullable=False)
    password = Column(String, nullable=False)
    api = Column(String, nullable=False)  # API key для админа
    user_api = Column(String, nullable=True)  # API key для пользователя
    country = Column(String, nullable=False)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)  # Изменено с Date на DateTime