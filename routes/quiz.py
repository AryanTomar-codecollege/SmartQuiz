from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from config import Config
from utils.adaptive import get_next_difficulty
from utils.db import execute_db, query_db

quiz_bp = Blueprint("quiz", __name__)


def get_quiz_deadline():
    quiz_deadline = session.get("quiz_deadline")
    if not quiz_deadline:
        return None

    try:
        return datetime.fromisoformat(quiz_deadline)
    except ValueError:
        return None


def get_remaining_quiz_time():
    deadline = get_quiz_deadline()
    if deadline is None:
        return Config.QUIZ_TIME_SECONDS

    remaining_seconds = int((deadline - datetime.utcnow()).total_seconds())
    return max(0, remaining_seconds)


@quiz_bp.route("/start")
def start_quiz():
    session["quiz_answers"] = []
    session["current_difficulty"] = "easy"
    session["asked_ids"] = []
    session["quiz_active"] = True
    session["quiz_saved"] = False
    session["quiz_deadline"] = (
        datetime.utcnow() + timedelta(seconds=Config.QUIZ_TIME_SECONDS)
    ).isoformat()

    return redirect(url_for("quiz.next_question"))


@quiz_bp.route("/question")
def next_question():
    if not session.get("quiz_active"):
        return redirect(url_for("quiz.start_quiz"))

    if get_remaining_quiz_time() <= 0:
        flash("Time is up. Your quiz has been submitted.", "info")
        return redirect(url_for("quiz.result"))

    if len(session.get("quiz_answers", [])) >= Config.QUESTIONS_PER_QUIZ:
        return redirect(url_for("quiz.result"))

    difficulty = session.get("current_difficulty", "easy")
    asked_ids = session.get("asked_ids", [])

    if asked_ids:
        placeholders = ", ".join(["%s"] * len(asked_ids))
        sql = f"""
            SELECT * FROM questions
            WHERE difficulty = %s AND id NOT IN ({placeholders})
            ORDER BY RAND() LIMIT 1
        """
        params = (difficulty, *asked_ids)
    else:
        sql = "SELECT * FROM questions WHERE difficulty = %s ORDER BY RAND() LIMIT 1"
        params = (difficulty,)

    question = query_db(sql, params, fetchone=True)

    if not question:
        if asked_ids:
            placeholders = ", ".join(["%s"] * len(asked_ids))
            sql = (
                f"SELECT * FROM questions WHERE id NOT IN ({placeholders}) "
                "ORDER BY RAND() LIMIT 1"
            )
            params = tuple(asked_ids)
        else:
            sql = "SELECT * FROM questions ORDER BY RAND() LIMIT 1"
            params = ()
        question = query_db(sql, params, fetchone=True)

    if not question:
        return redirect(url_for("quiz.result"))

    return render_template(
        "quiz.html",
        question=question,
        question_number=len(session.get("quiz_answers", [])) + 1,
        total_questions=Config.QUESTIONS_PER_QUIZ,
        quiz_time=get_remaining_quiz_time(),
    )


@quiz_bp.route("/answer", methods=["POST"])
def submit_answer():
    if not session.get("quiz_active"):
        return redirect(url_for("quiz.start_quiz"))

    if get_remaining_quiz_time() <= 0:
        flash("Time is up. Your quiz has been submitted.", "info")
        return redirect(url_for("quiz.result"))

    question_id = request.form.get("question_id", type=int)
    selected_ans = request.form.get("selected_ans")

    if question_id is None:
        flash("Invalid question submission.", "error")
        return redirect(url_for("quiz.next_question"))

    question = query_db(
        "SELECT * FROM questions WHERE id = %s",
        (question_id,),
        fetchone=True,
    )

    if not question:
        flash("Question not found.", "error")
        return redirect(url_for("quiz.next_question"))

    is_correct = selected_ans == question["correct_ans"]

    answers = session.get("quiz_answers", [])
    answers.append(
        {
            "question_id": question_id,
            "selected": selected_ans,
            "is_correct": is_correct,
            "difficulty": question["difficulty"],
        }
    )
    session["quiz_answers"] = answers

    asked_ids = session.get("asked_ids", [])
    asked_ids.append(question_id)
    session["asked_ids"] = asked_ids
    session["current_difficulty"] = get_next_difficulty(
        question["difficulty"],
        is_correct,
    )

    return redirect(url_for("quiz.next_question"))


@quiz_bp.route("/result")
def result():
    session["quiz_active"] = False
    answers = session.get("quiz_answers", [])

    if not answers:
        flash("No quiz data found. Start a new quiz.", "info")
        return redirect(url_for("main.index"))

    score = sum(1 for answer in answers if answer["is_correct"])
    total = len(answers)
    percentage = round((score / total) * 100) if total else 0

    result_details = []
    for answer in answers:
        question = query_db(
            "SELECT * FROM questions WHERE id = %s",
            (answer["question_id"],),
            fetchone=True,
        )
        if question:
            result_details.append(
                {
                    "question": question["question"],
                    "selected": answer["selected"],
                    "correct": question["correct_ans"],
                    "is_correct": answer["is_correct"],
                    "difficulty": question["difficulty"],
                    "options": {
                        "a": question["option_a"],
                        "b": question["option_b"],
                        "c": question["option_c"],
                        "d": question["option_d"],
                    },
                }
            )

    user_id = session.get("user_id")
    if user_id and not session.get("quiz_saved"):
        attempt_id = execute_db(
            "INSERT INTO quiz_attempts (user_id, score, total) VALUES (%s, %s, %s)",
            (user_id, score, total),
        )
        for answer in answers:
            execute_db(
                "INSERT INTO attempt_answers (attempt_id, question_id, selected_ans, is_correct) "
                "VALUES (%s, %s, %s, %s)",
                (
                    attempt_id,
                    answer["question_id"],
                    answer["selected"],
                    1 if answer["is_correct"] else 0,
                ),
            )
        session["quiz_saved"] = True

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=percentage,
        details=result_details,
    )


@quiz_bp.route("/end")
def end_quiz():
    session.pop("quiz_answers", None)
    session.pop("current_difficulty", None)
    session.pop("asked_ids", None)
    session.pop("quiz_deadline", None)
    session.pop("quiz_saved", None)
    session["quiz_active"] = False
    flash("Quiz ended. No attempt was recorded.", "info")
    return redirect(url_for("main.index"))
