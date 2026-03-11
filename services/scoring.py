"""Scoring System — computes session-level scores and grades."""

from typing import List

from models import Evaluation, PerformanceGrade, SessionSummary


def compute_session_score(evaluations: List[Evaluation]) -> float:
    """Return the average score (0-10) across all evaluations."""
    if not evaluations:
        return 0.0
    total = sum(e.score for e in evaluations)
    return round(total / len(evaluations), 2)


def classify_performance(score: float) -> PerformanceGrade:
    """Map a 0-10 score to a human-readable grade."""
    if score >= 8.5:
        return PerformanceGrade.EXCELLENT
    elif score >= 6.5:
        return PerformanceGrade.GOOD
    elif score >= 4.5:
        return PerformanceGrade.AVERAGE
    else:
        return PerformanceGrade.NEEDS_IMPROVEMENT


def build_session_summary(
    evaluations: List[Evaluation],
    summary_feedback: str = "",
) -> SessionSummary:
    """Build a SessionSummary from a list of evaluations."""
    overall_score = compute_session_score(evaluations)
    grade = classify_performance(overall_score)
    return SessionSummary(
        overall_score=overall_score,
        grade=grade,
        summary_feedback=summary_feedback,
    )
