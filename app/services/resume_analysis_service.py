from __future__ import annotations

from pydantic import BaseModel

from app.services.file_storage_service import FileStorageService
from app.services.llm_service import LlmService
from app.services.pdf_extractor import PdfExtractor
from schemas.cv_models import CvBO


CV_ANALYSIS_SYSTEM = """
你是一个专业的简历解析专家。请把非结构化简历文本转换成 CvBO 对象 JSON。
要求：
1. 字段名严格使用：name,birthDate,title,avatarUrl,summary,contact,socialLinks,educations,experiences,projects,skills,certificates,meta
2. 日期统一 yyyy-MM-dd
3. highlights.type 取值：1-工作经历，2-项目经历，3-专业技能
4. 无法确定的信息设为 null，集合为空时返回 []
5. 仅输出纯 JSON，不要 Markdown 代码块
"""


CV_ANALYSIS_USER = """
请仔细分析以下简历文本，将其转换为标准化的 CvBO 对象结构：

简历内容：
{resume_text}
"""


class ResumeAnalysisService:
    def __init__(
        self,
        file_storage_service: FileStorageService,
        pdf_extractor: PdfExtractor,
        llm_service: LlmService,
    ) -> None:
        self.file_storage_service = file_storage_service
        self.pdf_extractor = pdf_extractor
        self.llm_service = llm_service

    def analyze_resume_file(self, file_name: str, bucket_name: str | None = None) -> CvBO:
        with self.file_storage_service.download_file_by_bucket_and_name(bucket_name, file_name) as fp:
            content = fp.read()
        resume_text = self.pdf_extractor.extract_text(content)
        return self.llm_service.chat_json(
            system=CV_ANALYSIS_SYSTEM,
            user=CV_ANALYSIS_USER.format(resume_text=resume_text),
            model_class=CvBO,
        )
