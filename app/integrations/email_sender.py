from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.settings import get_settings


def send_html_mail(to: str, subject: str, content_html: str) -> bool:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from:
        raise RuntimeError("SMTP is not configured (smtp_host/smtp_from missing).")

    if not to or not subject or not content_html:
        raise ValueError("Email parameters must not be empty.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to

    msg.attach(MIMEText(content_html, "html", "utf-8"))

    if settings.smtp_use_ssl:
        smtp: smtplib.SMTP_SSL | smtplib.SMTP = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=20)
    else:
        smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20)
        smtp.starttls()

    try:
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.smtp_from, [to], msg.as_string())
        return True
    finally:
        smtp.quit()
