"""
Semiconductor Training System - FastAPI Backend
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os

from .database import init_db, create_user, verify_user, get_user, seed_default_users
from .knowledge import get_module_index, get_modules_for_role, scan_library
from .quiz import (
    seed_questions_to_db, generate_quiz, submit_answer,
    get_user_stats, log_reading,
    generate_mistake_quiz, generate_daily_recommendation, get_progress_summary
)

app = FastAPI(title="半导体培训系统", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────── Models ──────
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "newbie"
    display_name: Optional[str] = None

class QuizRequest(BaseModel):
    user_id: int
    module_code: str = ""
    role: str = ""
    count: int = 10
    difficulty: Optional[str] = None

class RetryMistakesRequest(BaseModel):
    user_id: int
    module_code: str = ""
    count: int = 10
    difficulty: Optional[str] = None

class AnswerRequest(BaseModel):
    user_id: int
    question_id: str
    user_answer: str
    spent_seconds: float = 0

class ReadingRequest(BaseModel):
    user_id: int
    module_code: str
    entry_title: str = ""

# ────── Startup ──────
@app.on_event("startup")
async def startup():
    init_db()
    seed_default_users()
    result = seed_questions_to_db()
    # Generate index if not exists
    get_module_index()
    try:
        print(f"✅ Training system ready. {result.get('total', 0)} questions loaded (+{result.get('inserted', 0)}).")
    except:
        print("✅ Training system ready.")

# ────── Auth ──────
@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = verify_user(req.username, req.password)
    if not user:
        raise HTTPException(401, "用户名或密码错误")
    return {"user_id": user["id"], "username": user["username"],
            "role": user["role"], "display_name": user["display_name"]}

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    user = create_user(req.username, req.password, req.role, req.display_name)
    if not user:
        raise HTTPException(400, "用户名已存在")
    return {"user_id": user["id"], "username": user["username"], "role": user["role"]}

@app.get("/api/auth/user/{user_id}")
def user_info(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    return {"user_id": user["id"], "username": user["username"],
            "role": user["role"], "display_name": user["display_name"]}

# ────── Knowledge ──────
@app.get("/api/knowledge/index")
def knowledge_index():
    return get_module_index()

@app.get("/api/knowledge/refresh")
def knowledge_refresh():
    return scan_library()

@app.get("/api/knowledge/role/{role}")
def role_modules(role: str):
    return get_modules_for_role(role)

# ────── Quiz ──────
@app.post("/api/quiz/generate")
def quiz_generate(req: QuizRequest):
    module_code = req.module_code
    if not module_code and req.role:
        # Resolve role → pick first available module that has questions
        from .knowledge import get_modules_for_role
        from .database import get_db
        conn = get_db()
        role_data = get_modules_for_role(req.role)
        all_mods = role_data.get("required", []) + role_data.get("elective", [])
        for mod in all_mods:
            code = mod.get("code", "")
            # Check if there are questions for this module
            cnt = conn.execute(
                "SELECT COUNT(*) as c FROM questions WHERE module_code=?", (code,)
            ).fetchone()["c"]
            if cnt > 0:
                module_code = code
                break
        conn.close()
        if not module_code and all_mods:
            module_code = all_mods[0].get("code", "")  # fallback
    if not module_code:
        return {"questions": [], "count": 0, "error": "请提供 module_code 或 role"}
    questions = generate_quiz(req.user_id, module_code, req.count, req.difficulty)
    return {"questions": questions, "count": len(questions)}

@app.post("/api/quiz/submit")
def quiz_submit(req: AnswerRequest):
    result = submit_answer(req.user_id, req.question_id, req.user_answer, req.spent_seconds)
    if result is None:
        raise HTTPException(404, "题目不存在")
    return result

@app.get("/api/quiz/stats/{user_id}")
def quiz_stats(user_id: int):
    return get_user_stats(user_id)

@app.post("/api/quiz/retry-mistakes")
def quiz_retry_mistakes(req: RetryMistakesRequest):
    questions = generate_mistake_quiz(req.user_id, req.module_code, req.count, req.difficulty)
    return {"questions": questions, "count": len(questions)}

@app.get("/api/quiz/daily-recommendation/{user_id}")
def quiz_daily_recommendation(user_id: int, count: int = 10):
    questions = generate_daily_recommendation(user_id, count=count)
    return {"questions": questions, "count": len(questions)}

# ────── Progress ──────
@app.get("/api/progress/summary/{user_id}")
def progress_summary(user_id: int):
    return get_progress_summary(user_id)

# ────── Reading ──────
@app.post("/api/reading/log")
def reading_log(req: ReadingRequest):
    log_reading(req.user_id, req.module_code, req.entry_title)
    return {"status": "ok"}

# ────── Health ──────
@app.get("/api/health")
def health():
    return {"status": "ok", "service": "training-system"}

# ────── Intro Page ──────
@app.get("/intro", response_class=HTMLResponse)
def intro_page():
    intro_path = os.path.expanduser("~/.hermes/scripts/training-intro.html")
    if os.path.exists(intro_path):
        with open(intro_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Intro page not found</h1>"
