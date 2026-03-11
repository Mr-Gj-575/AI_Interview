"""Answer Evaluator — uses Ollama when available, rule-based evaluation as fallback."""

import json
import re
import httpx

from config import settings
from models import Evaluation


EVALUATION_PROMPT_TEMPLATE = """You are an expert technical interviewer evaluating a candidate's answer.

Question: {question}
Candidate's Answer: {answer}

Evaluate the answer carefully. Consider:
- Technical accuracy
- Completeness
- Clarity of explanation
- Depth of understanding

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
    "score": <number from 0 to 10>,
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "suggestions": ["suggestion 1", "suggestion 2"],
    "feedback": "A concise overall feedback paragraph"
}}"""


async def _try_ollama(question_text: str, answer_text: str) -> dict | None:
    """Try to evaluate via Ollama. Returns parsed dict or None."""
    prompt = EVALUATION_PROMPT_TEMPLATE.format(
        question=question_text,
        answer=answer_text,
    )
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3},
                },
            )
            response.raise_for_status()
            data = response.json()
            raw_text = data.get("response", "")
            return json.loads(raw_text)
    except Exception:
        return None


def _rule_based_evaluation(question_text: str, answer_text: str) -> dict:
    """Heuristic-based evaluation when no LLM is available."""
    answer = answer_text.strip()
    word_count = len(answer.split())
    sentence_count = len(re.split(r'[.!?]+', answer))

    # Score based on length and structure
    strengths = []
    weaknesses = []
    suggestions = []

    # Length scoring (0-3 points)
    if word_count >= 100:
        length_score = 3.0
        strengths.append("Detailed and comprehensive answer")
    elif word_count >= 50:
        length_score = 2.0
        strengths.append("Good amount of detail provided")
    elif word_count >= 20:
        length_score = 1.0
        weaknesses.append("Answer could be more detailed")
        suggestions.append("Provide more in-depth explanation with examples")
    else:
        length_score = 0.5
        weaknesses.append("Answer is too brief")
        suggestions.append("Expand your answer with detailed explanations and examples")

    # Structure scoring (0-2 points)
    has_examples = bool(re.search(r'(for example|e\.g\.|such as|like |instance)', answer, re.I))
    has_technical_terms = bool(re.search(r'(function|class|method|algorithm|complexity|data|memory|thread|process|object|interface|pattern|module|API|O\()', answer, re.I))
    has_comparison = bool(re.search(r'(however|whereas|unlike|differ|compared|while|but|on the other hand)', answer, re.I))

    structure_score = 0.0
    if has_examples:
        structure_score += 0.7
        strengths.append("Includes practical examples")
    else:
        suggestions.append("Include concrete examples to strengthen your answer")

    if has_technical_terms:
        structure_score += 0.7
        strengths.append("Uses appropriate technical terminology")

    if has_comparison:
        structure_score += 0.6
        strengths.append("Makes good comparisons and distinctions")

    # Relevance scoring (0-3 points) — check keyword overlap with question
    question_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', question_text.lower()))
    answer_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', answer.lower()))
    # Remove common stop words
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
                  'her', 'was', 'one', 'our', 'out', 'has', 'have', 'with', 'what', 'how',
                  'why', 'when', 'where', 'who', 'which', 'this', 'that', 'from', 'they'}
    question_words -= stop_words
    answer_words -= stop_words

    if question_words:
        overlap = len(question_words & answer_words) / len(question_words)
    else:
        overlap = 0.5

    relevance_score = min(overlap * 4.0, 3.0)
    if relevance_score >= 2.0:
        strengths.append("Answer is relevant to the question")
    else:
        weaknesses.append("Answer may not fully address the question")
        suggestions.append("Make sure to directly address all aspects of the question")

    # Coherence bonus (0-2 points)
    coherence_score = min(sentence_count * 0.4, 2.0)

    total = min(length_score + structure_score + relevance_score + coherence_score, 10.0)
    total = round(total, 1)

    # Generate feedback
    if total >= 8:
        feedback = "Excellent answer! You demonstrated strong understanding of the topic with clear explanations and relevant examples."
    elif total >= 6:
        feedback = "Good answer that covers the main concepts. Adding more depth and specific examples would strengthen your response."
    elif total >= 4:
        feedback = "Your answer shows basic understanding but could benefit from more detail, examples, and technical depth."
    else:
        feedback = "Your answer needs significant improvement. Focus on understanding the core concepts and providing structured, detailed explanations."

    if not strengths:
        strengths.append("Attempted to answer the question")

    return {
        "score": total,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
        "feedback": feedback,
    }


async def evaluate_answer(
    question_text: str,
    answer_text: str,
    question_id: int = 1,
) -> Evaluation:
    """Evaluate via Ollama; fall back to rule-based evaluation if unavailable."""

    # Try Ollama
    parsed = await _try_ollama(question_text, answer_text)

    # Fallback to rule-based
    if parsed is None:
        parsed = _rule_based_evaluation(question_text, answer_text)

    try:
        return Evaluation(
            question_id=question_id,
            score=min(max(float(parsed.get("score", 0)), 0), 10),
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            suggestions=parsed.get("suggestions", []),
            feedback=parsed.get("feedback", ""),
        )
    except (KeyError, ValueError):
        return Evaluation(
            question_id=question_id,
            score=0,
            strengths=[],
            weaknesses=[],
            suggestions=[],
            feedback="Could not evaluate the answer.",
        )
