// Centralized API client.
//
// Every call from the React app to the backend goes through this file.
// Why one file?
//   - You can find every endpoint the frontend uses in 60 seconds.
//   - Adding cross-cutting concerns (auth header, error handling, logging)
//     happens once, here, not scattered across pages.
//   - Swapping fetch for axios/ky/TanStack Query later only touches this file.
//
// For a real production frontend you'd probably reach for TanStack Query —
// it adds caching, background refetching, optimistic updates, and request
// dedup on top of this kind of thin wrapper. See CONTRIBUTING.md →
// "Frontend Improvements".

// VITE_API_URL is injected at build time by Vite from .env or docker-compose.
// Falling back to localhost makes local dev work without env config.
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// We persist the JWT in localStorage so a page refresh doesn't log the
// user out. The trade-off: any XSS bug that runs in this origin can read
// the token. A more secure alternative is an HttpOnly cookie set by the
// server on login — but that adds CSRF concerns. For a learning app,
// localStorage is the simplest reasonable choice.
const TOKEN_KEY = "gym_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

// Generic request function. Every method on `api` below uses this.
async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  // Attach the bearer token on every request — the backend reads it from
  // the Authorization header in get_current_user().
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  // 204 No Content = success but nothing to parse.
  if (res.status === 204) return null;

  // Try to parse the body as JSON. If it isn't JSON (e.g. an HTML 500 page),
  // wrap it in a {detail: ...} so error handling below stays uniform.
  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!res.ok) {
    // FastAPI puts error messages in `detail`. We surface them to the UI
    // by throwing — pages catch the error and show err.message in a banner.
    const message = data?.detail || `Request failed (${res.status})`;
    const err = new Error(typeof message === "string" ? message : JSON.stringify(message));
    err.status = res.status; // pages read this to handle 409 specially, etc.
    throw err;
  }
  return data;
}

// Each `api.x()` is a one-liner that names what it does and where it goes.
// Keeping them in one object makes autocomplete + cross-references painless.
export const api = {
  // auth
  register: (body) => request("POST", "/auth/register", body),
  login: (body) => request("POST", "/auth/login", body),
  me: () => request("GET", "/auth/me"),

  // classes
  listClasses: () => request("GET", "/classes"),
  createClass: (body) => request("POST", "/classes", body),
  updateClass: (id, body) => request("PATCH", `/classes/${id}`, body),
  deleteClass: (id, force = false) =>
    request("DELETE", `/classes/${id}${force ? "?force=true" : ""}`),
  classRoster: (id) => request("GET", `/classes/${id}/roster`),

  // enrollments
  enroll: (classId) => request("POST", "/enrollments", { class_id: classId }),
  cancelEnrollment: (id) => request("DELETE", `/enrollments/${id}`),
  myEnrollments: () => request("GET", "/enrollments/me"),

  // members — server-side paginated; URLSearchParams handles encoding
  listMembers: ({ page = 1, pageSize = 10, q = "" } = {}) => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (q) params.set("q", q);
    return request("GET", `/members?${params.toString()}`);
  },
  memberStats: () => request("GET", "/members/stats"),
  addMember: (body) => request("POST", "/members", body),
  removeMember: (id) => request("DELETE", `/members/${id}`),

  // subscriptions
  subscribe: (plan) => request("POST", "/subscriptions", { plan }),
  mySubscription: () => request("GET", "/subscriptions/me"),
};
