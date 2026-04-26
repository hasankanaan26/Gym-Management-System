export function Card({ title, children, actions }) {
  return (
    <section className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 mb-6">
      {(title || actions) && (
        <div className="flex items-center justify-between mb-3">
          {title && <h2 className="text-lg font-semibold">{title}</h2>}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function Button({ children, className = "", variant = "primary", ...rest }) {
  const base =
    "inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed";
  const styles = {
    primary: "bg-slate-900 text-white hover:bg-slate-800",
    secondary: "bg-slate-100 text-slate-800 hover:bg-slate-200",
    danger: "bg-red-600 text-white hover:bg-red-700",
    subtle: "bg-transparent text-slate-600 hover:bg-slate-100",
  };
  return (
    <button className={`${base} ${styles[variant]} ${className}`} {...rest}>
      {children}
    </button>
  );
}

export function Input(props) {
  return (
    <input
      {...props}
      className={`w-full px-3 py-2 rounded-md border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-500 ${props.className || ""}`}
    />
  );
}

export function Select(props) {
  return (
    <select
      {...props}
      className={`w-full px-3 py-2 rounded-md border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-slate-500 ${props.className || ""}`}
    >
      {props.children}
    </select>
  );
}

export function Label({ children }) {
  return <label className="block text-sm font-medium text-slate-700 mb-1">{children}</label>;
}

export function Badge({ children, color = "slate" }) {
  const colors = {
    slate: "bg-slate-100 text-slate-700",
    green: "bg-green-100 text-green-800",
    red: "bg-red-100 text-red-800",
    amber: "bg-amber-100 text-amber-800",
    blue: "bg-blue-100 text-blue-800",
  };
  return (
    <span className={`inline-block px-2 py-0.5 text-xs rounded-full font-medium ${colors[color]}`}>
      {children}
    </span>
  );
}

export function ErrorBanner({ error }) {
  if (!error) return null;
  return (
    <div className="mb-3 p-3 rounded-md bg-red-50 border border-red-200 text-red-800 text-sm">
      {error}
    </div>
  );
}

export function formatTime(t) {
  if (!t) return "";
  // t is "HH:MM:SS"
  const [h, m] = t.split(":");
  const hour = parseInt(h, 10);
  const suffix = hour >= 12 ? "pm" : "am";
  const hour12 = ((hour + 11) % 12) + 1;
  return `${hour12}:${m}${suffix}`;
}

export function titleCase(s) {
  if (!s) return "";
  return s.charAt(0).toUpperCase() + s.slice(1);
}
