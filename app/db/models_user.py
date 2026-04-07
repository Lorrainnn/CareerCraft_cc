from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from app.db.base import Base


class UserInfo(Base):
    __tablename__ = "user_info"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password = Column(String(200), nullable=False)

    phone = Column(String(20), nullable=True, unique=True, index=True)
    email = Column(String(100), nullable=True, unique=True, index=True)

    status = Column(Integer, nullable=False, default=1)  # 1-normal, 0-disabled
    delete_flag = Column(Integer, nullable=False, default=0)  # 0-not deleted, 1-deleted

    last_login_time = Column(DateTime, nullable=True)
    created_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_time = Column(DateTime, nullable=True)
