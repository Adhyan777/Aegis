
import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Wallet,
  XCircle,
  BrainCircuit,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";

const CHART_COLORS = [
  "#818cf8",
  "#34d399",
  "#fbbf24",
  "#fb7185",
  "#38bdf8",
];

type Transaction = {
  id?: string;
  transaction_id?: string;
  transaction_reference?: string;
  customer_id?: string;
  amount?: number | string;
  currency?: string;
  transaction_type?: string;
  payment_method?: string;
  status?: string;
  city?: string;
  location?: string;
  transaction_time?: string;
  created_at?: string;
  timestamp?: string;
};

type Analytics = {
  total_transactions?: number | string;
  total_amount?: number | string;
  total_volume?: number | string;
  status_breakdown?: Record<string, number>;
  payment_method_breakdown?: Record<string, number>;
  transaction_type_breakdown?: Record<string, number>;
  [key: string]: unknown;
};

type Trend = {
  date: string;
  transaction_count: number;
  total_amount: number | string;
};

type FraudSummary = {
  total_analyzed?: number;
  suspicious_transactions?: number;
  risk_breakdown?: Record<string, number>;
  transactions_for_review?: unknown[];
};

type Explanation = {
  source: string;
  reason: string;
};

type Intelligence = {
  transaction_id: string;
  transaction_reference?: string;
  customer_id?: string;
  amount?: number;
  currency?: string;
  rule_based_score: number;
  anomaly_score: number | null;
  anomaly_available: boolean;
  combined_risk_score: number;
  risk_level: string;
  is_suspicious: boolean;
  explanations: Explanation[];
  anomaly_analysis?: {
    message?: string;
    training_transactions?: number;
    note?: string;
  };
  scoring_method?: string;
  score_is_probability?: boolean;
};

const asNumber = (value: unknown): number => {
  const result = Number(value ?? 0);
  return Number.isFinite(result) ? result : 0;
};

const currency = (value: unknown): string =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(asNumber(value));

const titleCase = (value: string): string =>
  value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());

const formatDate = (value?: string): string => {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
};

const unwrapTransactions = (data: unknown): Transaction[] => {
  if (Array.isArray(data)) return data as Transaction[];

  if (data && typeof data === "object") {
    const object = data as Record<string, unknown>;

    if (Array.isArray(object.transactions)) {
      return object.transactions as Transaction[];
    }

    if (Array.isArray(object.items)) return object.items as Transaction[];
    if (Array.isArray(object.data)) return object.data as Transaction[];
  }

  return [];
};

const unwrapTrends = (data: unknown): Trend[] => {
  if (Array.isArray(data)) return data as Trend[];

  if (data && typeof data === "object") {
    const object = data as Record<string, unknown>;

    if (Array.isArray(object.trends)) return object.trends as Trend[];

    if (Array.isArray(object.daily_trends)) {
      return object.daily_trends as Trend[];
    }

    if (Array.isArray(object.data)) return object.data as Trend[];
  }

  return [];
};

function MetricCard({
  label,
  value,
  description,
  icon,
  tone,
}: {
  label: string;
  value: string;
  description: string;
  icon: React.ReactNode;
  tone: string;
}) {
  return (
    <article className="metric-card">
      <div className={`metric-icon ${tone}`}>{icon}</div>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-description">{description}</div>
    </article>
  );
}

function StatusBadge({ status }: { status?: string }) {
  const value = (status ?? "unknown").toLowerCase();

  const tone =
    value === "completed" || value === "successful"
      ? "green"
      : value === "pending"
        ? "amber"
        : value === "failed" || value === "declined"
          ? "red"
          : "neutral";

  return (
    <span className={`status-badge ${tone}`}>
      {titleCase(status ?? "unknown")}
    </span>
  );
}

