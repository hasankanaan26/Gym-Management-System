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

function RequireAuth({ children, role }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (role && user.role !== role) return <Navigate to="/" replace />;
  return children;
}

function Home() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return user.role === "manager" ? (
    <Navigate to="/manager" replace />
  ) : (
    <Navigate to="/member" replace />
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

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

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
