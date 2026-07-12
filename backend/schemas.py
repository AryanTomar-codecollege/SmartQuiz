from datetime import datetime

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class AuthResponse(BaseModel):
    message: str
    user: dict | None = None


class QuestionOut(BaseModel):
    id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    difficulty: str
    category: str | None = None


class QuizStartResponse(BaseModel):
    question: QuestionOut | None
    question_number: int
    total_questions: int
    quiz_time: int
    quiz_deadline: str
    active: bool


class QuizAnswerRequest(BaseModel):
    question_id: int
    selected_ans: str = Field(pattern="^[abcd]$")


class ReviewItem(BaseModel):
    question: str
    selected: str | None
    correct: str
    is_correct: bool
    difficulty: str
    options: dict[str, str]


class QuizResultResponse(BaseModel):
    score: int
    total: int
    percentage: int
    details: list[ReviewItem]
    timed_out: bool = False


class DashboardAttempt(BaseModel):
    id: int
    score: int
    total: int
    taken_at: datetime
    percentage: int
    status: str = "completed"


class MissedAttempt(BaseModel):
    id: int
    score: int
    total: int
    percentage: int
    taken_at: datetime
    expires_at: datetime | None = None


class DashboardResponse(BaseModel):
    attempts: list[DashboardAttempt]
    missed: list[MissedAttempt]
    stats: dict[str, int]


class UserOut(BaseModel):
    id: int
    username: str
    email: str
