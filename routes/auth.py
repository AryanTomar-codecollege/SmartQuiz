from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from utils.db import execute_db, query_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("signup.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("signup.html")

        existing = query_db(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email),
            fetchone=True,
        )
        if existing:
            flash("Username or email already exists.", "error")
            return render_template("signup.html")

        hashed = generate_password_hash(password)
        execute_db(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed),
        )

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("All fields are required.", "error")
            return render_template("login.html")

        user = query_db(
            "SELECT * FROM users WHERE username = %s",
            (username,),
            fetchone=True,
        )

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("main.index"))

        flash("Invalid username or password.", "error")
        return render_template("login.html")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
