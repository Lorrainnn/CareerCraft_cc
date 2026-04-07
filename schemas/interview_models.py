from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InterviewDecision(str, Enum):
    PROBE = "PROBE"
    NEXT = "NEXT"
    STAGE_FINISH = "STAGE_FINISH"
    FINISH = "FINISH"


class JDAlignmentResultBO(BaseModel):
    matchScore: int = 0
    matchedSkills: list[str] = Field(default_factory=list)
    missingSkills: list[str] = Field(default_factory=list)
    relatedProjects: list[str] = Field(default_factory=list)
    focusAreas: list[str] = Field(default_factory=list)
    suggestion: str | None = None


class InterviewPlanStageBO(BaseModel):
    order: int
    name: str
    keyTopics: list[str] = Field(default_factory=list)
    strategy: str | None = None


class InterviewPlanBO(BaseModel):
    stages: list[InterviewPlanStageBO] = Field(default_factory=list)
    estimatedDuration: str | None = None
    focusAreas: list[str] = Field(default_factory=list)
    questionPriorities: list[str] = Field(default_factory=list)


class ReflectionResultBO(BaseModel):
    score: int = 0
    decision: InterviewDecision = InterviewDecision.NEXT
    feedback: str = ""
    probeSuggestions: list[str] = Field(default_factory=list)


class InterviewSessionStageInfoBO(BaseModel):
    stageIndex: int
    stageName: str
    plannedQuestionCount: int
    finished: bool = False


class InterviewSessionBO(BaseModel):
    sessionId: int
    resumeId: int
    userId: int
    jobDescription: str
    jdAlignmentResult: JDAlignmentResultBO
    interviewPlan: InterviewPlanBO
    currentStageIndex: int
    currentStageName: str
    currentQuestionIndex: int
    currentQuestion: str
    totalPlannedQuestions: int
    stageInfos: list[InterviewSessionStageInfoBO] = Field(default_factory=list)


class InterviewProgressInfoBO(BaseModel):
    completedQuestions: int
    totalQuestions: int
    currentStageCompleted: int
    currentStageTotal: int
    completedStages: int
    totalStages: int


class InterviewProgressBO(BaseModel):
    sessionId: int
    currentQuestionIndex: int
    currentStageIndex: int
    currentStageName: str
    currentQuestion: str
    lastUserAnswer: str | None = None
    lastReflection: ReflectionResultBO | None = None
    currentDecision: InterviewDecision
    progress: InterviewProgressInfoBO


class InterviewCompleteQARecordBO(BaseModel):
    stageIndex: int
    stageName: str
    question: str
    answer: str
    score: int
    decision: InterviewDecision
    feedback: str
    isProbe: bool = False


class InterviewStageResultBO(BaseModel):
    stageIndex: int
    stageName: str
    stageScore: float = 0
    questionCount: int = 0
    probeCount: int = 0
    stageFeedback: str = ""


class InterviewStatisticsBO(BaseModel):
    totalQuestions: int = 0
    totalProbes: int = 0
    correctAnswers: int = 0
    wrongAnswers: int = 0
    weakAreas: list[str] = Field(default_factory=list)
    strongAreas: list[str] = Field(default_factory=list)
    durationMinutes: int = 0


class InterviewCompleteBO(BaseModel):
    sessionId: int
    finished: bool = True
    totalScore: int = 0
    finalFeedback: str = ""
    qaHistory: list[InterviewCompleteQARecordBO] = Field(default_factory=list)
    stageResults: list[InterviewStageResultBO] = Field(default_factory=list)
    statistics: InterviewStatisticsBO = Field(default_factory=InterviewStatisticsBO)


class InterviewResponseType(str, Enum):
    SESSION = "SESSION"
    PROGRESS = "PROGRESS"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class InterviewState(str, Enum):
    INITIALIZING = "INITIALIZING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    ERROR = "ERROR"


class InterviewResponseBO(BaseModel):
    responseType: InterviewResponseType
    sessionId: int
    interviewState: InterviewState
    session: Optional[InterviewSessionBO] = None
    progress: Optional[InterviewProgressBO] = None
    complete: Optional[InterviewCompleteBO] = None


class InterviewStartRequest(BaseModel):
    resumeId: int
    jobDescription: str


class InterviewContinueRequest(BaseModel):
    userAnswer: str
