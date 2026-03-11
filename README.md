# 🎯 AI Technical Interview Simulator

An AI-powered system that generates technical interview questions, evaluates answers, provides scoring, and gives actionable feedback.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.38-red)
![MongoDB](https://img.shields.io/badge/MongoDB-Optional-yellow)
![Ollama](https://img.shields.io/badge/Ollama-Optional-purple)

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Question Generator** | Generates technical questions across 6+ topics and 3 difficulty levels |
| 2 | **Answer Evaluation** | AI-powered or rule-based evaluation of candidate answers |
| 3 | **Scoring System** | 0-10 scoring with performance grades (Excellent/Good/Average/Needs Improvement) |
| 4 | **Conversation Storage** | Persistent session history with MongoDB (or in-memory fallback) |
| 5 | **Feedback Generation** | Per-question + session-level AI feedback with strengths, weaknesses, and suggestions |

## Tech Stack

- **Backend:** Python, FastAPI
- **Frontend:** Streamlit
- **LLM:** Ollama (Llama 3 / any local model) — *optional, has built-in fallback*
- **Database:** MongoDB — *optional, has in-memory fallback*

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/AI_Interview.git
cd AI_Interview

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment config
cp .env.example .env

# 4. Start the backend (Terminal 1)
uvicorn main:app --reload

# 5. Start the frontend (Terminal 2)
streamlit run streamlit_app.py
```

Open **http://localhost:8501** and start interviewing! 🚀

> **Note:** The app works fully standalone. Install Ollama + MongoDB for AI-powered evaluation and persistent storage.

## Optional: Enable AI Evaluation

```bash
# Install Ollama (https://ollama.com)
ollama pull llama3
ollama serve
```

## Optional: Enable Persistent Storage

Start MongoDB on `localhost:27017` — the app auto-detects and uses it.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sessions` | Start new interview session |
| `POST` | `/api/sessions/{id}/generate` | Generate next question |
| `POST` | `/api/sessions/{id}/answer` | Submit answer, get evaluation |
| `POST` | `/api/sessions/{id}/finish` | End session, get summary |
| `GET` | `/api/sessions/{id}` | Get session details |
| `GET` | `/api/sessions` | List all sessions |

## Project Structure

```
├── .env.example          # Environment template
├── requirements.txt      # Dependencies
├── config.py             # Settings loader
├── database.py           # MongoDB connection + fallback
├── models.py             # Pydantic models
├── main.py               # FastAPI entry point
├── routes/
│   └── interview.py      # API routes
├── services/
│   ├── question_generator.py
│   ├── answer_evaluator.py
│   ├── scoring.py
│   ├── feedback_generator.py
│   └── conversation_store.py
└── streamlit_app.py      # Streamlit UI
```

## License

MIT
