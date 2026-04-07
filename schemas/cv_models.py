from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _parse_local_date(v: Any) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        # Most LLM outputs should be yyyy-MM-dd.
        try:
            return date.fromisoformat(s)
        except ValueError:
            # Best-effort fallback.
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except ValueError:
                return None
    return None


class HighlightBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[int] = None
    type: Optional[int] = None
    relatedId: Optional[int] = None
    highlight: Optional[str] = None
    sortOrder: Optional[int] = None


class ContactBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    phone: Optional[str] = None
    email: Optional[str] = None
    wechat: Optional[str] = None
    location: Optional[str] = None


class SocialLinkBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: Optional[str] = None
    url: Optional[str] = None
    sortOrder: Optional[int] = None


class EducationBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    school: Optional[str] = None
    major: Optional[str] = None
    degree: Optional[str] = None
    sortOrder: Optional[int] = None
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    description: Optional[str] = None

    @field_validator("startDate", mode="before")
    @classmethod
    def _start_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)

    @field_validator("endDate", mode="before")
    @classmethod
    def _end_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)


class ExperienceBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    role: Optional[str] = None
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    description: Optional[str] = None
    sortOrder: Optional[int] = None
    highlights: List[HighlightBO] = Field(default_factory=list)

    @field_validator("startDate", mode="before")
    @classmethod
    def _start_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)

    @field_validator("endDate", mode="before")
    @classmethod
    def _end_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)


class ProjectBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    role: Optional[str] = None
    description: Optional[str] = None
    sortOrder: Optional[int] = None
    highlights: List[HighlightBO] = Field(default_factory=list)

    @field_validator("startDate", mode="before")
    @classmethod
    def _start_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)

    @field_validator("endDate", mode="before")
    @classmethod
    def _end_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)


class SkillBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: Optional[str] = None
    name: Optional[str] = None
    level: Optional[str] = None
    sortOrder: Optional[int] = None
    highlights: List[HighlightBO] = Field(default_factory=list)


class CertificateBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[date] = None
    description: Optional[str] = None
    sortOrder: Optional[int] = None

    @field_validator("date", mode="before")
    @classmethod
    def _cert_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)


class LocaleConfigBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    locale: Optional[str] = "zh-CN"
    datePattern: Optional[str] = "yyyy.MM"
    # 为了兼容模板渲染，这里统一存成 JSON 字符串，例如 {"education":"教育经历",...}
    sectionLabels: Optional[str] = None

    @field_validator("sectionLabels", mode="before")
    @classmethod
    def _coerce_section_labels(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        # If LLM returns an object/array, convert to JSON string.
        try:
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)


class FormatMetaBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    theme: Optional[str] = None
    alignment: Optional[str] = None
    lineSpacing: Optional[float] = None
    fontFamily: Optional[str] = None
    datePattern: Optional[str] = None
    hyperlinkStyle: Optional[str] = None
    showAvatar: Optional[bool] = None
    showSocial: Optional[bool] = None
    twoColumnLayout: Optional[bool] = None
    localeConfig: Optional[LocaleConfigBO] = None


class OptimizationRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    feedback: Optional[str] = None
    score: Optional[float] = None


class CvBO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    userId: Optional[int] = None
    cvType: Optional[str] = None

    # name 是简历结构化后的必填字段。
    name: str = Field(..., min_length=1)

    birthDate: Optional[date] = None
    title: Optional[str] = None
    avatarUrl: Optional[str] = None
    summary: Optional[str] = None

    contact: Optional[ContactBO] = None
    socialLinks: List[SocialLinkBO] = Field(default_factory=list)
    educations: List[EducationBO] = Field(default_factory=list)
    experiences: List[ExperienceBO] = Field(default_factory=list)
    projects: List[ProjectBO] = Field(default_factory=list)
    skills: List[SkillBO] = Field(default_factory=list)
    certificates: List[CertificateBO] = Field(default_factory=list)

    advice: Optional[str] = None
    optimizationHistory: List[OptimizationRecord] = Field(default_factory=list)

    meta: Optional[FormatMetaBO] = None

    @field_validator("birthDate", mode="before")
    @classmethod
    def _birth_date(cls, v: Any) -> Optional[date]:
        return _parse_local_date(v)

    @field_validator("contact", mode="after")
    @classmethod
    def _validate_contact(cls, v: Optional[ContactBO]) -> Optional[ContactBO]:
        # 简历中最好至少保留一种可用联系方式。
        if v is None:
            return None
        if not (v.phone or v.email):
            # 不强行拒绝（有些简历可能缺手机号/邮箱），但保持字段存在时更可控。
            return v
        return v
