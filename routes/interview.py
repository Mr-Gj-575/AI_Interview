"""Interview API routes."""

from fastapi import APIRouter, HTTPException

from models import (
    CreateSessionRequest,
    SubmitAnswerRequest,
    SessionResponse,
    QuestionResponse,
    EvaluationResponse,
    QuestionAnswer,
    SessionStatus,
)
from services import (
    question_generator,
    answer_evaluator,
    scoring,
    feedback_generator,
    conversation_store,
)

router = APIRouter(prefix="/api")


# ── POST /api/sessions ─────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse)
async def create_session(req: CreateSessionRequest):
    """Start a new interview session."""
    session = await conversation_store.create_session(
        topic=req.topic,
        difficulty=req.difficulty,
        num_questions=req.num_questions,
    )
    return _to_session_response(session)


# ── POST /api/sessions/{id}/generate ───────────────────────────────────────

@router.post("/sessions/{session_id}/generate", response_model=QuestionResponse)
async def generate_question(session_id: str):
    """Generate the next interview question for the session."""
    session = await _get_session_or_404(session_id)

    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(400, "Session is already completed.")

    if len(session.questions) >= session.num_questions:
        raise HTTPException(400, "All questions have been generated for this session.")

    question = await question_generator.generate_question(
        topic=session.topic,
        difficulty=session.difficulty,
        question_id=len(session.questions) + 1,
    )

    qa = QuestionAnswer(question=question)
    await conversation_store.add_question_to_session(session_id, qa)

    return QuestionResponse(
        question_id=question.question_id,
        topic=question.topic,
        difficulty=question.difficulty,
        question_text=question.question_text,
    )


# ── POST /api/sessions/{id}/answer ─────────────────────────────────────────

@router.post("/sessions/{session_id}/answer", response_model=EvaluationResponse)
async def submit_answer(session_id: str, req: SubmitAnswerRequest):
    """Submit an answer for the current question and receive an evaluation."""
    session = await _get_session_or_404(session_id)

    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(400, "Session is already completed.")

    idx = session.current_question_index
    if idx >= len(session.questions):
        raise HTTPException(400, "No pending question to answer. Generate a question first.")

    current_qa = session.questions[idx]

    evaluation = await answer_evaluator.evaluate_answer(
        question_text=current_qa.question.question_text,
        answer_text=req.answer_text,
        question_id=current_qa.question.question_id,
    )

    await conversation_store.save_answer_and_evaluation(
        session_id=session_id,
        question_index=idx,
        answer_text=req.answer_text,
        evaluation=evaluation,
    )

    return EvaluationResponse(
        question_id=evaluation.question_id,
        score=evaluation.score,
        strengths=evaluation.strengths,
        weaknesses=evaluation.weaknesses,
        suggestions=evaluation.suggestions,
        feedback=evaluation.feedback,
    )


# ── POST /api/sessions/{id}/finish ─────────────────────────────────────────

@router.post("/sessions/{session_id}/finish", response_model=SessionResponse)
async def finish_session(session_id: str):
    """Finish the session and get summary feedback."""
    session = await _get_session_or_404(session_id)

    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(400, "Session is already completed.")

    # Collect evaluations
    evaluations = [
        qa.evaluation for qa in session.questions if qa.evaluation is not None
    ]

    # Generate summary feedback
    summary_text = await feedback_generator.generate_summary_feedback(session.questions)

    # Build session summary with scoring
    summary = scoring.build_session_summary(evaluations, summary_text)

    # Persist
    await conversation_store.finish_session(session_id, summary)

    # Return updated session
    updated = await _get_session_or_404(session_id)
    return _to_session_response(updated)


# ── GET /api/sessions/{id} ─────────────────────────────────────────────────

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get full details of a session."""
    session = await _get_session_or_404(session_id)
    return _to_session_response(session)


# ── GET /api/sessions ──────────────────────────────────────────────────────

@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions():
    """List all interview sessions."""
    sessions = await conversation_store.list_sessions()
    return [_to_session_response(s) for s in sessions]


# ── Helpers ─────────────────────────────────────────────────────────────────

async def _get_session_or_404(session_id: str):
    session = await conversation_store.get_session(session_id)
    if session is None:
        raise HTTPException(404, f"Session '{session_id}' not found.")
    return session


def _to_session_response(session):
    return SessionResponse(
        session_id=session.session_id,
        topic=session.topic,
        difficulty=session.difficulty,
        num_questions=session.num_questions,
        current_question_index=session.current_question_index,
        status=session.status,
        questions=session.questions,
        summary=session.summary,
        created_at=session.created_at,
    )
