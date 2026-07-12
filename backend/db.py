from pathlib import Path
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, create_engine, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from config import Config


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(String(255), nullable=False)
    option_b: Mapped[str] = mapped_column(String(255), nullable=False)
    option_c: Mapped[str] = mapped_column(String(255), nullable=False)
    option_d: Mapped[str] = mapped_column(String(255), nullable=False)
    correct_ans: Mapped[str] = mapped_column(String(1), nullable=False)
    difficulty: Mapped[str] = mapped_column(
        Enum("easy", "medium", "hard", name="difficulty_level"),
        nullable=False,
        default="easy",
    )
    category: Mapped[str] = mapped_column(String(50), default="general")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    taken_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    selected_ans: Mapped[str] = mapped_column(String(1), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


def _build_database_url():
    database_url = Config.DATABASE_URL
    if database_url == "sqlite:///quiz.db":
        db_path = Path(__file__).resolve().parent.parent / "quiz.db"
        return f"sqlite:///{db_path.as_posix()}"
    return database_url


engine = create_engine(
    _build_database_url(),
    connect_args={"check_same_thread": False} if Config.DATABASE_URL.startswith("sqlite") else {},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Migrate existing tables: add new columns if they are missing.
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(quiz_attempts)"))
        columns = {row[1] for row in result}
        if "status" not in columns:
            conn.execute(
                text("ALTER TABLE quiz_attempts ADD COLUMN status VARCHAR(20) DEFAULT 'completed'")
            )
        if "expires_at" not in columns:
            conn.execute(
                text("ALTER TABLE quiz_attempts ADD COLUMN expires_at DATETIME")
            )
        conn.commit()
