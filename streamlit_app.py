"""
AI Technical Interview Simulator — Streamlit Frontend
Run with:  streamlit run streamlit_app.py
"""

import streamlit as st
import requests
import time

# ── Config ───────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000/api"

st.set_page_config(
    page_title="AI Interview Simulator",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .hero h1 {
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }
    .hero p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0;
    }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
    }
    .metric-card h2 {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        color: #4a00e0;
    }
    .metric-card p {
        font-size: 0.95rem;
        color: #555;
        margin: 0.3rem 0 0 0;
    }

    /* Score badge */
    .score-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 24px;
        font-weight: 700;
        font-size: 1.1rem;
        color: white;
    }
    .score-excellent { background: linear-gradient(135deg, #11998e, #38ef7d); }
    .score-good      { background: linear-gradient(135deg, #36d1dc, #5b86e5); }
    .score-average   { background: linear-gradient(135deg, #f7971e, #ffd200); color: #333; }
    .score-needs     { background: linear-gradient(135deg, #e53935, #e35d5b); }

    /* Question card */
    .question-card {
        background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
        border-radius: 14px;
        padding: 1.8rem;
        margin: 1rem 0;
        font-size: 1.05rem;
        line-height: 1.6;
        color: #1a1a2e;
    }
    .question-card .q-label {
        font-weight: 700;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.7;
        margin-bottom: 0.5rem;
    }

    /* Feedback section */
    .feedback-section {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        margin: 0.7rem 0;
    }
    .feedback-section h4 {
        margin: 0 0 0.4rem 0;
        color: #4a00e0;
    }

    /* Session history card */
    .session-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
        transition: box-shadow 0.2s ease;
    }
    .session-card:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    }

    /* Hide default streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── State init ───────────────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "page": "home",
        "session_id": None,
        "current_question": None,
        "last_evaluation": None,
        "questions_answered": 0,
        "session_data": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── API helpers ──────────────────────────────────────────────────────────────

def api_post(path: str, json_data: dict | None = None):
    try:
        r = requests.post(f"{API_BASE}{path}", json=json_data, timeout=120)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the API server. Make sure FastAPI is running on http://localhost:8000")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.text}")
        return None

def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to the API server. Make sure FastAPI is running on http://localhost:8000")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.text}")
        return None


# ── Score badge helper ──────────────────────────────────────────────────────

def score_badge(score: float) -> str:
    if score >= 8.5:
        cls = "score-excellent"
    elif score >= 6.5:
        cls = "score-good"
    elif score >= 4.5:
        cls = "score-average"
    else:
        cls = "score-needs"
    return f'<span class="score-badge {cls}">{score}/10</span>'


# ═══════════════════════════════════════════════════════════════════════════
#  HOME PAGE
# ═══════════════════════════════════════════════════════════════════════════

def page_home():
    st.markdown("""
    <div class="hero">
        <h1>🎯 AI Interview Simulator</h1>
        <p>Practice technical interviews with AI-powered question generation, evaluation & feedback</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])

    # ── Start new interview ─────────────────────────────────────────────
    with col1:
        st.markdown("### 🚀 Start New Interview")

        topic = st.selectbox(
            "Topic",
            ["Python", "JavaScript", "Data Structures & Algorithms", "System Design",
             "SQL & Databases", "Machine Learning", "React", "Node.js",
             "DevOps & CI/CD", "Operating Systems", "Networking", "Java", "C++"],
            index=0,
        )

        difficulty = st.select_slider(
            "Difficulty",
            options=["Easy", "Medium", "Hard"],
            value="Medium",
        )

        num_questions = st.slider("Number of Questions", 1, 15, 5)

        if st.button("▶️  Begin Interview", type="primary", use_container_width=True):
            with st.spinner("Creating session..."):
                data = api_post("/sessions", {
                    "topic": topic,
                    "difficulty": difficulty,
                    "num_questions": num_questions,
                })
            if data:
                st.session_state.session_id = data["session_id"]
                st.session_state.session_data = data
                st.session_state.current_question = None
                st.session_state.last_evaluation = None
                st.session_state.questions_answered = 0
                st.session_state.page = "interview"
                st.rerun()

    # ── Past sessions ───────────────────────────────────────────────────
    with col2:
        st.markdown("### 📋 Past Sessions")
        sessions = api_get("/sessions")
        if sessions:
            if not sessions:
                st.info("No past sessions yet. Start your first interview!")
            for s in sessions[:10]:
                status_icon = "✅" if s["status"] == "completed" else "🔄"
                score_text = ""
                if s.get("summary"):
                    score_text = f" — **{s['summary']['overall_score']}/10** ({s['summary']['grade']})"

                with st.container():
                    st.markdown(f"""
                    <div class="session-card">
                        <strong>{status_icon} {s['topic']}</strong> · {s['difficulty']}{score_text}<br/>
                        <small style="color:#888">{s['num_questions']} questions · {s['created_at'][:10]}</small>
                    </div>
                    """, unsafe_allow_html=True)

                    if s["status"] == "completed":
                        if st.button("View Results", key=f"view_{s['session_id']}"):
                            st.session_state.session_id = s["session_id"]
                            st.session_state.session_data = s
                            st.session_state.page = "results"
                            st.rerun()
                    elif s["status"] == "in_progress":
                        if st.button("Resume", key=f"resume_{s['session_id']}"):
                            st.session_state.session_id = s["session_id"]
                            st.session_state.session_data = s
                            st.session_state.questions_answered = s["current_question_index"]
                            st.session_state.current_question = None
                            st.session_state.last_evaluation = None
                            st.session_state.page = "interview"
                            st.rerun()
        else:
            st.info("Start your first interview to see past sessions here!")


# ═══════════════════════════════════════════════════════════════════════════
#  INTERVIEW PAGE
# ═══════════════════════════════════════════════════════════════════════════

def page_interview():
    session = st.session_state.session_data
    if not session:
        st.session_state.page = "home"
        st.rerun()
        return

    # Header
    total_q = session["num_questions"]
    answered = st.session_state.questions_answered

    st.markdown(f"""
    <div class="hero" style="padding: 1.5rem 2rem;">
        <h1 style="font-size:1.6rem;">🎤 Interview · {session['topic']} ({session['difficulty']})</h1>
        <p>Question {min(answered + 1, total_q)} of {total_q}</p>
    </div>
    """, unsafe_allow_html=True)

    # Progress bar
    st.progress(answered / total_q if total_q else 0)

    # ── Show last evaluation if exists ──────────────────────────────────
    if st.session_state.last_evaluation:
        ev = st.session_state.last_evaluation
        st.markdown(f"""
        <div class="feedback-section">
            <h4>📝 Evaluation for Previous Question</h4>
            <p>{score_badge(ev['score'])} &nbsp; {ev['feedback']}</p>
        </div>
        """, unsafe_allow_html=True)

        if ev.get("strengths"):
            st.markdown("**✅ Strengths:** " + " · ".join(ev["strengths"]))
        if ev.get("weaknesses"):
            st.markdown("**⚠️ Weaknesses:** " + " · ".join(ev["weaknesses"]))
        if ev.get("suggestions"):
            st.markdown("**💡 Suggestions:** " + " · ".join(ev["suggestions"]))
        st.divider()

    # ── Check if interview is done ──────────────────────────────────────
    if answered >= total_q:
        st.success("🎉 All questions answered! Click below to get your results.")
        if st.button("📊  Get Session Results", type="primary", use_container_width=True):
            with st.spinner("Generating summary feedback..."):
                data = api_post(f"/sessions/{session['session_id']}/finish")
            if data:
                st.session_state.session_data = data
                st.session_state.page = "results"
                st.rerun()
        return

    # ── Generate question ───────────────────────────────────────────────
    if st.session_state.current_question is None:
        with st.spinner("🤔 Generating question..."):
            q_data = api_post(f"/sessions/{session['session_id']}/generate")
        if q_data:
            st.session_state.current_question = q_data
            st.rerun()
        return

    # ── Show current question ───────────────────────────────────────────
    q = st.session_state.current_question

    st.markdown(f"""
    <div class="question-card">
        <div class="q-label">Question {q['question_id']}</div>
        {q['question_text']}
    </div>
    """, unsafe_allow_html=True)

    answer = st.text_area(
        "Your Answer",
        height=200,
        placeholder="Type your answer here... Be as detailed as possible.",
        key=f"answer_{q['question_id']}",
    )

    col_submit, col_skip, col_quit = st.columns([2, 1, 1])

    with col_submit:
        if st.button("✅  Submit Answer", type="primary", use_container_width=True, disabled=not answer.strip()):
            with st.spinner("🔍 Evaluating your answer..."):
                ev_data = api_post(
                    f"/sessions/{session['session_id']}/answer",
                    {"answer_text": answer},
                )
            if ev_data:
                st.session_state.last_evaluation = ev_data
                st.session_state.current_question = None
                st.session_state.questions_answered += 1
                # Refresh session data
                updated = api_get(f"/sessions/{session['session_id']}")
                if updated:
                    st.session_state.session_data = updated
                st.rerun()

    with col_skip:
        if st.button("⏭️ Skip", use_container_width=True):
            # Submit empty answer
            with st.spinner("Skipping..."):
                ev_data = api_post(
                    f"/sessions/{session['session_id']}/answer",
                    {"answer_text": "(skipped)"},
                )
            if ev_data:
                st.session_state.last_evaluation = None
                st.session_state.current_question = None
                st.session_state.questions_answered += 1
                updated = api_get(f"/sessions/{session['session_id']}")
                if updated:
                    st.session_state.session_data = updated
                st.rerun()

    with col_quit:
        if st.button("🏠 Quit", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.current_question = None
            st.session_state.last_evaluation = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  RESULTS PAGE
# ═══════════════════════════════════════════════════════════════════════════

def page_results():
    session = st.session_state.session_data
    if not session:
        st.session_state.page = "home"
        st.rerun()
        return

    summary = session.get("summary")

    st.markdown(f"""
    <div class="hero">
        <h1 style="font-size:1.8rem;">📊 Interview Results</h1>
        <p>{session['topic']} · {session['difficulty']} · {session['num_questions']} Questions</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Score cards row ─────────────────────────────────────────────────
    if summary:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <h2>{summary['overall_score']}</h2>
                <p>Overall Score (out of 10)</p>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <h2>{summary['grade']}</h2>
                <p>Performance Grade</p>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            answered = sum(1 for q in session["questions"] if q.get("answer_text") and q["answer_text"] != "(skipped)")
            st.markdown(f"""
            <div class="metric-card">
                <h2>{answered}/{session['num_questions']}</h2>
                <p>Questions Answered</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Per-question breakdown ──────────────────────────────────────────
    st.markdown("### 📝 Question-by-Question Breakdown")

    for qa in session.get("questions", []):
        q = qa.get("question", {})
        ev = qa.get("evaluation")
        q_num = q.get("question_id", "?")

        with st.expander(
            f"Q{q_num}: {q.get('question_text', 'N/A')[:80]}..."
            if len(q.get("question_text", "")) > 80
            else f"Q{q_num}: {q.get('question_text', 'N/A')}",
            expanded=False,
        ):
            st.markdown(f"**Question:** {q.get('question_text', '')}")
            st.markdown(f"**Your Answer:** {qa.get('answer_text', '(no answer)')}")

            if ev:
                st.markdown(f"**Score:** {score_badge(ev['score'])}", unsafe_allow_html=True)
                st.markdown(f"**Feedback:** {ev.get('feedback', '')}")

                if ev.get("strengths"):
                    st.markdown("**✅ Strengths:**")
                    for s in ev["strengths"]:
                        st.markdown(f"- {s}")
                if ev.get("weaknesses"):
                    st.markdown("**⚠️ Weaknesses:**")
                    for w in ev["weaknesses"]:
                        st.markdown(f"- {w}")
                if ev.get("suggestions"):
                    st.markdown("**💡 Suggestions:**")
                    for s in ev["suggestions"]:
                        st.markdown(f"- {s}")

    # ── Summary feedback ────────────────────────────────────────────────
    if summary and summary.get("summary_feedback"):
        st.divider()
        st.markdown("### 🎯 AI Summary Feedback")
        st.markdown(f"""
        <div class="feedback-section" style="border-left-color: #764ba2;">
            {summary['summary_feedback']}
        </div>
        """, unsafe_allow_html=True)

    # Back button
    st.divider()
    if st.button("🏠  Back to Home", type="primary", use_container_width=True):
        st.session_state.page = "home"
        st.session_state.session_id = None
        st.session_state.session_data = None
        st.session_state.current_question = None
        st.session_state.last_evaluation = None
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
#  SIDEBAR + ROUTER
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🎯 AI Interview")
    st.divider()

    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    st.divider()
    st.markdown("""
    <div style="font-size:0.8rem; color:#888; text-align:center;">
        Built with Streamlit · FastAPI · Ollama · MongoDB
    </div>
    """, unsafe_allow_html=True)


# Route to the right page
if st.session_state.page == "interview":
    page_interview()
elif st.session_state.page == "results":
    page_results()
else:
    page_home()
