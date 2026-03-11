"""Conversation Store — CRUD on MongoDB with in-memory fallback."""

from __future__ import annotations

from typing import Dict, List, Optional
from uuid import uuid4
from copy import deepcopy

from database import get_database, is_memory_mode
from models import (
    InterviewSession,
    QuestionAnswer,
    Evaluation,
    SessionSummary,
    SessionStatus,
    Difficulty,
)

_COLLECTION = "sessions"

# ── In-memory store ──────────────────────────────────────────────────────────
_memory_store: Dict[str, dict] = {}


def _db():
    db = get_database()
    if db is None:
        return None
    return db[_COLLECTION]


# ── Create ───────────────────────────────────────────────────────────────────

async def create_session(
    topic: str,
    difficulty: Difficulty,
    num_questions: int,
) -> InterviewSession:
    session = InterviewSession(
        session_id=str(uuid4()),
        topic=topic,
        difficulty=difficulty,
        num_questions=num_questions,
    )
    doc = session.model_dump(mode="json")

    if is_memory_mode():
        _memory_store[session.session_id] = doc
    else:
        await _db().insert_one(doc)
    return session


# ── Read ─────────────────────────────────────────────────────────────────────

async def get_session(session_id: str) -> Optional[InterviewSession]:
    if is_memory_mode():
        doc = _memory_store.get(session_id)
        if doc is None:
            return None
        return InterviewSession(**doc)
    else:
        doc = await _db().find_one({"session_id": session_id})
        if doc is None:
            return None
        doc.pop("_id", None)
        return InterviewSession(**doc)


async def list_sessions() -> List[InterviewSession]:
    if is_memory_mode():
        sessions = [InterviewSession(**d) for d in _memory_store.values()]
        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions
    else:
        cursor = _db().find().sort("created_at", -1)
        sessions: List[InterviewSession] = []
        async for doc in cursor:
            doc.pop("_id", None)
            sessions.append(InterviewSession(**doc))
        return sessions


# ── Update ───────────────────────────────────────────────────────────────────

async def add_question_to_session(
    session_id: str,
    qa: QuestionAnswer,
) -> None:
    if is_memory_mode():
        _memory_store[session_id]["questions"].append(qa.model_dump(mode="json"))
    else:
        await _db().update_one(
            {"session_id": session_id},
            {"$push": {"questions": qa.model_dump(mode="json")}},
        )


async def save_answer_and_evaluation(
    session_id: str,
    question_index: int,
    answer_text: str,
    evaluation: Evaluation,
) -> None:
    if is_memory_mode():
        _memory_store[session_id]["questions"][question_index]["answer_text"] = answer_text
        _memory_store[session_id]["questions"][question_index]["evaluation"] = evaluation.model_dump(mode="json")
        _memory_store[session_id]["current_question_index"] = question_index + 1
    else:
        await _db().update_one(
            {"session_id": session_id},
            {
                "$set": {
                    f"questions.{question_index}.answer_text": answer_text,
                    f"questions.{question_index}.evaluation": evaluation.model_dump(mode="json"),
                    "current_question_index": question_index + 1,
                }
            },
        )


async def finish_session(
    session_id: str,
    summary: SessionSummary,
) -> None:
    if is_memory_mode():
        _memory_store[session_id]["status"] = SessionStatus.COMPLETED.value
        _memory_store[session_id]["summary"] = summary.model_dump(mode="json")
    else:
        await _db().update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": SessionStatus.COMPLETED.value,
                    "summary": summary.model_dump(mode="json"),
                }
            },
        )
