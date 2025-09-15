# ---------- Load .env early ----------
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ---------- Imports ----------
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.services import state, report, llm
from app.grading import pandas_eval, formula_rules
from app.questions.bank import get_question_by_id
from app.db import init_db, SessionLocal, Answer

# Optional sanity print (remove if you prefer quiet logs)
print("LLM active?", bool(os.getenv("OPENAI_API_KEY")))

# ---------- App init ----------
app = FastAPI(title="Excel Mock Interviewer Advanced PoC", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relax for PoC
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

# ---------- Models ----------
class StartRequest(BaseModel):
    candidate_email: Optional[str] = None

class AnswerRequest(BaseModel):
    interview_id: str
    question_id: str
    answer_text: Optional[str] = None
    answer_table: Optional[List[Dict[str, Any]]] = None
    want_hint: Optional[bool] = False

# ---------- Health ----------
@app.get("/health")
def health():
    return {"ok": True, "version": "0.2.0"}

# ---------- Start interview ----------
@app.post("/start")
def start(req: StartRequest):
    itv = state.create_interview(req.candidate_email)
    q = state.next_question(itv["id"])
    return {"interview_id": itv["id"], "question": q}

# ---------- Helpers ----------
def detect_kind(ans_text: Optional[str], ans_table: Optional[List[Dict[str, Any]]]) -> str:
    """
    Heuristic detector for answer type:
    - table if answer_table provided
    - formula if text starts with '='
    - value if text parses as float
    - else text
    """
    if ans_table is not None:
        return "table"
    t = (ans_text or "").strip()
    if t.startswith("="):
        return "formula"
    try:
        float(t)
        return "value"
    except Exception:
        return "text"

# ---------- Answer endpoint (with type-guard + hints) ----------
@app.post("/answer")
def answer(req: AnswerRequest):
    itv = state.get_interview(req.interview_id)
    if not itv:
        raise HTTPException(404, "Interview not found")

    q = get_question_by_id(req.question_id)
    if not q:
        raise HTTPException(404, "Question not found")

    # Hints do not advance the interview
    if req.want_hint:
        state.record_hint(req.interview_id, q["id"])
        return {"hint": q.get("hint", "Try breaking the task into smaller parts.")}

    # Type guard: if user submits the wrong type, re-ask same question without advancing
    expected = q.get("kind", "formula")
    detected = detect_kind(req.answer_text, req.answer_table)
    if detected != expected:
        return {
            "score": 0,
            "feedback": f"This question expects **{expected}**, but you entered **{detected}**. Please answer in the expected format.",
            "correct": False,
            "done": False,
            "next_question": {  # re-ask same question
                "id": q["id"],
                "prompt": q["prompt"],
                "kind": q["kind"],
                "skill": q["skill"],
                "max_score": q["max_score"],
                "hint": q.get("hint"),
            },
        }

    # Evaluate according to kind
    try:
        if expected == "formula":
            score, fb, ok = formula_rules.evaluate_formula(q, (req.answer_text or ""))
        elif expected in ("value", "table"):
            score, fb, ok = pandas_eval.evaluate(q, req.answer_text, req.answer_table)
        elif expected == "text":
            score, fb, ok = llm.evaluate_text_with_rubric(q, (req.answer_text or ""))
        else:
            score, fb, ok = 0.0, "Unknown question kind.", False
    except Exception as e:
        score, fb, ok = 0.0, f"Evaluation error: {e}", False

    # Record this answer (for report/metrics)
    state.record_answer(
        req.interview_id,
        q["id"],
        req.answer_text,
        req.answer_table,
        score,
        fb,
    )

    # Advance to next question
    nx = state.next_question(req.interview_id)
    done = nx is None
    summary = report.generate_report(itv) if done else None
    return {
        "score": score,
        "feedback": fb,
        "correct": ok,
        "done": done,
        "next_question": nx,
        "summary": summary,
    }

# ---------- Report ----------
@app.get("/report/{iid}")
def report_api(iid: str):
    itv = state.get_interview(iid)
    if not itv:
        raise HTTPException(404, "Interview not found")
    return report.generate_report(itv)

# ---------- Simple admin metrics ----------
@app.get("/admin/metrics")
def metrics():
    db: Session = SessionLocal()
    try:
        total = db.query(func.count(Answer.id)).scalar() or 0
        avg = float(db.query(func.avg(Answer.score)).scalar() or 0.0)
        from collections import defaultdict
        per = defaultdict(list)

        for a in db.query(Answer).all():
            q = get_question_by_id(a.question_id)
            if q:
                per[q.get("skill", "general")].append(a.score)

        per_avg = {k: round(sum(v) / len(v), 2) if v else 0.0 for k, v in per.items()}
        return {"total_answers": total, "avg_score": round(avg, 2), "per_skill_avg": per_avg}
    finally:
        db.close()
