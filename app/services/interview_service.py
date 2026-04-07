from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from app.services.llm_service import LlmService
from schemas.cv_models import CvBO
from schemas.interview_models import (
    InterviewCompleteBO,
    InterviewCompleteQARecordBO,
    InterviewDecision,
    InterviewPlanBO,
    InterviewProgressBO,
    InterviewProgressInfoBO,
    InterviewResponseBO,
    InterviewResponseType,
    InterviewSessionBO,
    InterviewSessionStageInfoBO,
    InterviewStageResultBO,
    InterviewState,
    InterviewStatisticsBO,
    JDAlignmentResultBO,
    ReflectionResultBO,
)


@dataclass
class QARecord:
    stage_index: int
    stage_name: str
    question: str
    answer: str
    score: int
    decision: InterviewDecision
    feedback: str
    is_probe: bool


@dataclass
class InterviewSessionContext:
    session_id: int
    resume_id: int
    user_id: int
    job_description: str
    created_time: float = field(default_factory=time.time)
    start_time: float = field(default_factory=time.time)
    jd_alignment_result: JDAlignmentResultBO | None = None
    interview_plan: InterviewPlanBO | None = None
    current_stage_index: int = 0
    current_question_index: int = 0
    current_question: str = ""
    last_user_answer: str = ""
    qa_history: list[QARecord] = field(default_factory=list)
    current_decision: InterviewDecision = InterviewDecision.NEXT
    finished_stages: list[int] = field(default_factory=list)
    probe_count: int = 0
    finished: bool = False

    def can_probe(self) -> bool:
        return self.probe_count < 3 and not self.finished


