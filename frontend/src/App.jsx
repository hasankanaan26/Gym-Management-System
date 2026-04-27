// Top-level routing — maps URL paths to page components.
//
// Three concepts in here are worth understanding:
//
//   1. **Route guards** (RequireAuth). A wrapper component that checks
//      `useAuth()` and either redirects to /login or to "/" depending on
//      what's missing. Without this, anyone could navigate to /manager
//      directly by typing the URL.
//
//   2. **Nested routes**. The `<Layout />` route has child routes inside.
//      React Router renders the parent's <Outlet /> with the matching
//      child — this is how the sidebar/header stays put while the page
//      body changes.
//
//   3. **Role-based redirects**. The "/" route renders <Home>, which
//      decides whether to send you to /manager or /member based on your
//      role. Centralizing this means the backend doesn't have to care
//      about frontend URLs.

import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import MemberDashboard from "./pages/MemberDashboard.jsx";
import ManagerDashboard from "./pages/ManagerDashboard.jsx";
import BrowseClasses from "./pages/BrowseClasses.jsx";
import ManageClasses from "./pages/ManageClasses.jsx";
import ManageMembers from "./pages/ManageMembers.jsx";
import Layout from "./components/Layout.jsx";

// Wrap any route that requires being logged in. Pass `role` to additionally
// require a specific role; otherwise any logged-in user passes.
function RequireAuth({ children, role }) {
  const { user, loading } = useAuth();
  // Wait for the initial /auth/me check to finish — otherwise we'd
  // redirect to /login on every refresh before the token is validated.
  if (loading) return <div className="p-8">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return children;
}

function Home() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  // Send each role to their natural landing page.
  return user.role === "manager" ? (
    <Navigate to="/manager" replace />
  ) : (
    <Navigate to="/member" replace />
  );
}

export default function App() {
  return (
    <Routes>
      {/* Public routes — no Layout, no auth required. */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Authenticated routes — wrapped in Layout (header/nav). */}
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Home />} />

        <Route
          path="/member"
          element={
            <RequireAuth role="member">
              <MemberDashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/member/classes"
          element={
            <RequireAuth role="member">
              <BrowseClasses />
            </RequireAuth>
          }
        />

        <Route
          path="/manager"
          element={
            <RequireAuth role="manager">
              <ManagerDashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/manager/classes"
          element={
            <RequireAuth role="manager">
              <ManageClasses />
            </RequireAuth>
          }
        />
        <Route
          path="/manager/members"
          element={
            <RequireAuth role="manager">
              <ManageMembers />
            </RequireAuth>
          }
        />
      </Route>

      {/* Catch-all — bounce unknown URLs back to home. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