function ProgressRow({
  label,
  count,
  total,
  tone,
  icon,
}: {
  label: string;
  count: number;
  total: number;
  tone: string;
  icon: React.ReactNode;
}) {
  const percentage = total > 0 ? Math.min((count / total) * 100, 100) : 0;

  return (
    <div className="progress-row">
      <div className="progress-heading">
        <span className={`progress-label ${tone}`}>
          {icon}
          {label}
        </span>
        <strong>{count}</strong>
      </div>

      <div className="progress-track">
        <div
          className={`progress-fill ${tone}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function RiskCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div className={`risk-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>
        {tone === "red"
          ? "Priority review"
          : tone === "amber"
            ? "Needs attention"
            : tone === "green"
              ? "Lower rule score"
              : "Medium and high risk"}
      </small>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="detail-row">
      <span>{label}</span>
      <strong>
        {value === undefined || value === null || value === ""
          ? "—"
          : String(value)}
      </strong>
    </div>
  );
}

function RiskPill({ level }: { level: string }) {
  const normalized = level.toLowerCase();

  const colors =
    normalized === "high"
      ? {
          background: "rgba(251,113,133,0.14)",
          color: "#fda4af",
          border: "rgba(251,113,133,0.3)",
        }
      : normalized === "medium"
        ? {
            background: "rgba(251,191,36,0.12)",
            color: "#fcd34d",
            border: "rgba(251,191,36,0.3)",
          }
        : {
            background: "rgba(52,211,153,0.12)",
            color: "#6ee7b7",
            border: "rgba(52,211,153,0.3)",
          };

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        borderRadius: 999,
        border: `1px solid ${colors.border}`,
        background: colors.background,
        color: colors.color,
        padding: "5px 10px",
        fontSize: 11,
        fontWeight: 700,
        whiteSpace: "nowrap",
      }}
    >
      {titleCase(normalized)}
    </span>
  );
}

