const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    throw new Error(data?.detail || data?.message || "Request failed");
  }

  return data;
}

export const api = {
  me: () => request("/api/me"),
  signup: (payload) => request("/api/auth/signup", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/api/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  startQuiz: () => request("/api/quiz/start", { method: "POST" }),
  currentQuiz: () => request("/api/quiz/current"),
  answerQuiz: (payload) => request("/api/quiz/answer", { method: "POST", body: JSON.stringify(payload) }),
  resultQuiz: () => request("/api/quiz/result"),
  endQuiz: () => request("/api/quiz/end", { method: "POST" }),
  timeoutQuiz: () => request("/api/quiz/timeout", { method: "POST" }),
  dashboard: () => request("/api/dashboard"),
  missedQuizzes: () => request("/api/quiz/missed"),
  deleteMissedQuiz: (id) => request(`/api/quiz/missed/${id}`, { method: "DELETE" }),
};
