// Auth context — global "who is logged in?" state for the React app.
//
// React Context is built into React. It's how you share state without
// passing props through every intermediate component ("prop drilling").
// Any component that needs the current user just calls `useAuth()`.
//
// On app load we check whether there's a saved JWT and, if so, fetch
// /auth/me to confirm it's still valid. That handles the page-refresh
// case: the user stays logged in until their token expires.
//
// In a larger app you might switch to Zustand, Redux, or Jotai. For
// auth state specifically, Context is more than enough — it doesn't
// change often.

import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";

// `null` is the initial value when no provider is present. We never read
// it because <AuthProvider> wraps the entire app in main.jsx.
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // `loading` lets pages show a "Loading…" placeholder while we figure
  // out if the saved token is still valid — without this, the UI flashes
  // the login page for a frame before redirecting.
  const [loading, setLoading] = useState(true);

  // Run once on mount: try to revive the session from a saved token.
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then((u) => setUser(u))
      // If /me fails the token is bad/expired — wipe it.
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const res = await api.login({ email, password });
    setToken(res.access_token);
    setUser(res.user);
    return res.user; // returned so pages can redirect by role immediately
  }

  async function register(email, password, name) {
    const res = await api.register({ email, password, name });
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  }

  function logout() {
    setToken(null);
    setUser(null);
    // Note: we don't tell the server. Stateless JWT design — there's no
    // server-side session to invalidate. To support real logout/revocation
    // you'd add a token blacklist or switch to short-lived access tokens
    // plus refresh tokens. (Another good contribution opportunity.)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Tiny helper so components don't have to import AuthContext directly.
export function useAuth() {
  return useContext(AuthContext);
}
