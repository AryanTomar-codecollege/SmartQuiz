from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, session, url_for

from utils.db import query_db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")

    if not user_id:
        flash("Please log in to view your dashboard.", "error")
        return redirect(url_for("auth.login"))

    attempts = query_db(
        """SELECT id, score, total, taken_at,
                  ROUND((score / total) * 100) as percentage
           FROM quiz_attempts
           WHERE user_id = %s
           ORDER BY taken_at DESC""",
        (user_id,),
    )

    for attempt in attempts:
        taken_at = attempt.get("taken_at")
        if isinstance(taken_at, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S GMT"):
                try:
                    attempt["taken_at"] = datetime.strptime(taken_at, fmt)
                    break
                except ValueError:
                    continue

        attempt["percentage"] = int(attempt.get("percentage") or 0)

    total_quizzes = len(attempts)
    if total_quizzes > 0:
        avg_score = round(sum(attempt["percentage"] for attempt in attempts) / total_quizzes)
        best_score = max(attempt["percentage"] for attempt in attempts)
        total_questions = sum(attempt["total"] for attempt in attempts)
        total_correct = sum(attempt["score"] for attempt in attempts)
    else:
        avg_score = 0
        best_score = 0
        total_questions = 0
        total_correct = 0

    stats = {
        "total_quizzes": total_quizzes,
        "avg_score": avg_score,
        "best_score": best_score,
        "total_questions": total_questions,
        "total_correct": total_correct,
    }

    return render_template("dashboard.html", attempts=attempts, stats=stats)
