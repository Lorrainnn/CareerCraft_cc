from __future__ import annotations

import json

from pydantic import BaseModel

from app.services.llm_service import LlmService
from app.services.progress_stream import progress_broker
from app.services.rag_service import ResumeRagService
from schemas.cv_models import CvBO, OptimizationRecord
from schemas.interview_models import ReflectionResultBO
from schemas.llm_models import CvReview


CV_REVIEW_SYSTEM = """
你是一位资深招聘专家和技术面试官。请根据职位描述评估候选人简历。
输出 CvReview JSON：score(0-1), feedback(详细建议)。
必须输出纯 JSON。
"""


CV_TAILOR_SYSTEM = """
你是一位专业的简历定制专家。
请基于原始简历、审核反馈和参考模板，输出新的 CvBO JSON。
要求：
1. 绝不虚构经历
2. 可以重写 summary、描述、亮点顺序
3. meta.localeConfig.sectionLabels 必须是字符串
4. 只输出纯 JSON
"""


class OptimizationService:
    def __init__(self, llm_service: LlmService, rag_service: ResumeRagService) -> None:
        self.llm_service = llm_service
        self.rag_service = rag_service

    async def optimize(
        self,
        *,
        cv: CvBO,
        job_description: str,
        stream_id: str | None = None,
    ) -> CvBO:
        reference_templates = self.rag_service.retrieve_templates(job_description, 3)
        current = cv.model_copy(deep=True)
        current.optimizationHistory = list(current.optimizationHistory)

        for _ in range(3):
            review = self.llm_service.chat_json(
                system=CV_REVIEW_SYSTEM,
                user=(
                    "职位描述：\n"
                    + job_description
                    + "\n\n候选人简历：\n"
                    + json.dumps(current.model_dump(mode="json"), ensure_ascii=False)
                    + "\n\n参考模板：\n"
                    + "\n\n".join(reference_templates)
                ),
                model_class=CvReview,
            )
            record = OptimizationRecord(score=review.score, feedback=review.feedback)
            current.optimizationHistory.append(record)
            current.advice = review.feedback

            if stream_id:
                await progress_broker.emit(
                    stream_id,
                    "progress",
                    {
                        "message": (
                            f"✅ 简历质量达标，优化完成！最终评分: {review.score:.2f}"
                            if review.score > 0.8
                            else f"🔄 继续优化，当前评分: {review.score:.2f}，目标评分: 0.8+"
                        ),
                        "score": review.score,
                        "feedback": review.feedback,
                        "status": "COMPLETED" if review.score > 0.8 else "PROCESSING",
                    },
                )

            if review.score > 0.8:
                break

            current = self.llm_service.chat_json(
                system=CV_TAILOR_SYSTEM,
                user=(
                    "当前简历：\n"
                    + json.dumps(current.model_dump(mode="json"), ensure_ascii=False)
                    + "\n\n职位描述：\n"
                    + job_description
                    + "\n\n审核反馈：\n"
                    + json.dumps(review.model_dump(mode="json"), ensure_ascii=False)
                    + "\n\n参考模板：\n"
                    + "\n\n".join(reference_templates)
                ),
                model_class=CvBO,
            )
            current.optimizationHistory = list(current.optimizationHistory)

        return current
