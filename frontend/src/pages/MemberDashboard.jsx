// MemberDashboard — landing page for logged-in members.
//
// Two responsibilities:
//   1. Show subscription status + a "Subscribe" form when not active.
//   2. Show the user's upcoming classes with a Cancel button each.
//
// Both data fetches are kicked off in parallel via Promise.all on mount.
// In a bigger app you'd extract this fetch + cache logic into TanStack
// Query (see CONTRIBUTING.md → "Frontend Improvements").

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import {
  Badge,
  Button,
  Card,
  ErrorBanner,
  Select,
  formatTime,
  titleCase,
} from "../components/ui.jsx";

function subStatusColor(sub) {
  if (!sub) return "red";
  const expired = new Date(sub.expires_at) <= new Date();
  if (sub.status === "active" && !expired) return "green";
  return "red";
}

function subStatusLabel(sub) {
  if (!sub) return "None";
  const expired = new Date(sub.expires_at) <= new Date();
  if (sub.status === "active" && !expired) return "Active";
  return "Expired";
}

export default function MemberDashboard() {
  const [subscription, setSubscription] = useState(null);
  const [enrollments, setEnrollments] = useState([]);
  const [plan, setPlan] = useState("monthly");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setError(null);
    try {
      const [sub, mine] = await Promise.all([
        api.mySubscription(),
        api.myEnrollments(),
      ]);
      setSubscription(sub);
      setEnrollments(mine);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onSubscribe() {
    setError(null);
    try {
      await api.subscribe(plan);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onCancel(id) {
    setError(null);
    try {
      await api.cancelEnrollment(id);
      setEnrollments(enrollments.filter((e) => e.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  if (loading) return <div>Loading…</div>;

  const isActive =
    subscription &&
    subscription.status === "active" &&
    new Date(subscription.expires_at) > new Date();

  return (
    <div>
      <ErrorBanner error={error} />

      <Card title="Subscription">
        <div className="flex items-center gap-3 mb-3">
          <Badge color={subStatusColor(subscription)}>
            {subStatusLabel(subscription)}
          </Badge>
          {subscription && (
            <span className="text-sm text-slate-600">
              Plan: {titleCase(subscription.plan)} · Expires{" "}
              {new Date(subscription.expires_at).toLocaleDateString()}
            </span>
          )}
        </div>
        {!isActive && (
          <div className="flex items-end gap-3">
            <div className="w-48">
              <Select value={plan} onChange={(e) => setPlan(e.target.value)}>
                <option value="monthly">Monthly — 30 days</option>
                <option value="quarterly">Quarterly — 90 days</option>
                <option value="yearly">Yearly — 365 days</option>
              </Select>
            </div>
            <Button onClick={onSubscribe}>Subscribe</Button>
          </div>
        )}
      </Card>

      <Card
        title="My upcoming classes"
        actions={
          <Link to="/member/classes">
            <Button variant="secondary">Browse classes</Button>
          </Link>
        }
      >
        {enrollments.length === 0 ? (
          <p className="text-sm text-slate-600">
            You're not enrolled in any classes yet.
          </p>
        ) : (
          <ul className="divide-y divide-slate-200">
            {enrollments.map((e) => (
              <li key={e.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="font-medium">{e.gym_class.name}</div>
                  <div className="text-sm text-slate-600">
                    {titleCase(e.gym_class.day_of_week)} ·{" "}
                    {formatTime(e.gym_class.start_time)} ·{" "}
                    {e.gym_class.trainer_name}
                  </div>
                </div>
                <Button variant="danger" onClick={() => onCancel(e.id)}>
                  Cancel
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
