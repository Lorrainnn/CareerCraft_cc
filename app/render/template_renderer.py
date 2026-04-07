from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from schemas.cv_models import CvBO


class TemplateRenderer:
    def __init__(self) -> None:
        self.template_dir = Path("app/render/templates")
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def render_markdown(self, cv: CvBO) -> str:
        template = self.env.get_template("cv.md.j2")
        return template.render(self._context(cv))

    def markdown_to_html(self, markdown: str, *, two_column: bool = False, show_avatar: bool = False, show_social: bool = True) -> str:
        from commonmark import commonmark

        body = commonmark(markdown)
        css = Path("app/render/assets/style/cv.css").read_text(encoding="utf-8")
        container = "container two-column" if two_column else "container"
        avatar_cls = "show-avatar" if show_avatar else "hide-avatar"
        social_cls = "show-social" if show_social else "hide-social"
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>{css}</style>
</head>
<body class="resume-body {avatar_cls} {social_cls}">
  <div class="{container}">
    {body}
  </div>
</body>
</html>"""

    def html_to_pdf(self, html: str) -> bytes:
        try:
            from weasyprint import HTML

            return HTML(string=html, base_url=str(Path.cwd())).write_pdf()
        except Exception:
            return self._convert_with_soffice(html, "pdf")

    def html_to_docx(self, html: str) -> bytes:
        return self._convert_with_soffice(html, "docx")

    def _convert_with_soffice(self, html: str, target_ext: str) -> bytes:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            raise RuntimeError("LibreOffice/soffice not found for document conversion")
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            html_path = tmp / "resume.html"
            html_path.write_text(html, encoding="utf-8")
            subprocess.run(
                [soffice, "--headless", "--convert-to", target_ext, "--outdir", str(tmp), str(html_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            out_path = tmp / f"resume.{target_ext}"
            return out_path.read_bytes()

    def _context(self, cv: CvBO) -> dict[str, object]:
        section_labels = {}
        if cv.meta and cv.meta.localeConfig and cv.meta.localeConfig.sectionLabels:
            try:
                section_labels = json.loads(cv.meta.localeConfig.sectionLabels)
            except Exception:
                section_labels = {}
        return {
            "cv": cv,
            "section_labels": {
                "summary": section_labels.get("summary", "个人摘要"),
                "education": section_labels.get("education", "教育经历"),
                "experience": section_labels.get("experience", "实习/工作经历"),
                "project": section_labels.get("project", "项目经验"),
                "skill": section_labels.get("skill", "技能与亮点"),
                "certificate": section_labels.get("certificate", "证书与获奖"),
            },
        }
