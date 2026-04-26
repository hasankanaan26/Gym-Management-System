import { useEffect, useState } from "react";
import { api } from "../api.js";
import {
  Button,
  Card,
  ErrorBanner,
  formatTime,
  titleCase,
} from "../components/ui.jsx";

export default function BrowseClasses() {
  const [classes, setClasses] = useState([]);
  const [mine, setMine] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setError(null);
    try {
      const [all, enrolled] = await Promise.all([
        api.listClasses(),
        api.myEnrollments(),
      ]);
      setClasses(all);
      setMine(enrolled);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const enrolledIds = new Set(mine.map((e) => e.gym_class.id));
  const enrollmentByClass = Object.fromEntries(
    mine.map((e) => [e.gym_class.id, e.id])
  );

  async function onEnroll(classId) {
    setError(null);
    try {
      await api.enroll(classId);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onCancel(classId) {
    setError(null);
    try {
      await api.cancelEnrollment(enrollmentByClass[classId]);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <div>Loading…</div>;

  return (
    <div>
      <ErrorBanner error={error} />
      <Card title="All classes">
        {classes.length === 0 ? (
          <p className="text-sm text-slate-600">No classes available.</p>
        ) : (
          <ul className="divide-y divide-slate-200">
            {classes.map((c) => {
              const full = c.enrolled_count >= c.capacity;
              const enrolled = enrolledIds.has(c.id);
              return (
                <li key={c.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="font-medium">{c.name}</div>
                    <div className="text-sm text-slate-600">
                      {titleCase(c.day_of_week)} · {formatTime(c.start_time)} ·{" "}
                      {c.duration_minutes} min · {c.trainer_name}
                    </div>
                    {c.description && (
                      <div className="text-sm text-slate-500 mt-1">
                        {c.description}
                      </div>
                    )}
                    <div className="text-xs text-slate-500 mt-1">
                      {c.enrolled_count} / {c.capacity} enrolled
                    </div>
                  </div>
                  <div>
                    {enrolled ? (
                      <Button variant="danger" onClick={() => onCancel(c.id)}>
                        Cancel
                      </Button>
                    ) : (
                      <Button
                        onClick={() => onEnroll(c.id)}
                        disabled={full}
                        title={full ? "Class full" : ""}
                      >
                        {full ? "Full" : "Enroll"}
                      </Button>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </div>
  );
}
