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

    # MySQL database configuration
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "smart_quiz")

    # Quiz settings
    QUESTIONS_PER_QUIZ = int(os.environ.get("QUESTIONS_PER_QUIZ", 10))
    QUIZ_TIME_SECONDS = int(os.environ.get("QUIZ_TIME_SECONDS", 300))
