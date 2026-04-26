import { useEffect, useState } from "react";
import { api } from "../api.js";
import {
  Badge,
  Button,
  Card,
  ErrorBanner,
  Input,
  Label,
  Select,
  titleCase,
} from "../components/ui.jsx";

function statusBadge(m) {
  if (!m.subscription_status) return <Badge color="red">No subscription</Badge>;
  const expired =
    m.subscription_expires_at &&
    new Date(m.subscription_expires_at) <= new Date();
  if (m.subscription_status === "active" && !expired) {
    return <Badge color="green">Active</Badge>;
  }
  return <Badge color="red">Expired</Badge>;
}

export default function ManageMembers() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [q, setQ] = useState("");
  const [qInput, setQInput] = useState("");

  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 10 });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listMembers({ page, pageSize, q });
      setData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize, q]);

  function applySearch(e) {
    e.preventDefault();
    setPage(1);
    setQ(qInput.trim());
  }

  function clearSearch() {
    setQInput("");
    setQ("");
    setPage(1);
  }

  async function onCreate(e) {
    e.preventDefault();
    setError(null);
    try {
      await api.addMember(form);
      setForm({ name: "", email: "", password: "" });
      setPage(1);
      await load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function onRemove(id, name) {
    if (!confirm(`Remove ${name}?`)) return;
    try {
      await api.removeMember(id);
      // If we removed the last item on a page, step back a page.
      if (data.items.length === 1 && page > 1) {
        setPage(page - 1);
      } else {
        await load();
      }
    } catch (err) {
      setError(err.message);
    }
  }

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));
  const fromIdx = data.total === 0 ? 0 : (page - 1) * pageSize + 1;
  const toIdx = Math.min(page * pageSize, data.total);

  return (
    <div>
      <ErrorBanner error={error} />

      <Card title="Add a member">
        <form
          onSubmit={onCreate}
          className="grid grid-cols-1 sm:grid-cols-4 gap-3 items-end"
        >
          <div>
            <Label>Name</Label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div>
            <Label>Email</Label>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div>
            <Label>Temp. password</Label>
            <Input
              type="text"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              minLength={6}
              required
            />
          </div>
          <Button type="submit">Add member</Button>
        </form>
      </Card>

      <Card
        title={`Members (${data.total})`}
        actions={
          <form onSubmit={applySearch} className="flex items-center gap-2">
            <Input
              placeholder="Search name or email…"
              value={qInput}
              onChange={(e) => setQInput(e.target.value)}
              className="w-64"
            />
            <Button type="submit" variant="secondary">
              Search
            </Button>
            {q && (
              <Button type="button" variant="subtle" onClick={clearSearch}>
                Clear
              </Button>
            )}
          </form>
        }
      >
        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : data.items.length === 0 ? (
          <p className="text-sm text-slate-600">
            {q ? `No members match "${q}".` : "No members yet."}
          </p>
        ) : (
          <>
            <table className="w-full text-sm">
              <thead className="text-left text-slate-500">
                <tr>
                  <th className="py-2">Name</th>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Plan</th>
                  <th>Expires</th>
                  <th></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {data.items.map((m) => (
                  <tr key={m.id}>
                    <td className="py-2 font-medium">{m.name}</td>
                    <td>{m.email}</td>
                    <td>{statusBadge(m)}</td>
                    <td>
                      {m.subscription_plan ? titleCase(m.subscription_plan) : "—"}
                    </td>
                    <td>
                      {m.subscription_expires_at
                        ? new Date(m.subscription_expires_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="text-right">
                      <Button
                        variant="danger"
                        onClick={() => onRemove(m.id, m.name)}
                      >
                        Remove
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mt-4">
              <div className="text-sm text-slate-600">
                Showing {fromIdx}–{toIdx} of {data.total}
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32">
                  <Select
                    value={pageSize}
                    onChange={(e) => {
                      setPage(1);
                      setPageSize(Number(e.target.value));
                    }}
                  >
                    <option value={10}>10 / page</option>
                    <option value={20}>20 / page</option>
                    <option value={50}>50 / page</option>
                  </Select>
                </div>
                <Button
                  variant="secondary"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Prev
                </Button>
                <span className="text-sm text-slate-600">
                  Page {page} / {totalPages}
                </span>
                <Button
                  variant="secondary"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
