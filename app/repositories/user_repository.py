from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models_user import UserInfo


class UserRepository:
    def get_by_username(self, db: Session, username: str) -> Optional[UserInfo]:
        stmt = select(UserInfo).where(
            UserInfo.username == username,
            UserInfo.delete_flag == 0,
        )
        return db.execute(stmt).scalar_one_or_none()

    def get_by_username_and_email(self, db: Session, username: str, email: str) -> Optional[UserInfo]:
        stmt = select(UserInfo).where(
            UserInfo.username == username,
            UserInfo.email == email,
            UserInfo.delete_flag == 0,
        )
        return db.execute(stmt).scalar_one_or_none()

    def count_by_username(self, db: Session, username: str) -> int:
        stmt = select(func.count()).select_from(UserInfo).where(
            UserInfo.username == username,
            UserInfo.delete_flag == 0,
        )
        return int(db.execute(stmt).scalar_one())

    def count_by_email(self, db: Session, email: str) -> int:
        stmt = select(func.count()).select_from(UserInfo).where(
            UserInfo.email == email,
            UserInfo.delete_flag == 0,
        )
        return int(db.execute(stmt).scalar_one())

    def create_user(self, db: Session, username: str, password_hash: str, email: Optional[str]) -> int:
        user = UserInfo(
            username=username,
            password=password_hash,
            email=email,
            status=1,
            delete_flag=0,
            created_time=datetime.utcnow(),
            updated_time=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return int(user.id)

    def update_password(self, db: Session, user: UserInfo, new_password_hash: str) -> bool:
        user.password = new_password_hash
        user.updated_time = datetime.utcnow()
        db.add(user)
        db.commit()
        return True

    def update_last_login_time(self, db: Session, user_id: int) -> None:
        stmt = select(UserInfo).where(UserInfo.id == user_id, UserInfo.delete_flag == 0)
        user = db.execute(stmt).scalar_one_or_none()
        if not user:
            return
        user.last_login_time = datetime.utcnow()
        user.updated_time = datetime.utcnow()
        db.add(user)
        db.commit()

    def get_by_id(self, db: Session, user_id: int) -> Optional[UserInfo]:
        stmt = select(UserInfo).where(UserInfo.id == user_id, UserInfo.delete_flag == 0)
        return db.execute(stmt).scalar_one_or_none()

