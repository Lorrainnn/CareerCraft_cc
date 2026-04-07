from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models_resume import (
    Cv,
    CvCertificate,
    CvContact,
    CvEducation,
    CvExperience,
    CvFormatMeta,
    CvHighlight,
    CvLocaleConfig,
    CvProject,
    CvSkill,
    CvSocialLink,
)
from schemas.cv_models import (
    CertificateBO,
    ContactBO,
    CvBO,
    EducationBO,
    ExperienceBO,
    FormatMetaBO,
    HighlightBO,
    LocaleConfigBO,
    ProjectBO,
    SkillBO,
    SocialLinkBO,
)


class CvRepository:
    def get_cv_list(self, db: Session, *, user_id: int, cv_type: str | None = None) -> list[Cv]:
        stmt = (
            select(Cv)
            .where(Cv.user_id == user_id, Cv.delete_flag == 0)
            .order_by(Cv.updated_time.desc())
        )
        if cv_type:
            stmt = stmt.where(Cv.cv_type == cv_type)
        return list(db.execute(stmt).scalars().all())

    def get_cv(self, db: Session, *, user_id: int, resume_id: int, cv_type: str | None = None) -> Cv | None:
        stmt = select(Cv).where(Cv.id == resume_id, Cv.user_id == user_id, Cv.delete_flag == 0)
        if cv_type:
            stmt = stmt.where(Cv.cv_type == cv_type)
        return db.execute(stmt).scalar_one_or_none()

    def save_cv(self, db: Session, cv_bo: CvBO, *, now: datetime | None = None) -> int:
        now = now or datetime.utcnow()
        cv = Cv(
            user_id=cv_bo.userId,
            cv_type=cv_bo.cvType,
            name=cv_bo.name,
            birth_date=cv_bo.birthDate,
            title=cv_bo.title,
            avatar_url=cv_bo.avatarUrl,
            summary=cv_bo.summary,
            created_time=now,
            updated_time=now,
            delete_flag=0,
        )
        db.add(cv)
        db.flush()

        if cv_bo.contact:
            db.add(
                CvContact(
                    cv_id=cv.id,
                    phone=cv_bo.contact.phone,
                    email=cv_bo.contact.email,
                    wechat=cv_bo.contact.wechat,
                    location=cv_bo.contact.location,
                    created_time=now,
                    updated_time=now,
                    delete_flag=0,
                )
            )

        for item in cv_bo.socialLinks:
            db.add(
                CvSocialLink(
                    cv_id=cv.id,
                    label=item.label or "",
                    url=item.url or "",
                    sort_order=item.sortOrder or 0,
                    created_time=now,
                    updated_time=now,
                    delete_flag=0,
                )
            )

        for item in cv_bo.educations:
            db.add(
                CvEducation(
                    cv_id=cv.id,
                    school=item.school or "",
                    major=item.major or "",
                    degree=item.degree,
                    start_date=item.startDate,
                    end_date=item.endDate,
                    description=item.description,
                    sort_order=item.sortOrder or 0,
                    created_time=now,
                    updated_time=now,
                    delete_flag=0,
                )
            )

        for item in cv_bo.experiences:
            row = CvExperience(
                cv_id=cv.id,
                type=item.type or "全职",
                company=item.company or "",
                industry=item.industry,
                role=item.role or "",
                start_date=item.startDate,
                end_date=item.endDate,
                description=item.description,
                sort_order=item.sortOrder or 0,
                created_time=now,
                updated_time=now,
                delete_flag=0,
            )
            db.add(row)
            db.flush()
            for hl in item.highlights:
                db.add(
                    CvHighlight(
                        type=1,
                        related_id=row.id,
                        highlight=hl.highlight or "",
                        sort_order=hl.sortOrder or 0,
                        created_time=now,
                        updated_time=now,
                        delete_flag=0,
                    )
                )

        for item in cv_bo.projects:
            row = CvProject(
                cv_id=cv.id,
                name=item.name or "",
                start_date=item.startDate,
                end_date=item.endDate,
                role=item.role,
                description=item.description,
                sort_order=item.sortOrder or 0,
                created_time=now,
                updated_time=now,
                delete_flag=0,
            )
            db.add(row)
            db.flush()
            for hl in item.highlights:
                db.add(
                    CvHighlight(
                        type=2,
                        related_id=row.id,
                        highlight=hl.highlight or "",
                        sort_order=hl.sortOrder or 0,
                        created_time=now,
                        updated_time=now,
                        delete_flag=0,
                    )
                )

        for item in cv_bo.skills:
            row = CvSkill(
                cv_id=cv.id,
                category=item.category,
                name=item.name or "",
                level=item.level,
                sort_order=item.sortOrder or 0,
                created_time=now,
                updated_time=now,
                delete_flag=0,
            )
            db.add(row)
            db.flush()
            for hl in item.highlights:
                db.add(
                    CvHighlight(
                        type=3,
                        related_id=row.id,
                        highlight=hl.highlight or "",
                        sort_order=hl.sortOrder or 0,
                        created_time=now,
                        updated_time=now,
                        delete_flag=0,
                    )
                )

        for item in cv_bo.certificates:
            db.add(
                CvCertificate(
                    cv_id=cv.id,
                    name=item.name or "",
                    issuer=item.issuer,
                    date=item.date,
                    description=item.description,
                    sort_order=item.sortOrder or 0,
                    created_time=now,
                    updated_time=now,
                    delete_flag=0,
                )
            )

        if cv_bo.meta:
            meta = CvFormatMeta(
                cv_id=cv.id,
                theme=cv_bo.meta.theme,
                alignment=cv_bo.meta.alignment,
                line_spacing=cv_bo.meta.lineSpacing,
                font_family=cv_bo.meta.fontFamily,
                date_pattern=cv_bo.meta.datePattern,
                hyperlink_style=cv_bo.meta.hyperlinkStyle,
                show_avatar=cv_bo.meta.showAvatar,
                show_social=cv_bo.meta.showSocial,
                two_column_layout=cv_bo.meta.twoColumnLayout,
                created_time=now,
                updated_time=now,
                delete_flag=0,
            )
            db.add(meta)
            db.flush()
            if cv_bo.meta.localeConfig:
                db.add(
                    CvLocaleConfig(
                        format_meta_id=meta.id,
                        locale=cv_bo.meta.localeConfig.locale,
                        date_pattern=cv_bo.meta.localeConfig.datePattern,
                        section_labels=cv_bo.meta.localeConfig.sectionLabels,
                        created_time=now,
                        updated_time=now,
                        delete_flag=0,
                    )
                )

        db.commit()
        db.refresh(cv)
        return int(cv.id)

    def to_cv_bo(self, db: Session, cv: Cv) -> CvBO:
        cv_id = int(cv.id)
        contact = db.execute(
            select(CvContact).where(CvContact.cv_id == cv_id, CvContact.delete_flag == 0)
        ).scalar_one_or_none()
        social = list(
            db.execute(
                select(CvSocialLink)
                .where(CvSocialLink.cv_id == cv_id, CvSocialLink.delete_flag == 0)
                .order_by(CvSocialLink.sort_order.asc(), CvSocialLink.id.asc())
            ).scalars()
        )
        educations = list(
            db.execute(
                select(CvEducation)
                .where(CvEducation.cv_id == cv_id, CvEducation.delete_flag == 0)
                .order_by(CvEducation.sort_order.asc(), CvEducation.id.asc())
            ).scalars()
        )
        experiences = list(
            db.execute(
                select(CvExperience)
                .where(CvExperience.cv_id == cv_id, CvExperience.delete_flag == 0)
                .order_by(CvExperience.sort_order.asc(), CvExperience.id.asc())
            ).scalars()
        )
        projects = list(
            db.execute(
                select(CvProject)
                .where(CvProject.cv_id == cv_id, CvProject.delete_flag == 0)
                .order_by(CvProject.sort_order.asc(), CvProject.id.asc())
            ).scalars()
        )
        skills = list(
            db.execute(
                select(CvSkill)
                .where(CvSkill.cv_id == cv_id, CvSkill.delete_flag == 0)
                .order_by(CvSkill.sort_order.asc(), CvSkill.id.asc())
            ).scalars()
        )
        certificates = list(
            db.execute(
                select(CvCertificate)
                .where(CvCertificate.cv_id == cv_id, CvCertificate.delete_flag == 0)
                .order_by(CvCertificate.sort_order.asc(), CvCertificate.id.asc())
            ).scalars()
        )
        meta = db.execute(
            select(CvFormatMeta).where(CvFormatMeta.cv_id == cv_id, CvFormatMeta.delete_flag == 0)
        ).scalar_one_or_none()
        locale = None
        if meta:
            locale = db.execute(
                select(CvLocaleConfig).where(
                    CvLocaleConfig.format_meta_id == meta.id, CvLocaleConfig.delete_flag == 0
                )
            ).scalar_one_or_none()

        def highlights(type_: int, related_id: int) -> list[HighlightBO]:
            rows = list(
                db.execute(
                    select(CvHighlight)
                    .where(
                        CvHighlight.type == type_,
                        CvHighlight.related_id == related_id,
                        CvHighlight.delete_flag == 0,
                    )
                    .order_by(CvHighlight.sort_order.asc(), CvHighlight.id.asc())
                ).scalars()
            )
            return [
                HighlightBO(
                    id=int(row.id),
                    type=row.type,
                    relatedId=row.related_id,
                    highlight=row.highlight,
                    sortOrder=row.sort_order,
                )
                for row in rows
            ]

        return CvBO(
            userId=cv.user_id,
            cvType=cv.cv_type,
            name=cv.name,
            birthDate=cv.birth_date,
            title=cv.title,
            avatarUrl=cv.avatar_url,
            summary=cv.summary,
            contact=ContactBO(
                phone=contact.phone,
                email=contact.email,
                wechat=contact.wechat,
                location=contact.location,
            )
            if contact
            else None,
            socialLinks=[
                SocialLinkBO(label=row.label, url=row.url, sortOrder=row.sort_order) for row in social
            ],
            educations=[
                EducationBO(
                    school=row.school,
                    major=row.major,
                    degree=row.degree,
                    startDate=row.start_date,
                    endDate=row.end_date,
                    description=row.description,
                    sortOrder=row.sort_order,
                )
                for row in educations
            ],
            experiences=[
                ExperienceBO(
                    type=row.type,
                    company=row.company,
                    industry=row.industry,
                    role=row.role,
                    startDate=row.start_date,
                    endDate=row.end_date,
                    description=row.description,
                    sortOrder=row.sort_order,
                    highlights=highlights(1, int(row.id)),
                )
                for row in experiences
            ],
            projects=[
                ProjectBO(
                    name=row.name,
                    startDate=row.start_date,
                    endDate=row.end_date,
                    role=row.role,
                    description=row.description,
                    sortOrder=row.sort_order,
                    highlights=highlights(2, int(row.id)),
                )
                for row in projects
            ],
            skills=[
                SkillBO(
                    category=row.category,
                    name=row.name,
                    level=row.level,
                    sortOrder=row.sort_order,
                    highlights=highlights(3, int(row.id)),
                )
                for row in skills
            ],
            certificates=[
                CertificateBO(
                    name=row.name,
                    issuer=row.issuer,
                    date=row.date,
                    description=row.description,
                    sortOrder=row.sort_order,
                )
                for row in certificates
            ],
            meta=FormatMetaBO(
                theme=meta.theme,
                alignment=meta.alignment,
                lineSpacing=meta.line_spacing,
                fontFamily=meta.font_family,
                datePattern=meta.date_pattern,
                hyperlinkStyle=meta.hyperlink_style,
                showAvatar=meta.show_avatar,
                showSocial=meta.show_social,
                twoColumnLayout=meta.two_column_layout,
                localeConfig=LocaleConfigBO(
                    locale=locale.locale if locale else "zh-CN",
                    datePattern=locale.date_pattern if locale else "yyyy.MM",
                    sectionLabels=locale.section_labels if locale else None,
                ),
            )
            if meta
            else None,
        )
