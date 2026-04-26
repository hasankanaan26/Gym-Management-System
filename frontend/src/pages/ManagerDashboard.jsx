import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import { Badge, Button, Card, ErrorBanner } from "../components/ui.jsx";

export default function ManagerDashboard() {
  const [stats, setStats] = useState({ total: 0, active: 0, inactive: 0 });
  const [classes, setClasses] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [s, c] = await Promise.all([api.memberStats(), api.listClasses()]);
        setStats(s);
        setClasses(c);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <div>Loading…</div>;

  const totalEnrollments = classes.reduce((n, c) => n + c.enrolled_count, 0);

  return (
    <div>
      <ErrorBanner error={error} />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <Card title="Members">
          <div className="text-3xl font-bold">{stats.total}</div>
          <div className="text-sm text-slate-600">
            <Badge color="green">{stats.active} active</Badge>{" "}
            <Badge color="red">{stats.inactive} inactive</Badge>
          </div>
        </Card>
        <Card title="Classes">
          <div className="text-3xl font-bold">{classes.length}</div>
          <div className="text-sm text-slate-600">Across the week</div>
        </Card>
        <Card title="Enrollments">
          <div className="text-3xl font-bold">{totalEnrollments}</div>
          <div className="text-sm text-slate-600">Across all classes</div>
        </Card>
      </div>

      <Card
        title="Classes overview"
        actions={
          <Link to="/manager/classes">
            <Button variant="secondary">Manage classes</Button>
          </Link>
        }
      >
        {classes.length === 0 ? (
          <p className="text-sm text-slate-600">No classes yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500">
              <tr>
                <th className="py-2">Name</th>
                <th>Trainer</th>
                <th>Day / Time</th>
                <th>Enrolled</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {classes.map((c) => (
                <tr key={c.id}>
                  <td className="py-2 font-medium">{c.name}</td>
                  <td>{c.trainer_name}</td>
                  <td>
                    {c.day_of_week} {c.start_time}
                  </td>
                  <td>
                    {c.enrolled_count} / {c.capacity}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
