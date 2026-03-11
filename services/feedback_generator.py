"""Feedback Generator — session summary via Ollama or rule-based fallback."""

import httpx

from typing import List

from config import settings
from models import QuestionAnswer


SUMMARY_PROMPT_TEMPLATE = """You are an expert technical interviewer providing a final session summary.

The candidate has answered the following questions during their interview:

{qa_block}

Provide a comprehensive summary feedback covering:
1. Overall performance assessment
2. Key strengths demonstrated
3. Areas that need improvement
4. Specific recommendations for further study

Write 3-5 paragraphs of constructive, encouraging, and actionable feedback.
Respond with plain text only (no JSON, no markdown formatting)."""


def _format_qa_block(qa_pairs: List[QuestionAnswer]) -> str:
    parts: list[str] = []
    for i, qa in enumerate(qa_pairs, 1):
        answer = qa.answer_text or "(no answer provided)"
        score = qa.evaluation.score if qa.evaluation else "N/A"
        parts.append(
            f"Q{i}: {qa.question.question_text}\n"
            f"Answer: {answer}\n"
            f"Score: {score}/10"
        )
    return "\n\n".join(parts)


def _rule_based_summary(qa_pairs: List[QuestionAnswer]) -> str:
    """Generate a rule-based summary when Ollama is not available."""
    if not qa_pairs:
        return "No questions were answered in this session."

    scores = [qa.evaluation.score for qa in qa_pairs if qa.evaluation]
    avg = sum(scores) / len(scores) if scores else 0
    answered = sum(1 for qa in qa_pairs if qa.answer_text and qa.answer_text != "(skipped)")
    skipped = len(qa_pairs) - answered

    all_strengths = []
    all_weaknesses = []
    all_suggestions = []
    for qa in qa_pairs:
        if qa.evaluation:
            all_strengths.extend(qa.evaluation.strengths)
            all_weaknesses.extend(qa.evaluation.weaknesses)
            all_suggestions.extend(qa.evaluation.suggestions)

    # Remove duplicates while preserving order
    strengths = list(dict.fromkeys(all_strengths))[:5]
    weaknesses = list(dict.fromkeys(all_weaknesses))[:5]
    suggestions = list(dict.fromkeys(all_suggestions))[:5]

    # Build summary paragraphs
    paragraphs = []

    # Performance assessment
    if avg >= 8.5:
        paragraphs.append(f"Outstanding performance! You scored an average of {avg:.1f}/10 across {len(scores)} questions, demonstrating excellent technical knowledge and communication skills. You clearly have a strong foundation in the subject matter.")
    elif avg >= 6.5:
        paragraphs.append(f"Good performance overall. You scored an average of {avg:.1f}/10 across {len(scores)} questions. You showed solid understanding of the core concepts, with some areas where deeper knowledge would strengthen your responses.")
    elif avg >= 4.5:
        paragraphs.append(f"You scored an average of {avg:.1f}/10 across {len(scores)} questions. While you demonstrated basic understanding of the topics, there are several areas that would benefit from further study and practice.")
    else:
        paragraphs.append(f"You scored an average of {avg:.1f}/10 across {len(scores)} questions. The results suggest that more preparation would be beneficial. Don't be discouraged — with focused study and practice, you can significantly improve your performance.")

    # Strengths
    if strengths:
        s_list = ", ".join(strengths[:3])
        paragraphs.append(f"Key strengths observed in your answers include: {s_list}. Continue building on these areas as they form a solid foundation for technical interviews.")

    # Weaknesses and suggestions
    if weaknesses:
        w_list = ", ".join(weaknesses[:3])
        paragraphs.append(f"Areas for improvement include: {w_list}. Focusing on these aspects will help round out your skill set and improve your interview performance.")

    if suggestions:
        s_list = "; ".join(suggestions[:3])
        paragraphs.append(f"Recommendations for further development: {s_list}.")

    if skipped > 0:
        paragraphs.append(f"Note: You skipped {skipped} question(s). In a real interview, try to attempt every question — even a partial answer shows your thought process and can earn partial credit.")

    return "\n\n".join(paragraphs)


async def generate_summary_feedback(qa_pairs: List[QuestionAnswer]) -> str:
    """Generate summary via Ollama; fall back to rule-based summary."""

    # Try Ollama
    qa_block = _format_qa_block(qa_pairs)
    prompt = SUMMARY_PROMPT_TEMPLATE.format(qa_block=qa_block)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5},
                },
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "").strip()
            if result:
                return result
    except Exception:
        pass

    # Fallback
    return _rule_based_summary(qa_pairs)
