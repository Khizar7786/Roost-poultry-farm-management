import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bird,
  Skull,
  Bell,
  Camera,
  TrendingUp,
  Wheat,
  Syringe,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import StatCard from "../components/StatCard";
import Badge from "../components/Badge";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { getDashboard } from "../api/dashboard";
import { formatDateTime, formatDate } from "../lib/utils";

const SEVERITY_TONE = { HIGH: "rust", MEDIUM: "gold", LOW: "ink" };

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(() => setError("Couldn't load your dashboard right now."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner full label="Loading your dashboard…" />;
  if (error) return <Card className="text-rust text-sm">{error}</Card>;

  const { flock_overview: flock, alerts, feed_stock_warnings, upcoming_vaccinations, market_price_forecast } = data;
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <div>
      <PageHeader
        eyebrow={data.farm_name}
        title={`${greeting}, ${user?.first_name || "there"}`}
        description={
          user?.role === "OWNER"
            ? "Here's how your farm is doing today."
            : "Here's what needs your attention today."
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={Bird} tone="ink" label="Active batches" value={flock.active_batch_count} />
        <StatCard icon={Bird} tone="ink" label="Total birds" value={flock.total_birds.toLocaleString()} />
        <StatCard icon={Skull} tone="rust" label="Mortality (7 days)" value={flock.mortality_last_7_days} />
        <StatCard icon={Bell} tone="gold" label="Unacknowledged alerts" value={alerts.length} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2" padded={false}>
          <div className="flex items-center justify-between px-6 pt-6 pb-4">
            <h3 className="font-display text-lg font-semibold text-ink-darker">Recent alerts</h3>
            <Link to="/alerts" className="text-sm font-semibold text-ink flex items-center gap-1 hover:gap-1.5 transition-all">
              View all <ArrowRight size={14} />
            </Link>
          </div>
          {alerts.length === 0 ? (
            <EmptyState
              icon={CheckCircle2}
              title="All clear"
              description="No unacknowledged alerts right now — nothing needs your attention."
            />
          ) : (
            <ul className="divide-y divide-ink-light">
              {alerts.slice(0, 6).map((a) => (
                <li key={a.id} className="px-6 py-3.5 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm text-ink-darker font-medium">{a.message}</p>
                    <p className="text-xs text-slate/50 mt-0.5">
                      {a.batch_number ? `Batch ${a.batch_number} · ` : ""}
                      {formatDateTime(a.created_at)}
                    </p>
                  </div>
                  <Badge tone={SEVERITY_TONE[a.severity]}>{a.severity}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <div className="space-y-6">
          <Card>
            <div className="flex items-center gap-2.5 mb-3.5">
              <Wheat size={16} className="text-gold-dark" />
              <h3 className="font-display text-base font-semibold text-ink-darker">Feed stock</h3>
            </div>
            {typeof feed_stock_warnings === "string" ? (
              <p className="text-sm text-slate/50">{feed_stock_warnings}</p>
            ) : (
              <ul className="space-y-2">
                {feed_stock_warnings.map((f, i) => (
                  <li key={i} className="flex items-center justify-between text-sm">
                    <span className="text-ink-darker">{f.feed_type}</span>
                    <Badge tone="rust">{f.quantity_kg}kg left</Badge>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card>
            <div className="flex items-center gap-2.5 mb-3.5">
              <Syringe size={16} className="text-gold-dark" />
              <h3 className="font-display text-base font-semibold text-ink-darker">
                Upcoming vaccinations
              </h3>
            </div>
            {typeof upcoming_vaccinations === "string" ? (
              <p className="text-sm text-slate/50">{upcoming_vaccinations}</p>
            ) : (
              <ul className="space-y-2.5">
                {upcoming_vaccinations.map((v, i) => (
                  <li key={i} className="text-sm">
                    <span className="text-ink-darker font-medium">{v.vaccine}</span>
                    <span className="text-slate/50"> — batch {v.batch}, {formatDate(v.scheduled_date)}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>
      </div>

      {user?.role === "OWNER" && (
        <Card className="mt-6">
          <div className="flex items-center justify-between mb-3.5">
            <div className="flex items-center gap-2.5">
              <TrendingUp size={16} className="text-ink" />
              <h3 className="font-display text-base font-semibold text-ink-darker">
                Market price forecast
              </h3>
            </div>
            <Link to="/price-prediction" className="text-sm font-semibold text-ink flex items-center gap-1 hover:gap-1.5 transition-all">
              Full forecast <ArrowRight size={14} />
            </Link>
          </div>
          {typeof market_price_forecast === "string" ? (
            <EmptyState
              icon={TrendingUp}
              title="No forecast yet"
              description="Record at least 5 sales, then generate your first price forecast."
              action={
                <Link to="/price-prediction" className="text-sm font-semibold text-ink hover:underline">
                  Go to Price Forecast →
                </Link>
              }
            />
          ) : (
            <div className="flex gap-3 overflow-x-auto pb-1">
              {market_price_forecast.forecast.slice(0, 6).map((f, i) => (
                <div key={i} className="shrink-0 bg-ink-light rounded-xl px-4 py-3 text-center min-w-[6.5rem]">
                  <div className="text-xs text-slate/50 mb-1">{formatDate(f.date)}</div>
                  <div className="font-display text-lg font-semibold text-ink-darker">
                    {f.price_pkr}
                  </div>
                  <div className={"text-xs font-semibold mt-0.5 " + (f.direction === "UP" ? "text-mint" : f.direction === "DOWN" ? "text-rust" : "text-slate/40")}>
                    {f.direction}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      <Card className="mt-6 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <span className="h-11 w-11 rounded-full bg-gold-light flex items-center justify-center">
            <Camera size={19} className="text-gold-dark" />
          </span>
          <div>
            <div className="font-semibold text-ink-darker text-sm">Ready to count today's flock?</div>
            <div className="text-xs text-slate/50">Snap a photo and get a live count in seconds.</div>
          </div>
        </div>
        <Link
          to="/chick-counting"
          className="text-sm font-semibold text-white bg-ink hover:bg-ink-dark px-4 py-2.5 rounded-xl transition-colors"
        >
          Start counting
        </Link>
      </Card>
    </div>
  );
}
