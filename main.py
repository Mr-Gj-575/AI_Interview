"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.interview import router as interview_router

app = FastAPI(
    title="AI Technical Interview Simulator",
    description="An AI-powered system that asks technical interview questions, evaluates answers, and provides feedback.",
    version="1.0.0",
)

# Allow Streamlit (or any frontend) to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interview_router)


@app.get("/")
async def root():
    return {"message": "AI Technical Interview Simulator API is running."}
