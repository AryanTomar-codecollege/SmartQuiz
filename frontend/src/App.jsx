import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";

const emptyAuth = { username: "", email: "", password: "" };

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("home");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState(emptyAuth);
  const [dashboard, setDashboard] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [result, setResult] = useState(null);
  const [selected, setSelected] = useState("");
  const [quizSecondsLeft, setQuizSecondsLeft] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [pageTransition, setPageTransition] = useState("");

  // Ref to hold the timer-expiry handler so the interval never captures a stale closure.
  const finalizeRef = useRef(null);
  // Guard against double-firing when the timer reaches zero.
  const timerFiredRef = useRef(false);

  // -- Auto-dismiss flash messages ----------------------------------------
  useEffect(() => {
    if (!message) return;
    const t = setTimeout(() => setMessage(""), 4000);
    return () => clearTimeout(t);
  }, [message]);

  useEffect(() => {
    if (!error) return;
    const t = setTimeout(() => setError(""), 6000);
    return () => clearTimeout(t);
  }, [error]);

  // -- Auth check on mount ------------------------------------------------
  useEffect(() => {
    api
      .me()
      .then((data) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  // -- Timer-expiry handler (saved in a ref) ------------------------------
  const handleTimerExpiry = useCallback(async () => {
    try {
      const data = await api.timeoutQuiz();
      setResult(data);
      setQuiz(null);
      setQuizSecondsLeft(0);
      setView("result");
    } catch (err) {
      setError(err.message);
      setQuiz(null);
      setQuizSecondsLeft(0);
      setView("home");
    }
  }, []);

  useEffect(() => {
    finalizeRef.current = handleTimerExpiry;
  }, [handleTimerExpiry]);

  // -- Quiz countdown timer -----------------------------------------------
  useEffect(() => {
    if (!quiz) return;
    const interval = setInterval(() => {
      setQuizSecondsLeft((current) => {
        if (current <= 1) {
          clearInterval(interval);
          return 0;
        }
        return current - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [quiz]);

  // When the timer hits 0 while a quiz is active, finalize once.
  useEffect(() => {
    if (quiz && quizSecondsLeft <= 0 && !timerFiredRef.current) {
      timerFiredRef.current = true;
      finalizeRef.current?.();
    }
  }, [quiz, quizSecondsLeft]);

  const isLoggedIn = !!user;

  // -- Navigation with fade transition ------------------------------------
  function navigate(newView) {
    setPageTransition("fade-out");
    setTimeout(() => {
      setView(newView);
      setPageTransition("fade-in");
      setTimeout(() => setPageTransition(""), 300);
    }, 150);
    setMobileMenuOpen(false);
  }

  // -- Auth ---------------------------------------------------------------
  async function submitAuth(event) {
    event.preventDefault();
    if (submitting) return;
    setError("");
    setMessage("");
    setSubmitting(true);
    try {
      const payload =
        authMode === "signup"
          ? {
              username: authForm.username.trim(),
              email: authForm.email.trim(),
              password: authForm.password,
            }
          : {
              username: authForm.username.trim(),
              password: authForm.password,
            };
      const data =
        authMode === "signup"
          ? await api.signup(payload)
          : await api.login(payload);
      setUser(data.user);
      setMessage(data.message);
      setAuthForm(emptyAuth);
      navigate("home");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  // -- Quiz ---------------------------------------------------------------
  async function startQuiz() {
    if (submitting) return;
    setError("");
    setMessage("");
    setSubmitting(true);
    timerFiredRef.current = false;
    try {
      const data = await api.startQuiz();
      setQuiz(data);
      setResult(null);
      setSelected("");
      setQuizSecondsLeft(data.quiz_time || 0);
      navigate("quiz");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function submitAnswer(event) {
    event.preventDefault();
    if (!quiz?.question || !selected || submitting) return;
    setError("");
    setSubmitting(true);
    try {
      const data = await api.answerQuiz({
        question_id: quiz.question.id,
        selected_ans: selected,
      });
      if (data.details) {
        setResult(data);
        setQuiz(null);
        setQuizSecondsLeft(0);
        navigate("result");
      } else {
        setQuiz(data);
        setSelected("");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function endQuiz() {
    await api.endQuiz();
    setQuiz(null);
    setSelected("");
    setQuizSecondsLeft(0);
    navigate("home");
  }

  // -- Dashboard ----------------------------------------------------------
  async function openDashboard() {
    if (submitting) return;
    setError("");
    setSubmitting(true);
    try {
      const data = await api.dashboard();
      setDashboard(data);
      navigate("dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function dismissMissed(id) {
    try {
      await api.deleteMissedQuiz(id);
      if (dashboard) {
        setDashboard({
          ...dashboard,
          missed: dashboard.missed.filter((m) => m.id !== id),
        });
      }
    } catch (err) {
      setError(err.message);
    }
  }

  // -- Logout -------------------------------------------------------------
  async function logout() {
    await api.logout();
    setUser(null);
    setDashboard(null);
    setQuiz(null);
    setResult(null);
    setQuizSecondsLeft(0);
    navigate("home");
  }

  // -- Auth view helpers --------------------------------------------------
  function openLogin() {
    setAuthMode("login");
    setAuthForm(emptyAuth);
    setError("");
    setMessage("");
    navigate("login");
  }

  function openSignup() {
    setAuthMode("signup");
    setAuthForm(emptyAuth);
    setError("");
    setMessage("");
    navigate("signup");
  }

  // -- Derived values -----------------------------------------------------
  const currentQuestion = quiz?.question;
  const percentageClass = result
    ? result.percentage >= 80
      ? "great"
      : result.percentage >= 50
        ? "good"
        : "low"
    : "low";
  const minutes = Math.floor(quizSecondsLeft / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (quizSecondsLeft % 60).toString().padStart(2, "0");
  const timerUrgency =
    quizSecondsLeft <= 30
      ? "danger"
      : quizSecondsLeft <= 60
        ? "warning"
        : "calm";

  // =====================================================================
  // Render
  // =====================================================================
  return (
    <div className="app-shell">
      {/* ---------- Navbar ---------- */}
      <header className="navbar">
        <div className="nav-container">
          <button
            className="nav-logo"
            onClick={() => navigate("home")}
            id="nav-home"
          >
            <span className="logo-badge" aria-hidden="true">
              SQ
            </span>
            <span className="logo-text">
              Smart<span className="logo-accent">Quiz</span>
            </span>
          </button>

          <button
            className="mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
            id="mobile-menu-toggle"
          >
            <span className={`hamburger ${mobileMenuOpen ? "open" : ""}`}>
              <span></span>
              <span></span>
              <span></span>
            </span>
          </button>

          <nav
            className={`nav-links ${mobileMenuOpen ? "nav-links--open" : ""}`}
          >
            <button
              className="nav-link"
              onClick={() => navigate("home")}
              id="nav-home-link"
            >
              Home
            </button>
            {isLoggedIn ? (
              <>
                <button
                  className="nav-link"
                  onClick={() => {
                    startQuiz();
                    setMobileMenuOpen(false);
                  }}
                  id="nav-start-quiz"
                >
                  Start Quiz
                </button>
                <button
                  className="nav-link"
                  onClick={() => {
                    openDashboard();
                    setMobileMenuOpen(false);
                  }}
                  id="nav-dashboard"
                >
                  Dashboard
                </button>
                <span className="nav-user">
                  <span className="nav-avatar">
                    {user.username[0].toUpperCase()}
                  </span>
                  <span className="nav-username">{user.username}</span>
                </span>
                <button
                  className="nav-link nav-link--logout"
                  onClick={logout}
                  id="nav-logout"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <button
                  className="nav-link"
                  onClick={openLogin}
                  id="nav-login"
                >
                  Login
                </button>
                <button
                  className="nav-link nav-link--primary"
                  onClick={openSignup}
                  id="nav-signup"
                >
                  Sign Up
                </button>
              </>
            )}
          </nav>
        </div>
      </header>

      {/* ---------- Main Content ---------- */}
      <main className={`page ${pageTransition}`}>
        {/* Flash messages */}
        {error && (
          <div
            className="flash flash--error"
            onClick={() => setError("")}
            id="flash-error"
          >
            {error}
          </div>
        )}
        {message && (
          <div
            className="flash flash--success"
            onClick={() => setMessage("")}
            id="flash-success"
          >
            {message}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <section className="center-panel">
            <div className="spinner"></div>
            <p className="loading-text">Loading SmartQuiz…</p>
          </section>
        )}

        {/* ==================== HOME ==================== */}
        {!loading && view === "home" && (
          <>
            <section className="hero" id="hero-section">
              <div className="hero-bg">
                <div className="hero-orb hero-orb--1" />
                <div className="hero-orb hero-orb--2" />
                <div className="hero-orb hero-orb--3" />
              </div>
              <div className="hero-content">
                <div className="hero-badge">⚡ Adaptive Learning Engine</div>
                <h1 className="hero-title">
                  Test Your Knowledge
                  <br />
                  <span className="hero-gradient">Intelligently</span>
                </h1>
                <p className="hero-subtitle">
                  Our adaptive quiz engine adjusts difficulty in real time based
                  on your performance. The better you answer, the harder it
                  gets. Track your progress and master any topic.
                </p>
                <div className="hero-actions">
                  {isLoggedIn ? (
                    <>
                      <button
                        className="btn btn--glow btn--large"
                        onClick={startQuiz}
                        disabled={submitting}
                        id="hero-start-quiz"
                      >
                        {submitting ? "Starting…" : "🚀 Start Quiz"}
                      </button>
                      <button
                        className="btn btn--glass btn--large"
                        onClick={openDashboard}
                        disabled={submitting}
                        id="hero-dashboard"
                      >
                        📊 Dashboard
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="btn btn--glow btn--large"
                        onClick={openSignup}
                        id="hero-signup"
                      >
                        Get Started Free
                      </button>
                      <button
                        className="btn btn--glass btn--large"
                        onClick={openLogin}
                        id="hero-login"
                      >
                        Login
                      </button>
                    </>
                  )}
                </div>
              </div>
            </section>

            <section className="features" id="features-section">
              <div className="features-grid">
                <div className="feature-card">
                  <div className="feature-icon">🧠</div>
                  <h3 className="feature-title">Adaptive Difficulty</h3>
                  <p className="feature-desc">
                    Questions dynamically adjust from easy to hard based on your
                    answers. Stay challenged, always.
                  </p>
                </div>
                <div className="feature-card">
                  <div className="feature-icon">📈</div>
                  <h3 className="feature-title">Track Progress</h3>
                  <p className="feature-desc">
                    Detailed dashboard with score history, averages, and
                    performance trends over time.
                  </p>
                </div>
                <div className="feature-card">
                  <div className="feature-icon">⏱️</div>
                  <h3 className="feature-title">Timed Challenges</h3>
                  <p className="feature-desc">
                    5-minute timed quizzes that test both knowledge and speed.
                    Can you beat the clock?
                  </p>
                </div>
              </div>
            </section>
          </>
        )}

        {/* ==================== LOGIN ==================== */}
        {!loading && view === "login" && (
          <section className="auth-section" id="login-section">
            <div className="auth-card glass-card">
              <div className="auth-header">
                <div className="auth-icon">👋</div>
                <h2 className="auth-title">Welcome Back</h2>
                <p className="auth-subtitle">
                  Log in to continue your quiz journey
                </p>
              </div>
              <form className="auth-form" onSubmit={submitAuth}>
                <div className="form-group">
                  <label className="form-label" htmlFor="login-username">
                    Username
                  </label>
                  <input
                    id="login-username"
                    className="form-input"
                    placeholder="Enter your username"
                    autoComplete="username"
                    value={authForm.username}
                    onChange={(e) =>
                      setAuthForm({ ...authForm, username: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="login-password">
                    Password
                  </label>
                  <input
                    id="login-password"
                    type="password"
                    className="form-input"
                    placeholder="Enter your password"
                    autoComplete="current-password"
                    value={authForm.password}
                    onChange={(e) =>
                      setAuthForm({ ...authForm, password: e.target.value })
                    }
                  />
                </div>
                <button
                  className="btn btn--glow btn--full"
                  type="submit"
                  disabled={submitting}
                  id="login-submit"
                >
                  {submitting ? "Logging in…" : "Login"}
                </button>
              </form>
              <p className="auth-footer">
                Don&rsquo;t have an account?{" "}
                <button className="link-button" onClick={openSignup}>
                  Sign Up
                </button>
              </p>
            </div>
          </section>
        )}

        {/* ==================== SIGNUP ==================== */}
        {!loading && view === "signup" && (
          <section className="auth-section" id="signup-section">
            <div className="auth-card glass-card">
              <div className="auth-header">
                <div className="auth-icon">🎉</div>
                <h2 className="auth-title">Create Account</h2>
                <p className="auth-subtitle">
                  Join SmartQuiz and start learning today
                </p>
              </div>
              <form className="auth-form" onSubmit={submitAuth}>
                <div className="form-group">
                  <label className="form-label" htmlFor="signup-username">
                    Username
                  </label>
                  <input
                    id="signup-username"
                    className="form-input"
                    placeholder="Choose a username"
                    autoComplete="username"
                    value={authForm.username}
                    onChange={(e) =>
                      setAuthForm({ ...authForm, username: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="signup-email">
                    Email
                  </label>
                  <input
                    id="signup-email"
                    type="email"
                    className="form-input"
                    placeholder="you@example.com"
                    autoComplete="email"
                    value={authForm.email}
                    onChange={(e) =>
                      setAuthForm({ ...authForm, email: e.target.value })
                    }
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="signup-password">
                    Password
                  </label>
                  <input
                    id="signup-password"
                    type="password"
                    className="form-input"
                    placeholder="At least 6 characters"
                    autoComplete="new-password"
                    value={authForm.password}
                    onChange={(e) =>
                      setAuthForm({ ...authForm, password: e.target.value })
                    }
                  />
                </div>
                <button
                  className="btn btn--glow btn--full"
                  type="submit"
                  disabled={submitting}
                  id="signup-submit"
                >
                  {submitting ? "Creating…" : "Create Account"}
                </button>
              </form>
              <p className="auth-footer">
                Already have an account?{" "}
                <button className="link-button" onClick={openLogin}>
                  Login
                </button>
              </p>
            </div>
          </section>
        )}

        {/* ==================== QUIZ ==================== */}
        {!loading && view === "quiz" && currentQuestion && (
          <section className="quiz-section" id="quiz-section">
            <div className="quiz-header-bar">
              <div className="quiz-info">
                <span className="quiz-counter">
                  Question {quiz.question_number} of {quiz.total_questions}
                </span>
                <div
                  className={`difficulty-badge difficulty--${currentQuestion.difficulty}`}
                >
                  {currentQuestion.difficulty === "easy"
                    ? "🟢"
                    : currentQuestion.difficulty === "medium"
                      ? "🟡"
                      : "🔴"}{" "}
                  {currentQuestion.difficulty.charAt(0).toUpperCase() +
                    currentQuestion.difficulty.slice(1)}
                </div>
              </div>
              <div className={`timer timer--${timerUrgency}`}>
                <svg
                  className="timer-icon"
                  viewBox="0 0 24 24"
                  width="18"
                  height="18"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                <span className="timer-text">
                  {minutes}:{seconds}
                </span>
              </div>
            </div>

            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${(quiz.question_number / quiz.total_questions) * 100}%`,
                }}
              />
            </div>

            <div className="question-card glass-card">
              <h2 className="question-text">{currentQuestion.question}</h2>
              <form onSubmit={submitAnswer} id="quiz-form">
                <div className="options-grid">
                  {[
                    ["a", currentQuestion.option_a],
                    ["b", currentQuestion.option_b],
                    ["c", currentQuestion.option_c],
                    ["d", currentQuestion.option_d],
                  ].map(([key, text]) => (
                    <label
                      className={`option-card ${selected === key ? "option-card--selected" : ""}`}
                      key={key}
                      htmlFor={`option-${key}`}
                    >
                      <input
                        type="radio"
                        name="selected_ans"
                        id={`option-${key}`}
                        value={key}
                        checked={selected === key}
                        onChange={() => setSelected(key)}
                        className="option-radio"
                      />
                      <span className="option-letter">
                        {key.toUpperCase()}
                      </span>
                      <span className="option-text">{text}</span>
                      {selected === key && (
                        <span className="option-check">✓</span>
                      )}
                    </label>
                  ))}
                </div>
                <div className="quiz-actions">
                  <button
                    className="btn btn--glow btn--large btn--flex"
                    type="submit"
                    disabled={!selected || submitting}
                    id="quiz-submit"
                  >
                    {submitting
                      ? "Submitting…"
                      : quiz.question_number === quiz.total_questions
                        ? "🏁 Finish Quiz"
                        : "Next →"}
                  </button>
                  <button
                    className="btn btn--glass btn--large btn--flex btn--danger"
                    type="button"
                    onClick={endQuiz}
                    id="quiz-end"
                  >
                    ✕ End Test
                  </button>
                </div>
              </form>
            </div>
          </section>
        )}

        {/* ==================== RESULT ==================== */}
        {!loading && view === "result" && result && (
          <section className="result-section" id="result-section">
            <div className="score-hero glass-card">
              {result.timed_out && (
                <div className="timeout-banner">⏰ Time&rsquo;s Up!</div>
              )}
              <div
                className={`score-ring score-ring--${percentageClass}`}
                style={{ "--score-pct": result.percentage }}
              >
                <span className="score-value">{result.percentage}%</span>
                <span className="score-label">Score</span>
              </div>
              <h2 className="result-title">
                {result.timed_out
                  ? "Quiz Timed Out"
                  : result.percentage >= 80
                    ? "🎉 Excellent Work!"
                    : result.percentage >= 50
                      ? "👍 Good Job!"
                      : "💪 Keep Practicing!"}
              </h2>
              <p className="result-summary">
                You answered <strong>{result.score}</strong> out of{" "}
                <strong>{result.total}</strong> questions correctly.
                {result.timed_out &&
                  " This quiz has been saved as a missed attempt — you can reattempt it from your dashboard."}
              </p>
            </div>

            <div className="review-section">
              <h3 className="section-title">📝 Answer Review</h3>
              <div className="review-grid">
                {result.details.map((item, index) => (
                  <div
                    className={`review-card ${item.is_correct ? "review-card--correct" : "review-card--wrong"}`}
                    key={index}
                  >
                    <div className="review-header">
                      <span
                        className={`review-badge ${item.is_correct ? "review-badge--correct" : "review-badge--wrong"}`}
                      >
                        {item.is_correct ? "✓ Correct" : "✕ Wrong"}
                      </span>
                      <span
                        className={`difficulty-badge difficulty--${item.difficulty}`}
                      >
                        {item.difficulty.charAt(0).toUpperCase() +
                          item.difficulty.slice(1)}
                      </span>
                    </div>
                    <p className="review-question">{item.question}</p>
                    <div className="review-answers">
                      <p className="review-your-answer">
                        Your answer:{" "}
                        <strong>
                          {item.options[item.selected] || "No answer"}
                        </strong>
                      </p>
                      {!item.is_correct && (
                        <p className="review-correct-answer">
                          Correct:{" "}
                          <strong>{item.options[item.correct]}</strong>
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="result-actions">
              <button
                className="btn btn--glow btn--large"
                onClick={startQuiz}
                disabled={submitting}
                id="result-retry"
              >
                {submitting ? "Starting…" : "🔄 Try Again"}
              </button>
              {isLoggedIn && (
                <button
                  className="btn btn--glass btn--large"
                  onClick={openDashboard}
                  disabled={submitting}
                  id="result-dashboard"
                >
                  📊 Dashboard
                </button>
              )}
              <button
                className="btn btn--glass btn--large"
                onClick={() => navigate("home")}
                id="result-home"
              >
                🏠 Home
              </button>
            </div>
          </section>
        )}

        {/* ==================== DASHBOARD ==================== */}
        {!loading && view === "dashboard" && dashboard && (
          <section className="dashboard-section" id="dashboard-section">
            <h2 className="page-title">📊 Your Dashboard</h2>

            {/* Stats */}
            <div className="stats-grid">
              <StatCard
                icon="🎯"
                label="Quizzes Taken"
                value={dashboard.stats.total_quizzes}
              />
              <StatCard
                icon="📈"
                label="Average Score"
                value={`${dashboard.stats.avg_score}%`}
              />
              <StatCard
                icon="🏆"
                label="Best Score"
                value={`${dashboard.stats.best_score}%`}
              />
              <StatCard
                icon="✅"
                label="Total Correct"
                value={`${dashboard.stats.total_correct}/${dashboard.stats.total_questions}`}
              />
            </div>

            {/* Missed Quizzes */}
            {dashboard.missed && dashboard.missed.length > 0 && (
              <div className="missed-section glass-card" id="missed-section">
                <h3 className="section-title">⏰ Missed Quizzes</h3>
                <p className="section-desc">
                  These quizzes timed out. Reattempt before they auto-delete (24
                  hrs)!
                </p>
                <div className="missed-grid">
                  {dashboard.missed.map((item) => (
                    <div className="missed-card" key={item.id}>
                      <div className="missed-info">
                        <span className="missed-score">
                          {item.score}/{item.total} ({item.percentage}%)
                        </span>
                        <span className="missed-date">
                          {new Date(item.taken_at).toLocaleDateString(
                            undefined,
                            {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            },
                          )}
                        </span>
                        {item.expires_at && (
                          <span className="missed-expires">
                            Expires:{" "}
                            {new Date(item.expires_at).toLocaleString(
                              undefined,
                              {
                                month: "short",
                                day: "numeric",
                                hour: "2-digit",
                                minute: "2-digit",
                              },
                            )}
                          </span>
                        )}
                      </div>
                      <div className="missed-actions">
                        <button
                          className="btn btn--glow btn--small"
                          onClick={startQuiz}
                          disabled={submitting}
                        >
                          Reattempt
                        </button>
                        <button
                          className="btn btn--ghost btn--small"
                          onClick={() => dismissMissed(item.id)}
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quiz History */}
            <div className="history-section glass-card" id="history-section">
              <h3 className="section-title">📋 Quiz History</h3>
              {dashboard.attempts.length ? (
                <div className="history-table-wrapper">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Date</th>
                        <th>Score</th>
                        <th>Progress</th>
                        <th>Rating</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboard.attempts.map((attempt, index) => (
                        <tr key={attempt.id}>
                          <td>{index + 1}</td>
                          <td>
                            {new Date(attempt.taken_at).toLocaleDateString(
                              undefined,
                              {
                                month: "short",
                                day: "numeric",
                                year: "numeric",
                              },
                            )}
                          </td>
                          <td className="score-cell">
                            {attempt.score} / {attempt.total}
                          </td>
                          <td>
                            <div className="mini-progress">
                              <div
                                className={`mini-progress-fill mini-progress--${attempt.percentage >= 80 ? "great" : attempt.percentage >= 50 ? "good" : "low"}`}
                                style={{
                                  width: `${attempt.percentage}%`,
                                }}
                              />
                            </div>
                            <span className="mini-percent">
                              {attempt.percentage}%
                            </span>
                          </td>
                          <td>
                            <span
                              className={`rating-pill rating--${attempt.percentage >= 80 ? "great" : attempt.percentage >= 50 ? "good" : "low"}`}
                            >
                              {attempt.percentage >= 80
                                ? "🌟 Excellent"
                                : attempt.percentage >= 50
                                  ? "👍 Good"
                                  : "📚 Practice"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">
                  <div className="empty-icon">📝</div>
                  <p>No completed quizzes yet. Start your first quiz!</p>
                </div>
              )}
            </div>

            <div className="dashboard-actions">
              <button
                className="btn btn--glow btn--large"
                onClick={startQuiz}
                disabled={submitting}
                id="dashboard-start-quiz"
              >
                {submitting ? "Starting…" : "🚀 Take New Quiz"}
              </button>
            </div>
          </section>
        )}
      </main>

      {/* ---------- Footer ---------- */}
      <footer className="footer">
        <p>SmartQuiz — Adaptive learning for everyone</p>
      </footer>
    </div>
  );
}

// =========================================================================
// Small sub-component
// =========================================================================
function StatCard({ icon, label, value }) {
  return (
    <div className="stat-card glass-card">
      <span className="stat-icon">{icon}</span>
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
