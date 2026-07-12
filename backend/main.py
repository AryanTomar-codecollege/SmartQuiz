from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import secrets
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import delete, desc, func, select

from backend.db import AttemptAnswer, Question, QuizAttempt, SessionLocal, User, init_db
from backend.schemas import (
    AuthResponse,
    DashboardResponse,
    LoginRequest,
    MissedAttempt,
    QuestionOut,
    QuizAnswerRequest,
    QuizResultResponse,
    QuizStartResponse,
    ReviewItem,
    SignupRequest,
    UserOut,
)
from backend.seed_data import QUESTION_SEED
from config import Config
from utils.adaptive import get_next_difficulty

PASSWORD_ITERATIONS = 120000
MISSED_QUIZ_EXPIRY_HOURS = 24


# ---------------------------------------------------------------------------
# Application lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _seed_questions()
    _cleanup_expired_missed()
    yield


app = FastAPI(title="Smart Quiz API", lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=Config.SECRET_KEY,
    session_cookie="smartquiz_session",
    same_site="none",
    https_only=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in Config.FRONTEND_ORIGINS.split(",")
        if origin.strip()
    ]
    if getattr(Config, "FRONTEND_ORIGINS", None)
    else ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_questions() -> None:
    with SessionLocal() as db:
        count = db.scalar(select(func.count()).select_from(Question)) or 0
        if count:
            return
        db.add_all(list(Question(**item) for item in QUESTION_SEED))
        db.commit()


def _cleanup_expired_missed() -> None:
    """Remove timed-out quiz attempts whose expiry window has passed."""
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        expired_ids = db.scalars(
            select(QuizAttempt.id).where(
                QuizAttempt.status == "timed_out",
                QuizAttempt.expires_at != None,  # noqa: E711
                QuizAttempt.expires_at < now,
            )
        ).all()
        if expired_ids:
            db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id.in_(expired_ids)))
            db.execute(delete(QuizAttempt).where(QuizAttempt.id.in_(expired_ids)))
            db.commit()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(candidate, expected)
    except Exception:
        return False


def _user_to_dict(user: User | None) -> dict[str, Any] | None:
    if not user:
        return None
    return {"id": user.id, "username": user.username, "email": user.email}


def _normalize_username(value: str) -> str:
    return value.strip()


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _get_current_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with SessionLocal() as db:
        return db.get(User, user_id)


def _require_user(request: Request) -> User:
    user = _get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please log in first.")
    return user


def _get_quiz_deadline(request: Request) -> datetime | None:
    quiz_deadline = request.session.get("quiz_deadline")
    if not quiz_deadline:
        return None
    try:
        return datetime.fromisoformat(quiz_deadline)
    except ValueError:
        return None


def _get_remaining_quiz_time(request: Request) -> int:
    deadline = _get_quiz_deadline(request)
    if deadline is None:
        return Config.QUIZ_TIME_SECONDS
    remaining_seconds = int((deadline - datetime.now(timezone.utc)).total_seconds())
    return max(0, remaining_seconds)


def _question_dict(question: Question) -> dict[str, Any]:
    return {
        "id": question.id,
        "question": question.question,
        "option_a": question.option_a,
        "option_b": question.option_b,
        "option_c": question.option_c,
        "option_d": question.option_d,
        "difficulty": question.difficulty,
        "category": question.category,
    }


def _get_next_question(request: Request) -> Question | None:
    difficulty = request.session.get("current_difficulty", "easy")
    asked_ids = request.session.get("asked_ids", [])

    with SessionLocal() as db:
        stmt = select(Question).where(Question.difficulty == difficulty)
        if asked_ids:
            stmt = stmt.where(Question.id.notin_(asked_ids))
        stmt = stmt.order_by(func.random()).limit(1)
        question = db.scalar(stmt)

        if question:
            return question

        stmt = select(Question)
        if asked_ids:
            stmt = stmt.where(Question.id.notin_(asked_ids))
        stmt = stmt.order_by(func.random()).limit(1)
        return db.scalar(stmt)


def _quiz_payload(request: Request, question: Question | None) -> dict[str, Any]:
    answers = request.session.get("quiz_answers", [])
    quiz_deadline = request.session.get("quiz_deadline")
    return {
        "question": _question_dict(question) if question else None,
        "question_number": len(answers) + (1 if question else 0),
        "total_questions": Config.QUESTIONS_PER_QUIZ,
        "quiz_time": _get_remaining_quiz_time(request),
        "quiz_deadline": quiz_deadline or "",
        "active": bool(request.session.get("quiz_active")),
    }


# ---------------------------------------------------------------------------
# Routes — General
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "Smart Quiz is running."}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me", response_model=UserOut | None)
def me(request: Request):
    return _user_to_dict(_get_current_user(request))


# ---------------------------------------------------------------------------
# Routes — Auth
# ---------------------------------------------------------------------------

