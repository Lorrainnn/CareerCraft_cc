from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BIGINT,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    created_time: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)
    updated_time: Mapped[datetime | None] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    delete_flag: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Cv(Base, TimestampMixin):
    __tablename__ = "cv"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BIGINT)
    cv_type: Mapped[str | None] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date)
    title: Mapped[str | None] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(String(500))


class CvContact(Base, TimestampMixin):
    __tablename__ = "cv_contact"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100))
    wechat: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(200))


class CvSocialLink(Base, TimestampMixin):
    __tablename__ = "cv_social_link"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CvEducation(Base, TimestampMixin):
    __tablename__ = "cv_education"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    school: Mapped[str] = mapped_column(String(200), nullable=False)
    major: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(50))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CvExperience(Base, TimestampMixin):
    __tablename__ = "cv_experience"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CvProject(Base, TimestampMixin):
    __tablename__ = "cv_project"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    role: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CvHighlight(Base, TimestampMixin):
    __tablename__ = "cv_highlight"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    type: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    related_id: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True)
    highlight: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CvSkill(Base, TimestampMixin):
    __tablename__ = "cv_skill"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[str | None] = mapped_column(String(50))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CvCertificate(Base, TimestampMixin):
    __tablename__ = "cv_certificate"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(200))
    date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CvFormatMeta(Base, TimestampMixin):
    __tablename__ = "cv_format_meta"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cv_id: Mapped[int] = mapped_column(BIGINT, ForeignKey("cv.id"), nullable=False, index=True)
    theme: Mapped[str | None] = mapped_column(String(50), default="default")
    alignment: Mapped[str | None] = mapped_column(String(20), default="left")
    line_spacing: Mapped[float | None] = mapped_column(Float, default=1.4)
    font_family: Mapped[str | None] = mapped_column(String(200))
    date_pattern: Mapped[str | None] = mapped_column(String(20), default="yyyy.MM")
    hyperlink_style: Mapped[str | None] = mapped_column(String(20), default="underline")
    show_avatar: Mapped[bool | None] = mapped_column(Boolean, default=False)
    show_social: Mapped[bool | None] = mapped_column(Boolean, default=True)
    two_column_layout: Mapped[bool | None] = mapped_column(Boolean, default=False)


class CvLocaleConfig(Base, TimestampMixin):
    __tablename__ = "cv_locale_config"
    __table_args__ = (UniqueConstraint("format_meta_id", "locale", name="uk_format_locale"),)

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    format_meta_id: Mapped[int] = mapped_column(
        BIGINT, ForeignKey("cv_format_meta.id"), nullable=False, index=True
    )
    locale: Mapped[str | None] = mapped_column(String(10), default="zh-CN")
    date_pattern: Mapped[str | None] = mapped_column(String(20), default="yyyy.MM")
    section_labels: Mapped[str | None] = mapped_column(String(500))


class ResumeTask(Base):
    __tablename__ = "resume_task"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    user_id: Mapped[int | None] = mapped_column(BIGINT, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(BIGINT, nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100))
    file_path: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PROCESSING")
    resume_id: Mapped[int | None] = mapped_column(BIGINT, index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    start_time: Mapped[datetime | None] = mapped_column(DateTime)
    complete_time: Mapped[datetime | None] = mapped_column(DateTime)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    delete_flag: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