class InterviewService:
    def __init__(self, llm_service: LlmService) -> None:
        self.llm_service = llm_service
        self._sessions: dict[int, InterviewSessionContext] = {}

    def start(self, *, user_id: int, resume_id: int, job_description: str, cv: CvBO) -> InterviewResponseBO:
        session_id = abs(uuid.uuid4().int >> 96)
        context = InterviewSessionContext(
            session_id=session_id,
            resume_id=resume_id,
            user_id=user_id,
            job_description=job_description,
        )
        context.jd_alignment_result = self._align(job_description, cv)
        context.interview_plan = self._plan(job_description, cv, context.jd_alignment_result)
        context.current_question = self._next_question(context, is_probe=False)
        self._sessions[session_id] = context
        return InterviewResponseBO(
            responseType=InterviewResponseType.SESSION,
            sessionId=session_id,
            interviewState=InterviewState.IN_PROGRESS,
            session=self._session_bo(context),
        )

    def continue_session(self, session_id: int, user_answer: str) -> InterviewResponseBO:
        context = self._sessions.get(session_id)
        if not context:
            raise ValueError("会话不存在或已过期")
        if context.finished:
            return self.finish(session_id)

        reflection = self._reflect(context.current_question, user_answer)
        context.last_user_answer = user_answer
        context.current_decision = reflection.decision
        context.qa_history.append(
            QARecord(
                stage_index=context.current_stage_index,
                stage_name=self._stage_name(context),
                question=context.current_question,
                answer=user_answer,
                score=reflection.score,
                decision=reflection.decision,
                feedback=reflection.feedback,
                is_probe=reflection.decision == InterviewDecision.PROBE,
            )
        )

        if reflection.decision == InterviewDecision.FINISH:
            context.finished = True
            return self.finish(session_id)
        if reflection.decision == InterviewDecision.PROBE and context.can_probe():
            context.probe_count += 1
        elif reflection.decision == InterviewDecision.STAGE_FINISH:
            context.finished_stages.append(context.current_stage_index)
            context.current_stage_index += 1
            context.current_question_index = 0
            context.probe_count = 0
        else:
            context.current_question_index += 1
            context.probe_count = 0

        if context.current_stage_index >= len(context.interview_plan.stages):
            context.finished = True
            return self.finish(session_id)

        context.current_question = self._next_question(
            context, is_probe=reflection.decision == InterviewDecision.PROBE
        )
        return InterviewResponseBO(
            responseType=InterviewResponseType.PROGRESS,
            sessionId=session_id,
            interviewState=InterviewState.IN_PROGRESS,
            progress=self._progress_bo(context, reflection),
        )

    def status(self, session_id: int) -> InterviewResponseBO:
        context = self._sessions.get(session_id)
        if not context:
            raise ValueError("会话不存在或已过期")
        if context.finished:
            return self.finish(session_id)
        return InterviewResponseBO(
            responseType=InterviewResponseType.PROGRESS,
            sessionId=session_id,
            interviewState=InterviewState.IN_PROGRESS,
            progress=self._progress_bo(context, None),
        )

    def finish(self, session_id: int) -> InterviewResponseBO:
        context = self._sessions.get(session_id)
        if not context:
            raise ValueError("会话不存在或已过期")
        context.finished = True
        return InterviewResponseBO(
            responseType=InterviewResponseType.COMPLETE,
            sessionId=session_id,
            interviewState=InterviewState.COMPLETED,
            complete=self._complete_bo(context),
        )

    def _align(self, job_description: str, cv: CvBO) -> JDAlignmentResultBO:
        skills = {item.name for item in cv.skills if item.name}
        matched = [skill for skill in skills if skill.lower() in job_description.lower()]
        missing = []
        for kw in ["Python", "MySQL", "Redis", "Docker", "FastAPI", "SQLAlchemy"]:
            if kw.lower() in job_description.lower() and kw not in matched:
                missing.append(kw)
        score = max(0, min(100, 40 + len(matched) * 10 - len(missing) * 5))
        return JDAlignmentResultBO(
            matchScore=score,
            matchedSkills=sorted(matched),
            missingSkills=missing,
            relatedProjects=[p.name for p in cv.projects if p.name][:3],
            focusAreas=missing[:3] or sorted(matched)[:3],
            suggestion="优先围绕 JD 中高频技术栈和项目深度提问。",
        )

    def _plan(self, job_description: str, cv: CvBO, align: JDAlignmentResultBO) -> InterviewPlanBO:
        stages = [
            {
                "order": 1,
                "name": "自我介绍与项目破冰",
                "keyTopics": [p.name for p in cv.projects if p.name][:2] or ["代表项目"],
                "strategy": "从简历中最能代表候选人能力的项目切入。",
            },
            {
                "order": 2,
                "name": "Python 基础与工程实践",
                "keyTopics": align.focusAreas or ["Python", "FastAPI", "SQLAlchemy"],
                "strategy": "从候选人真实经验延展到框架原理和工程实践。",
            },
            {
                "order": 3,
                "name": "系统设计与架构",
                "keyTopics": ["缓存", "异步任务", "RAG", "数据库设计"],
                "strategy": "结合项目里的真实场景问设计权衡。",
            },
        ]
        return InterviewPlanBO(
            stages=stages,
            estimatedDuration="25-35分钟",
            focusAreas=align.focusAreas,
            questionPriorities=[topic for stage in stages for topic in stage["keyTopics"]],
        )

    def _reflect(self, question: str, answer: str) -> ReflectionResultBO:
        if len(answer.strip()) < 20:
            return ReflectionResultBO(score=4, decision=InterviewDecision.PROBE, feedback="回答偏短，需要补充细节。")
        if "不知道" in answer or "不太清楚" in answer:
            return ReflectionResultBO(score=3, decision=InterviewDecision.NEXT, feedback="基础点存在缺口，建议后续补问更具体场景。")
        if len(answer) > 180:
            return ReflectionResultBO(score=8, decision=InterviewDecision.PROBE, feedback="回答较完整，可以继续深挖原理和权衡。")
        return ReflectionResultBO(score=7, decision=InterviewDecision.NEXT, feedback="回答基本完整，可以切到下一题。")

    def _next_question(self, context: InterviewSessionContext, *, is_probe: bool) -> str:
        stage = context.interview_plan.stages[min(context.current_stage_index, len(context.interview_plan.stages) - 1)]
        topic = stage.keyTopics[min(context.current_question_index, max(len(stage.keyTopics) - 1, 0))]
        if is_probe:
            return f"你刚才提到了 {topic}，请结合真实项目展开说说：为什么这么设计，踩过什么坑，怎么权衡？"
        return f"围绕“{topic}”这个主题，请结合你的真实项目经历详细说明你的设计思路、实现方式和最终效果。"

    def _stage_name(self, context: InterviewSessionContext) -> str:
        return context.interview_plan.stages[min(context.current_stage_index, len(context.interview_plan.stages) - 1)].name

    def _session_bo(self, context: InterviewSessionContext) -> InterviewSessionBO:
        stages = context.interview_plan.stages
        return InterviewSessionBO(
            sessionId=context.session_id,
            resumeId=context.resume_id,
            userId=context.user_id,
            jobDescription=context.job_description,
            jdAlignmentResult=context.jd_alignment_result,
            interviewPlan=context.interview_plan,
            currentStageIndex=context.current_stage_index,
            currentStageName=self._stage_name(context),
            currentQuestionIndex=context.current_question_index,
            currentQuestion=context.current_question,
            totalPlannedQuestions=sum(max(len(stage.keyTopics), 1) for stage in stages),
            stageInfos=[
                InterviewSessionStageInfoBO(
                    stageIndex=index,
                    stageName=stage.name,
                    plannedQuestionCount=max(len(stage.keyTopics), 1),
                    finished=index in context.finished_stages,
                )
                for index, stage in enumerate(stages)
            ],
        )

    def _progress_bo(
        self, context: InterviewSessionContext, reflection: ReflectionResultBO | None
    ) -> InterviewProgressBO:
        stages = context.interview_plan.stages
        stage = stages[min(context.current_stage_index, len(stages) - 1)]
        return InterviewProgressBO(
            sessionId=context.session_id,
            currentQuestionIndex=context.current_question_index,
            currentStageIndex=context.current_stage_index,
            currentStageName=stage.name,
            currentQuestion=context.current_question,
            lastUserAnswer=context.last_user_answer or None,
            lastReflection=reflection,
            currentDecision=context.current_decision,
            progress=InterviewProgressInfoBO(
                completedQuestions=len(context.qa_history),
                totalQuestions=sum(max(len(item.keyTopics), 1) for item in stages),
                currentStageCompleted=sum(1 for item in context.qa_history if item.stage_index == context.current_stage_index),
                currentStageTotal=max(len(stage.keyTopics), 1),
                completedStages=len(context.finished_stages),
                totalStages=len(stages),
            ),
        )

    def _complete_bo(self, context: InterviewSessionContext) -> InterviewCompleteBO:
        qa = [
            InterviewCompleteQARecordBO(
                stageIndex=item.stage_index,
                stageName=item.stage_name,
                question=item.question,
                answer=item.answer,
                score=item.score,
                decision=item.decision,
                feedback=item.feedback,
                isProbe=item.is_probe,
            )
            for item in context.qa_history
        ]
        grouped: dict[int, list[QARecord]] = {}
        for item in context.qa_history:
            grouped.setdefault(item.stage_index, []).append(item)
        stage_results = [
            InterviewStageResultBO(
                stageIndex=index,
                stageName=context.interview_plan.stages[index].name,
                stageScore=round(sum(i.score for i in rows) / max(len(rows), 1), 2),
                questionCount=len(rows),
                probeCount=sum(1 for i in rows if i.is_probe),
                stageFeedback="；".join(i.feedback for i in rows[-2:]),
            )
            for index, rows in grouped.items()
        ]
        total_score = int(round(sum(item.score for item in context.qa_history) / max(len(context.qa_history), 1) * 10))
        return InterviewCompleteBO(
            sessionId=context.session_id,
            finished=True,
            totalScore=total_score,
            finalFeedback="整体表现较稳，建议继续围绕项目深度、架构权衡和性能优化做强化准备。",
            qaHistory=qa,
            stageResults=stage_results,
            statistics=InterviewStatisticsBO(
                totalQuestions=len(context.qa_history),
                totalProbes=sum(1 for item in context.qa_history if item.is_probe),
                correctAnswers=sum(1 for item in context.qa_history if item.score >= 6),
                wrongAnswers=sum(1 for item in context.qa_history if item.score < 6),
                weakAreas=[item.stage_name for item in context.qa_history if item.score < 6][:3],
                strongAreas=[item.stage_name for item in context.qa_history if item.score >= 8][:3],
                durationMinutes=int((time.time() - context.start_time) / 60),
            ),
        )
