// ManageClasses — manager CRUD for classes.
//
// One form serves both Create and Edit: when `editingId` is null we POST,
// otherwise we PATCH. This is a common React pattern that avoids two
// nearly-identical forms.
//
// Roster expand/collapse is per-class state stored in `roster.open`. A
// proper modal would be more accessible — accessibility audit is on the
// contribution list (CONTRIBUTING.md → "Frontend Improvements").

import { useEffect, useState } from "react";
import { api } from "../api.js";
import {
  Button,
  Card,
  ErrorBanner,
  Input,
  Label,
  Select,
  formatTime,
  titleCase,
} from "../components/ui.jsx";

const DAYS = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];

const EMPTY = {
  name: "",
  description: "",
  trainer_name: "",
  day_of_week: "monday",
  start_time: "08:00",
  duration_minutes: 60,
  capacity: 20,
};

export default function ManageClasses() {
  const [classes, setClasses] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [roster, setRoster] = useState({ open: null, items: [] });

  async function load() {
    setError(null);
    try {
      const data = await api.listClasses();
      setClasses(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function resetForm() {
    setEditingId(null);
    setForm(EMPTY);
  }

  function startEdit(c) {
    setEditingId(c.id);
    setForm({
      name: c.name,
      description: c.description || "",
      trainer_name: c.trainer_name,
      day_of_week: c.day_of_week,
      start_time: c.start_time.slice(0, 5),
      duration_minutes: c.duration_minutes,
      capacity: c.capacity,
    });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    const body = {
      ...form,
      duration_minutes: Number(form.duration_minutes),
      capacity: Number(form.capacity),
    };
    try {
      if (editingId) {
        await api.updateClass(editingId, body);
      } else {
        await api.createClass(body);
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onDelete(c) {
    if (!confirm(`Delete "${c.name}"?`)) return;
    try {
      await api.deleteClass(c.id);
      await load();
    } catch (err) {
      if (err.status === 409) {
        if (
          confirm(
            `${err.message}\n\nDelete anyway and drop all enrollments?`
          )
        ) {
          try {
            await api.deleteClass(c.id, true);
            await load();
            return;
          } catch (e2) {
            setError(e2.message);
            return;
          }
        }
      } else {
        setError(err.message);
      }
    }
  }

  async function toggleRoster(classId) {
    if (roster.open === classId) {
      setRoster({ open: null, items: [] });
      return;
    }
    try {
      const items = await api.classRoster(classId);
      setRoster({ open: classId, items });
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <div>Loading…</div>;

  return (
    <div>
      <ErrorBanner error={error} />

      <Card title={editingId ? "Edit class" : "Create a class"}>
        <form onSubmit={onSubmit} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <Label>Name</Label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Description</Label>
            <Input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div>
            <Label>Trainer</Label>
            <Input
              value={form.trainer_name}
              onChange={(e) => setForm({ ...form, trainer_name: e.target.value })}
              required
            />
          </div>
          <div>
            <Label>Day</Label>
            <Select
              value={form.day_of_week}
              onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}
            >
              {DAYS.map((d) => (
                <option key={d} value={d}>
                  {titleCase(d)}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Start time</Label>
            <Input
              type="time"
              value={form.start_time}
              onChange={(e) => setForm({ ...form, start_time: e.target.value })}
              required
            />
          </div>
          <div>
            <Label>Duration (min)</Label>
            <Input
              type="number"
              min={15}
              max={240}
              value={form.duration_minutes}
              onChange={(e) =>
                setForm({ ...form, duration_minutes: e.target.value })
              }
              required
            />
          </div>
          <div>
            <Label>Capacity</Label>
            <Input
              type="number"
              min={1}
              max={200}
              value={form.capacity}
              onChange={(e) => setForm({ ...form, capacity: e.target.value })}
              required
            />
          </div>
          <div className="sm:col-span-2 flex gap-2 justify-end">
            {editingId && (
              <Button type="button" variant="secondary" onClick={resetForm}>
                Cancel
              </Button>
            )}
            <Button type="submit">{editingId ? "Save" : "Create class"}</Button>
          </div>
        </form>
      </Card>

      <Card title="All classes">
        {classes.length === 0 ? (
          <p className="text-sm text-slate-600">No classes yet.</p>
        ) : (
          <ul className="divide-y divide-slate-200">
            {classes.map((c) => (
              <li key={c.id} className="py-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-medium">{c.name}</div>
                    <div className="text-sm text-slate-600">
                      {titleCase(c.day_of_week)} · {formatTime(c.start_time)} ·{" "}
                      {c.duration_minutes} min · {c.trainer_name} · {c.enrolled_count}/
                      {c.capacity}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="subtle" onClick={() => toggleRoster(c.id)}>
                      {roster.open === c.id ? "Hide roster" : "Roster"}
                    </Button>
                    <Button variant="secondary" onClick={() => startEdit(c)}>
                      Edit
                    </Button>
                    <Button variant="danger" onClick={() => onDelete(c)}>
                      Delete
                    </Button>
                  </div>
                </div>
                {roster.open === c.id && (
                  <div className="mt-3 pl-2 border-l-2 border-slate-200">
                    {roster.items.length === 0 ? (
                      <p className="text-sm text-slate-500">No one enrolled yet.</p>
                    ) : (
                      <ul className="text-sm">
                        {roster.items.map((m) => (
                          <li key={m.user_id} className="py-0.5">
                            {m.name}{" "}
                            <span className="text-slate-500">({m.email})</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