export default function App() {
  const [analytics, setAnalytics] = useState<Analytics>({});
  const [fraud, setFraud] = useState<FraudSummary>({});
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [intelligence, setIntelligence] = useState<Intelligence[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [selected, setSelected] = useState<Transaction | null>(null);
  const [expandedRiskId, setExpandedRiskId] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    const endpoints = [
      { key: "analytics", url: `${API}/api/analytics/summary` },
      { key: "fraud", url: `${API}/api/fraud/summary` },
      {
        key: "transactions",
        url: `${API}/api/transactions?skip=0&limit=100`,
      },
      { key: "trends", url: `${API}/api/analytics/daily-trends` },
      {
        key: "paymentMethods",
        url: `${API}/api/analytics/payment-methods`,
      },
      {
        key: "intelligence",
        url: `${API}/api/fraud/intelligence-all`,
      },
    ];

    const results = await Promise.allSettled(
      endpoints.map(async (endpoint) => {
        const response = await fetch(endpoint.url);

        if (!response.ok) {
          throw new Error(`${endpoint.key}: HTTP ${response.status}`);
        }

        return {
          key: endpoint.key,
          data: await response.json(),
        };
      }),
    );

    const received: Record<string, unknown> = {};
    const failures: string[] = [];

    results.forEach((result, index) => {
      if (result.status === "fulfilled") {
        received[result.value.key] = result.value.data;
      } else {
        failures.push(endpoints[index].key);
      }
    });

    if (received.analytics) {
      const summary = received.analytics as Analytics;

      setAnalytics({
        ...summary,
        payment_method_breakdown:
          summary.payment_method_breakdown ??
          (received.paymentMethods as Record<string, number> | undefined) ??
          {},
      });
    } else {
      failures.push("analytics summary");
    }

    if (received.fraud) {
      setFraud(received.fraud as FraudSummary);
    }

    if (received.transactions !== undefined) {
      setTransactions(unwrapTransactions(received.transactions));
    }

    if (received.trends !== undefined) {
      setTrends(unwrapTrends(received.trends));
    }

    if (received.intelligence !== undefined) {
      setIntelligence(
        Array.isArray(received.intelligence)
          ? (received.intelligence as Intelligence[])
          : [],
      );
    }

    if (failures.length > 0) {
      setError(
        `Could not load: ${[...new Set(failures)].join(", ")}.`,
      );
    }

    setUpdatedAt(new Date().toLocaleTimeString("en-IN"));
    setLoading(false);
  }, []);

  useEffect(() => {
  const timer = window.setTimeout(() => {
    void loadDashboard();
  }, 0);

  return () => window.clearTimeout(timer);
}, [loadDashboard]);

  const statusBreakdown = analytics.status_breakdown ?? {};
  const paymentBreakdown = analytics.payment_method_breakdown ?? {};

  const totalTransactions = asNumber(analytics.total_transactions);

  const totalVolume = asNumber(
    analytics.total_volume ??
      analytics.total_amount ??
      analytics.total_transaction_volume,
  );

  const completed = asNumber(
    statusBreakdown.completed ?? statusBreakdown.successful,
  );

  const pending = asNumber(statusBreakdown.pending);

  const failed =
    asNumber(statusBreakdown.failed) + asNumber(statusBreakdown.declined);

  const risk = fraud.risk_breakdown ?? {};

  const reviewCount = Array.isArray(fraud.transactions_for_review)
    ? fraud.transactions_for_review.length
    : 0;

  const filtered = transactions.filter((transaction) => {
    const text = [
      transaction.transaction_reference,
      transaction.transaction_id,
      transaction.id,
      transaction.customer_id,
      transaction.payment_method,
      transaction.transaction_type,
      transaction.status,
      transaction.city,
      transaction.location,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    const matchesSearch = text.includes(search.toLowerCase());

    const matchesStatus =
      statusFilter === "all" ||
      transaction.status?.toLowerCase() === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const paymentData = Object.entries(paymentBreakdown).map(
    ([name, value]) => ({
      name: titleCase(name),
      value: asNumber(value),
    }),
  );

  const rankedInvestigations = [...intelligence]
    .filter((item) => {
      if (riskFilter === "all") return true;
      if (riskFilter === "suspicious") return item.is_suspicious;

      return item.risk_level.toLowerCase() === riskFilter;
    })
    .sort(
      (a, b) =>
        asNumber(b.combined_risk_score) -
        asNumber(a.combined_risk_score),
    );

  const highRiskCount = intelligence.filter(
    (item) => item.risk_level.toLowerCase() === "high",
  ).length;

  const mediumRiskCount = intelligence.filter(
    (item) => item.risk_level.toLowerCase() === "medium",
  ).length;

  const anomalyAvailableCount = intelligence.filter(
    (item) => item.anomaly_available && item.anomaly_score !== null,
  ).length;

  const suspiciousCount = intelligence.filter(
    (item) => item.is_suspicious,
  ).length;

  return (
    <div className="aegis">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={25} />
          </div>

          <div>
            <div className="brand-name">AEGIS</div>
            <div className="brand-subtitle">TRANSACTION INTELLIGENCE</div>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <a className="nav-link active" href="#overview">
          <Activity size={18} /> Overview
        </a>

        <a className="nav-link" href="#transactions">
          <Wallet size={18} /> Transactions
        </a>

        <a className="nav-link" href="#fraud">
          <ShieldAlert size={18} /> Fraud monitoring
        </a>

        <a className="nav-link" href="#investigations">
          <BrainCircuit size={18} /> Investigations
        </a>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <span className="online-dot" />
            <div>
              <strong>API connection</strong>
              <small>Local environment</small>
            </div>
          </div>

          <div className="sidebar-footer">AEGIS • RISK OPERATIONS</div>
        </div>
      </aside>

      <main className="main" id="overview">
        <header className="topbar">
          <div>
            <div className="eyebrow">RISK &amp; OPERATIONS</div>
            <h1>Overview</h1>
            <p className="subtitle">
              Transaction intelligence and fraud monitoring at a glance.
            </p>
          </div>

          <div className="topbar-actions">
            <span className="live-label">
              <span className="online-dot" /> LIVE DATA
            </span>

            <button
              className="refresh-button"
              onClick={() => void loadDashboard()}
              disabled={loading}
            >
              <RefreshCw
                size={16}
                className={loading ? "spin" : ""}
              />
              Refresh
            </button>
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />

            <div>
              <strong>Some data could not be loaded</strong>
              <p>{error}</p>
              <small>
                Check the FastAPI backend and the endpoint responses.
              </small>
            </div>
          </div>
        )}

        <section className="metrics-grid">
          <MetricCard
            label="Total transactions"
            value={totalTransactions.toLocaleString("en-IN")}
            description="Transactions recorded"
            icon={<Activity size={20} />}
            tone="blue"
          />

          <MetricCard
            label="Transaction volume"
            value={currency(totalVolume)}
            description="Total recorded value"
            icon={<Wallet size={20} />}
            tone="purple"
          />

          <MetricCard
            label="Completed"
            value={completed.toLocaleString("en-IN")}
            description="Successfully completed"
            icon={<CheckCircle2 size={20} />}
            tone="green"
          />

          <MetricCard
            label="Flagged transactions"
            value={asNumber(fraud.suspicious_transactions).toLocaleString(
              "en-IN",
            )}
            description="High-risk rule matches"
            icon={<ShieldAlert size={20} />}
            tone="red"
          />
        </section>

        <section className="charts-grid">
          <article className="panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">TRANSACTION ACTIVITY</div>
                <h2>Daily transaction trends</h2>
              </div>

              <span className="panel-tag">DAILY</span>
            </div>

            <div className="chart">
              {trends.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trends}>
                    <defs>
                      <linearGradient
                        id="trendFill"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="#818cf8"
                          stopOpacity={0.35}
                        />
                        <stop
                          offset="95%"
                          stopColor="#818cf8"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>

                    <CartesianGrid
                      stroke="#263247"
                      strokeDasharray="4 4"
                      vertical={false}
                    />

                    <XAxis
                      dataKey="date"
                      stroke="#8493aa"
                      tickLine={false}
                      axisLine={false}
                      tick={{ fontSize: 11 }}
                    />

                    <YAxis
                      stroke="#8493aa"
                      tickLine={false}
                      axisLine={false}
                      allowDecimals={false}
                      tick={{ fontSize: 11 }}
                    />

                    <Tooltip
                      contentStyle={{
                        background: "#111a29",
                        border: "1px solid #344158",
                        borderRadius: 10,
                        color: "#edf2fb",
                      }}
                    />

                    <Area
                      type="monotone"
                      dataKey="transaction_count"
                      name="Transactions"
                      stroke="#818cf8"
                      strokeWidth={3}
                      fill="url(#trendFill)"
                      activeDot={{ r: 5 }}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="chart-empty">
                  <Activity size={28} />
                  <strong>
                    {loading
                      ? "Loading trends..."
                      : "No trend data available"}
                  </strong>
                  <span>
                    {loading
                      ? "Fetching daily activity from the API."
                      : "Check the daily-trends endpoint if this section remains empty."}
                  </span>
                </div>
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">PAYMENT ANALYTICS</div>
                <h2>Payment methods</h2>
              </div>
            </div>

            {paymentData.length > 0 ? (
              <>
                <div className="donut-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={paymentData}
                        dataKey="value"
                        nameKey="name"
                        innerRadius="58%"
                        outerRadius="82%"
                        paddingAngle={4}
                        stroke="none"
                      >
                        {paymentData.map((entry, index) => (
                          <Cell
                            key={entry.name}
                            fill={
                              CHART_COLORS[index % CHART_COLORS.length]
                            }
                          />
                        ))}
                      </Pie>

                      <Tooltip
                        contentStyle={{
                          background: "#111a29",
                          border: "1px solid #344158",
                          borderRadius: 10,
                          color: "#edf2fb",
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="legend">
                  {paymentData.map((entry, index) => (
                    <div className="legend-item" key={entry.name}>
                      <span
                        className="legend-dot"
                        style={{
                          background:
                            CHART_COLORS[index % CHART_COLORS.length],
                        }}
                      />

                      <span>{entry.name}</span>
                      <strong>{entry.value}</strong>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="chart-empty compact">
                <Wallet size={25} />
                <strong>
                  {loading
                    ? "Loading payment data..."
                    : "No payment data available"}
                </strong>
                <span>
                  Payment-method counts appear here when returned by the API.
                </span>
              </div>
            )}
          </article>
        </section>

        <section className="panel status-panel">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">PROCESSING HEALTH</div>
              <h2>Transaction status</h2>
            </div>

            <span className="panel-tag">
              {totalTransactions} TOTAL
            </span>
          </div>

          <div className="status-grid">
            <ProgressRow
              label="Completed"
              count={completed}
              total={totalTransactions}
              tone="green"
              icon={<CheckCircle2 size={17} />}
            />

            <ProgressRow
              label="Pending"
              count={pending}
              total={totalTransactions}
              tone="amber"
              icon={<Clock3 size={17} />}
            />

            <ProgressRow
              label="Failed / declined"
              count={failed}
              total={totalTransactions}
              tone="red"
              icon={<XCircle size={17} />}
            />
          </div>
        </section>

        <section className="panel table-panel" id="transactions">
          <div className="panel-heading table-title">
            <div>
              <div className="eyebrow">LEDGER EXPLORER</div>
              <h2>Recent transactions</h2>
              <p className="subtitle">
                Search and inspect your transaction records.
              </p>
            </div>

            <span className="panel-tag">
              {filtered.length} RECORDS
            </span>
          </div>

          <div className="table-controls">
            <div className="search-box">
              <Search size={17} />

              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search transaction or customer..."
                aria-label="Search transactions"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
              aria-label="Filter transaction status"
            >
              <option value="all">All statuses</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="declined">Declined</option>
            </select>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>TRANSACTION</th>
                  <th>CUSTOMER</th>
                  <th>TYPE / METHOD</th>
                  <th>AMOUNT</th>
                  <th>STATUS</th>
                  <th>DATE</th>
                </tr>
              </thead>

              <tbody>
                {filtered.map((transaction, index) => (
                  <tr
                    key={
                      transaction.id ??
                      transaction.transaction_id ??
                      transaction.transaction_reference ??
                      index
                    }
                    onClick={() => setSelected(transaction)}
                    className="transaction-row"
                  >
                    <td>
                      <strong className="mono">
                        {transaction.transaction_reference ??
                          transaction.transaction_id ??
                          transaction.id ??
                          "—"}
                      </strong>

                      <small>
                        {transaction.city ?? transaction.location ?? "—"}
                      </small>
                    </td>

                    <td>{transaction.customer_id ?? "—"}</td>

                    <td>
                      {titleCase(transaction.transaction_type ?? "unknown")}
                      <small>
                        {titleCase(transaction.payment_method ?? "unknown")}
                      </small>
                    </td>

                    <td className="amount">
                      {currency(transaction.amount)}
                    </td>

                    <td>
                      <StatusBadge status={transaction.status} />
                    </td>

                    <td>
                      {formatDate(
                        transaction.transaction_time ??
                          transaction.created_at ??
                          transaction.timestamp,
                      )}
                    </td>
                  </tr>
                ))}

                {!loading && filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="empty-table">
                      No matching transactions found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel fraud-panel" id="fraud">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">RULE-BASED MONITORING</div>
              <h2>Fraud risk overview</h2>
              <p className="subtitle">
                Risk indicators generated by the current detection rules.
              </p>
            </div>

            <ShieldAlert size={23} />
          </div>

          <div className="risk-grid">
            <RiskCard
              label="High risk"
              value={asNumber(risk.high)}
              tone="red"
            />

            <RiskCard
              label="Medium risk"
              value={asNumber(risk.medium)}
              tone="amber"
            />

            <RiskCard
              label="Low risk"
              value={asNumber(risk.low)}
              tone="green"
            />

            <RiskCard
              label="For review"
              value={reviewCount}
              tone="purple"
            />
          </div>

          <div className="fraud-note">
            <AlertTriangle size={17} />
            Rule-based flags are indicators for investigation, not proof of
            fraud. An unflagged transaction is not guaranteed to be legitimate.
          </div>
        </section>

        <section className="panel" id="investigations">
          <div className="panel-heading">
            <div>
              <div className="eyebrow">UNIFIED RISK INTELLIGENCE</div>
              <h2>Investigation queue</h2>
              <p className="subtitle">
                Ranked transaction assessments with explainable risk signals.
              </p>
            </div>

            <BrainCircuit size={23} />
          </div>

          <div
            className="investigation-stats"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(145px, 1fr))",
              gap: 12,
              margin: "20px 0",
            }}
          >
            {[
              {
                label: "Assessments",
                value: intelligence.length,
                color: "#edf2fb",
              },
              {
                label: "Flagged for review",
                value: suspiciousCount,
                color: "#fb7185",
              },
              {
                label: "High risk",
                value: highRiskCount,
                color: "#fb7185",
              },
              {
                label: "Medium risk",
                value: mediumRiskCount,
                color: "#fbbf24",
              },
              {
                label: "Anomaly scores available",
                value: anomalyAvailableCount,
                color: "#34d399",
              },
            ].map((metric) => (
              <div
                key={metric.label}
                style={{
                  padding: 15,
                  background: "rgba(255,255,255,0.025)",
                  border: "1px solid #263247",
                  borderRadius: 12,
                }}
              >
                <div
                  style={{
                    color: "#8493aa",
                    fontSize: 12,
                    marginBottom: 9,
                  }}
                >
                  {metric.label}
                </div>

                <strong
                  style={{
                    color: metric.color,
                    fontSize: 24,
                  }}
                >
                  {metric.value}
                </strong>
              </div>
            ))}
          </div>

          <div
            className="table-controls"
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: 12,
              flexWrap: "wrap",
              marginBottom: 16,
            }}
          >
            <select
              value={riskFilter}
              onChange={(event) => setRiskFilter(event.target.value)}
              aria-label="Filter investigation risk"
            >
              <option value="all">All assessments</option>
              <option value="suspicious">Flagged for review</option>
              <option value="high">High risk</option>
              <option value="medium">Medium risk</option>
              <option value="low">Low risk</option>
            </select>

            <span className="panel-tag">
              {rankedInvestigations.length} RESULTS
            </span>
          </div>

          {rankedInvestigations.length > 0 ? (
            <div style={{ display: "grid", gap: 12 }}>
              {rankedInvestigations.map((item) => {
                const id = item.transaction_id;
                const expanded = expandedRiskId === id;

                return (
                  <article
                    key={id}
                    style={{
                      padding: 16,
                      border: "1px solid #263247",
                      borderRadius: 12,
                      background: "rgba(255,255,255,0.02)",
                    }}
                  >
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedRiskId(expanded ? null : id)
                      }
                      aria-expanded={expanded}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        flexWrap: "wrap",
                        gap: 16,
                        width: "100%",
                        padding: 0,
                        color: "#edf2fb",
                        textAlign: "left",
                        background: "transparent",
                        border: 0,
                        cursor: "pointer",
                      }}
                    >
                      <div
                        style={{
                          display: "grid",
                          gap: 7,
                          minWidth: 0,
                        }}
                      >
                        <strong className="mono">
                          {item.transaction_reference ?? id}
                        </strong>

                        <span
                          style={{
                            color: "#8493aa",
                            fontSize: 12,
                          }}
                        >
                          Customer: {item.customer_id ?? "—"}
                        </span>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          flexWrap: "wrap",
                        }}
                      >
                        <RiskPill level={item.risk_level} />

                        <strong
                          style={{
                            fontSize: 18,
                            fontVariantNumeric: "tabular-nums",
                          }}
                        >
                          {Math.round(
                            asNumber(item.combined_risk_score),
                          )}
                          <span
                            style={{
                              color: "#8493aa",
                              fontSize: 12,
                            }}
                          >
                            /100
                          </span>
                        </strong>

                        {expanded ? (
                          <ChevronUp size={18} />
                        ) : (
                          <ChevronDown size={18} />
                        )}
                      </div>
                    </button>

                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "10px 22px",
                        marginTop: 14,
                        color: "#9aa8bd",
                        fontSize: 12,
                      }}
                    >
                      <span>Amount: {currency(item.amount)}</span>

                      <span>
                        Rule score: {asNumber(item.rule_based_score)}/100
                      </span>

                      <span>
                        Anomaly score:{" "}
                        {item.anomaly_score === null ||
                        item.anomaly_score === undefined
                          ? "Unavailable"
                          : `${item.anomaly_score}/100`}
                      </span>

                      <span>
                        {item.is_suspicious
                          ? "Flagged for review"
                          : "Not flagged by combined threshold"}
                      </span>
                    </div>

                    {expanded && (
                      <div
                        style={{
                          marginTop: 18,
                          paddingTop: 16,
                          borderTop: "1px solid #263247",
                        }}
                      >
                        <h3
                          style={{
                            margin: "0 0 12px",
                            fontSize: 14,
                          }}
                        >
                          Risk explanations
                        </h3>

                        {item.explanations?.length ? (
                          <ul
                            style={{
                              display: "grid",
                              gap: 12,
                              paddingLeft: 20,
                              color: "#cbd5e1",
                              fontSize: 13,
                              lineHeight: 1.6,
                            }}
                          >
                            {item.explanations.map((explanation, index) => (
                              <li key={`${id}-${index}`}>
                                <span
                                  style={{
                                    display: "inline-block",
                                    marginRight: 8,
                                    color: "#a5b4fc",
                                    fontSize: 11,
                                    fontWeight: 700,
                                  }}
                                >
                                  {titleCase(explanation.source)}
                                </span>

                                {explanation.reason}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p style={{ color: "#9aa8bd", fontSize: 13 }}>
                            No configured risk signals were returned.
                          </p>
                        )}

                        {!item.anomaly_available && (
                          <div
                            style={{
                              marginTop: 14,
                              padding: 12,
                              border: "1px solid rgba(251,191,36,0.2)",
                              borderRadius: 8,
                              background: "rgba(251,191,36,0.06)",
                              color: "#fcd34d",
                              fontSize: 12,
                              lineHeight: 1.6,
                            }}
                          >
                            Statistical anomaly scoring is unavailable,
                            typically because there is insufficient transaction
                            history. The combined score falls back to the
                            rule-based score.
                            {item.anomaly_analysis?.message
                              ? ` ${item.anomaly_analysis.message}`
                              : ""}
                          </div>
                        )}

                        <p
                          style={{
                            marginTop: 14,
                            color: "#8493aa",
                            fontSize: 12,
                            lineHeight: 1.6,
                          }}
                        >
                          This is a heuristic risk score, not a probability
                          of fraud. The statistical detector is not a trained
                          machine-learning model. Flagged transactions require
                          appropriate investigation.
                        </p>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <div className="chart-empty compact">
              <ShieldCheck size={25} />

              <strong>
                {loading
                  ? "Loading investigation assessments..."
                  : intelligence.length === 0
                    ? "No investigation assessments available"
                    : "No matching assessments"}
              </strong>

              <span>
                {intelligence.length === 0
                  ? "The unified fraud intelligence endpoint must return assessment results."
                  : "Try a different risk filter."}
              </span>
            </div>
          )}
        </section>

        <footer className="footer">
          <span>AEGIS • TRANSACTION INTELLIGENCE</span>
          <span>
            {updatedAt ? `Last refreshed ${updatedAt}` : "Not refreshed yet"}
          </span>
        </footer>
      </main>

      {selected && (
        <div
          className="modal-backdrop"
          onClick={() => setSelected(null)}
        >
          <section
            className="detail-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="detail-title"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="modal-heading">
              <div>
                <div className="eyebrow">LEDGER RECORD</div>
                <h2 id="detail-title">Transaction details</h2>
              </div>

              <button
                className="close-button"
                onClick={() => setSelected(null)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <Detail
              label="Reference"
              value={
                selected.transaction_reference ??
                selected.transaction_id ??
                selected.id
              }
            />

            <Detail label="Customer" value={selected.customer_id} />
            <Detail label="Amount" value={currency(selected.amount)} />

            <Detail
              label="Type"
              value={titleCase(selected.transaction_type ?? "unknown")}
            />

            <Detail
              label="Payment method"
              value={titleCase(selected.payment_method ?? "unknown")}
            />

            <Detail
              label="Status"
              value={titleCase(selected.status ?? "unknown")}
            />

            <Detail
              label="Location"
              value={selected.city ?? selected.location}
            />

            <Detail
              label="Date"
              value={formatDate(
                selected.transaction_time ??
                  selected.created_at ??
                  selected.timestamp,
              )}
            />
          </section>
        </div>
      )}
    </div>
  );
}
