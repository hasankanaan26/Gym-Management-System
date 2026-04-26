import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const isManager = user?.role === "manager";

  const linkCls = ({ isActive }) =>
    `px-3 py-2 rounded-md text-sm font-medium ${
      isActive
        ? "bg-slate-900 text-white"
        : "text-slate-700 hover:bg-slate-200"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <Link to="/" className="font-semibold text-lg">
            🏋️ Gym Management
          </Link>
          <nav className="flex items-center gap-1">
            {isManager ? (
              <>
                <NavLink to="/manager" end className={linkCls}>
                  Overview
                </NavLink>
                <NavLink to="/manager/classes" className={linkCls}>
                  Classes
                </NavLink>
                <NavLink to="/manager/members" className={linkCls}>
                  Members
                </NavLink>
              </>
            ) : (
              <>
                <NavLink to="/member" end className={linkCls}>
                  Dashboard
                </NavLink>
                <NavLink to="/member/classes" className={linkCls}>
                  Browse Classes
                </NavLink>
              </>
            )}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">
              {user?.name} <span className="text-slate-400">({user?.role})</span>
            </span>
            <button
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="px-3 py-1.5 rounded-md bg-slate-100 hover:bg-slate-200"
            >
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
