"""Pydantic models for requests, responses, and database documents."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class SessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class PerformanceGrade(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    NEEDS_IMPROVEMENT = "Needs Improvement"


# ── Domain models ────────────────────────────────────────────────────────────

class Question(BaseModel):
    question_id: int = 1
    topic: str
    difficulty: Difficulty
    question_text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Evaluation(BaseModel):
    question_id: int
    score: float = Field(ge=0, le=10)
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggestions: List[str] = []
    feedback: str = ""
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuestionAnswer(BaseModel):
    """Stores a question together with its answer and evaluation."""
    question: Question
    answer_text: Optional[str] = None
    evaluation: Optional[Evaluation] = None


class SessionSummary(BaseModel):
    overall_score: float = 0.0
    grade: PerformanceGrade = PerformanceGrade.NEEDS_IMPROVEMENT
    summary_feedback: str = ""


class InterviewSession(BaseModel):
    session_id: str = ""
    topic: str
    difficulty: Difficulty
    num_questions: int = 5
    questions: List[QuestionAnswer] = []
    current_question_index: int = 0
    status: SessionStatus = SessionStatus.IN_PROGRESS
    summary: Optional[SessionSummary] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── API request / response schemas ──────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    topic: str
    difficulty: Difficulty = Difficulty.MEDIUM
    num_questions: int = Field(default=5, ge=1, le=20)


class SubmitAnswerRequest(BaseModel):
    answer_text: str


class SessionResponse(BaseModel):
    session_id: str
    topic: str
    difficulty: Difficulty
    num_questions: int
    current_question_index: int
    status: SessionStatus
    questions: List[QuestionAnswer] = []
    summary: Optional[SessionSummary] = None
    created_at: datetime


class QuestionResponse(BaseModel):
    question_id: int
    topic: str
    difficulty: Difficulty
    question_text: str


class EvaluationResponse(BaseModel):
    question_id: int
    score: float
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    feedback: str
