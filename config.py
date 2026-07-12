import os
from pathlib import Path


def load_env_file():
    """Load key=value pairs from .env into os.environ if they are not already set."""
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-for-local-development")

    # SQLite by default, but keep this configurable so MySQL can be swapped back in later.
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///quiz.db")
    FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    # Quiz settings
    QUESTIONS_PER_QUIZ = int(os.environ.get("QUESTIONS_PER_QUIZ", 10))
    QUIZ_TIME_SECONDS = int(os.environ.get("QUIZ_TIME_SECONDS", 300))
