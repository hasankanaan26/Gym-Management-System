// Centralized fetch wrapper — every call to the backend goes through here.

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const TOKEN_KEY = "gym_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

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
    const message = data?.detail || `Request failed (${res.status})`;
    const err = new Error(typeof message === "string" ? message : JSON.stringify(message));
    err.status = res.status;
    throw err;
  }
  return data;
}

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

  // members
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