@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(request: Request, payload: SignupRequest):
    username = _normalize_username(payload.username)
    email = _normalize_email(payload.email)

    if not username or not email:
        raise HTTPException(status_code=400, detail="Username and email are required.")

    with SessionLocal() as db:
        username_taken = db.scalar(select(User.id).where(User.username == username)) is not None
        email_taken = db.scalar(select(User.id).where(User.email == email)) is not None

        if username_taken and email_taken:
            raise HTTPException(status_code=400, detail="Username and email already exist.")
        if username_taken:
            raise HTTPException(status_code=400, detail="Username already exists.")
        if email_taken:
            raise HTTPException(status_code=400, detail="Email already exists.")

        user = User(
            username=username,
            email=email,
            password=_hash_password(payload.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return {"message": "Account created!", "user": _user_to_dict(user)}


@app.post("/api/auth/login", response_model=AuthResponse)
def login(request: Request, payload: LoginRequest):
    username = _normalize_username(payload.username)

    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))

    if not user or not _verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return {"message": f"Welcome back, {user.username}!", "user": _user_to_dict(user)}


@app.post("/api/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "You have been logged out."}


# ---------------------------------------------------------------------------
# Routes — Quiz
# ---------------------------------------------------------------------------

@app.post("/api/quiz/start", response_model=QuizStartResponse)
def start_quiz(request: Request):
    _require_user(request)
    request.session["quiz_answers"] = []
    request.session["current_difficulty"] = "easy"
    request.session["asked_ids"] = []
    request.session["quiz_active"] = True
    request.session["quiz_saved"] = False
    request.session["quiz_deadline"] = (
        datetime.now(timezone.utc) + timedelta(seconds=Config.QUIZ_TIME_SECONDS)
    ).isoformat()
    question = _get_next_question(request)
    return _quiz_payload(request, question)


@app.get("/api/quiz/current", response_model=QuizStartResponse)
def current_question(request: Request):
    if not request.session.get("quiz_active"):
        raise HTTPException(status_code=400, detail="Quiz is not active.")
    if _get_remaining_quiz_time(request) <= 0:
        raise HTTPException(status_code=400, detail="Time is up.")
    if len(request.session.get("quiz_answers", [])) >= Config.QUESTIONS_PER_QUIZ:
        raise HTTPException(status_code=400, detail="Quiz already completed.")
    question = _get_next_question(request)
    if not question:
        raise HTTPException(status_code=404, detail="No more questions available.")
    return _quiz_payload(request, question)


@app.post("/api/quiz/answer", response_model=QuizStartResponse | QuizResultResponse)
def submit_answer(request: Request, payload: QuizAnswerRequest):
    if not request.session.get("quiz_active"):
        raise HTTPException(status_code=400, detail="Quiz is not active.")
    if _get_remaining_quiz_time(request) <= 0:
        raise HTTPException(status_code=400, detail="Time is up.")

    with SessionLocal() as db:
        question = db.get(Question, payload.question_id)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    is_correct = payload.selected_ans == question.correct_ans
    answers = request.session.get("quiz_answers", [])
    answers.append(
        {
            "question_id": question.id,
            "selected": payload.selected_ans,
            "is_correct": is_correct,
            "difficulty": question.difficulty,
        }
    )
    request.session["quiz_answers"] = answers

    asked_ids = request.session.get("asked_ids", [])
    asked_ids.append(question.id)
    request.session["asked_ids"] = asked_ids
    request.session["current_difficulty"] = get_next_difficulty(question.difficulty, is_correct)

    if len(answers) >= Config.QUESTIONS_PER_QUIZ or _get_remaining_quiz_time(request) <= 0:
        return _finalize_quiz(request)

    next_question = _get_next_question(request)
    if not next_question:
        return _finalize_quiz(request)
    return _quiz_payload(request, next_question)


def _finalize_quiz(request: Request, status: str = "completed") -> QuizResultResponse:
    request.session["quiz_active"] = False
    answers = request.session.get("quiz_answers", [])
    if not answers:
        raise HTTPException(status_code=400, detail="No quiz data found.")

    score = sum(1 for answer in answers if answer["is_correct"])
    total = len(answers)
    percentage = round((score / total) * 100) if total else 0
    details: list[ReviewItem] = []

    with SessionLocal() as db:
        if request.session.get("user_id") and not request.session.get("quiz_saved"):
            expires_at = (
                datetime.now(timezone.utc) + timedelta(hours=MISSED_QUIZ_EXPIRY_HOURS)
                if status == "timed_out"
                else None
            )
            attempt = QuizAttempt(
                user_id=request.session["user_id"],
                score=score,
                total=total,
                status=status,
                expires_at=expires_at,
            )
            db.add(attempt)
            db.commit()
            db.refresh(attempt)

            for answer in answers:
                db.add(
                    AttemptAnswer(
                        attempt_id=attempt.id,
                        question_id=answer["question_id"],
                        selected_ans=answer["selected"],
                        is_correct=bool(answer["is_correct"]),
                    )
                )
            db.commit()
            request.session["quiz_saved"] = True

        for answer in answers:
            question = db.get(Question, answer["question_id"])
            if question:
                details.append(
                    ReviewItem(
                        question=question.question,
                        selected=answer["selected"],
                        correct=question.correct_ans,
                        is_correct=answer["is_correct"],
                        difficulty=question.difficulty,
                        options={
                            "a": question.option_a,
                            "b": question.option_b,
                            "c": question.option_c,
                            "d": question.option_d,
                        },
                    )
                )

    return QuizResultResponse(
        score=score,
        total=total,
        percentage=percentage,
        details=details,
        timed_out=(status == "timed_out"),
    )


@app.get("/api/quiz/result", response_model=QuizResultResponse)
def quiz_result(request: Request):
    return _finalize_quiz(request)


@app.post("/api/quiz/timeout", response_model=QuizResultResponse)
def timeout_quiz(request: Request):
    """Called when the quiz timer expires. Saves the attempt as timed-out."""
    _require_user(request)
    return _finalize_quiz(request, status="timed_out")


@app.post("/api/quiz/end")
def end_quiz(request: Request):
    request.session.pop("quiz_answers", None)
    request.session.pop("current_difficulty", None)
    request.session.pop("asked_ids", None)
    request.session.pop("quiz_deadline", None)
    request.session.pop("quiz_saved", None)
    request.session["quiz_active"] = False
    return {"message": "Quiz ended. No attempt was recorded."}


# ---------------------------------------------------------------------------
# Routes — Missed Quizzes
# ---------------------------------------------------------------------------

@app.get("/api/quiz/missed")
def get_missed_quizzes(request: Request):
    user = _require_user(request)
    _cleanup_expired_missed()
    with SessionLocal() as db:
        attempts = db.scalars(
            select(QuizAttempt)
            .where(
                QuizAttempt.user_id == user.id,
                QuizAttempt.status == "timed_out",
            )
            .order_by(desc(QuizAttempt.taken_at))
        ).all()

    return [
        MissedAttempt(
            id=a.id,
            score=a.score,
            total=a.total,
            percentage=round((a.score / a.total) * 100) if a.total else 0,
            taken_at=a.taken_at,
            expires_at=a.expires_at,
        )
        for a in attempts
    ]


@app.delete("/api/quiz/missed/{attempt_id}")
def delete_missed_quiz(request: Request, attempt_id: int):
    user = _require_user(request)
    with SessionLocal() as db:
        attempt = db.get(QuizAttempt, attempt_id)
        if not attempt or attempt.user_id != user.id or attempt.status != "timed_out":
            raise HTTPException(status_code=404, detail="Missed quiz not found.")
        db.execute(delete(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt_id))
        db.delete(attempt)
        db.commit()
    return {"message": "Missed quiz dismissed."}


# ---------------------------------------------------------------------------
# Routes — Dashboard
# ---------------------------------------------------------------------------

@app.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(request: Request):
    user = _require_user(request)
    _cleanup_expired_missed()
    with SessionLocal() as db:
        completed_attempts = db.scalars(
            select(QuizAttempt)
            .where(QuizAttempt.user_id == user.id, QuizAttempt.status == "completed")
            .order_by(desc(QuizAttempt.taken_at))
        ).all()

        missed_attempts = db.scalars(
            select(QuizAttempt)
            .where(QuizAttempt.user_id == user.id, QuizAttempt.status == "timed_out")
            .order_by(desc(QuizAttempt.taken_at))
        ).all()

    attempt_payload = [
        {
            "id": attempt.id,
            "score": attempt.score,
            "total": attempt.total,
            "taken_at": attempt.taken_at,
            "percentage": round((attempt.score / attempt.total) * 100) if attempt.total else 0,
            "status": attempt.status,
        }
        for attempt in completed_attempts
    ]

    missed_payload = [
        MissedAttempt(
            id=a.id,
            score=a.score,
            total=a.total,
            percentage=round((a.score / a.total) * 100) if a.total else 0,
            taken_at=a.taken_at,
            expires_at=a.expires_at,
        )
        for a in missed_attempts
    ]

    total_quizzes = len(attempt_payload)
    avg_score = round(sum(item["percentage"] for item in attempt_payload) / total_quizzes) if total_quizzes else 0
    best_score = max((item["percentage"] for item in attempt_payload), default=0)
    total_questions = sum(item["total"] for item in attempt_payload)
    total_correct = sum(item["score"] for item in attempt_payload)

    return {
        "attempts": attempt_payload,
        "missed": missed_payload,
        "stats": {
            "total_quizzes": total_quizzes,
            "avg_score": avg_score,
            "best_score": best_score,
            "total_questions": total_questions,
            "total_correct": total_correct,
        },
    }
