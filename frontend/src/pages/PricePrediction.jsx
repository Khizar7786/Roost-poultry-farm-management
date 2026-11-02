import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { TrendingUp, Sparkles, Target, Calendar } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Button from "../components/Button";
import Badge from "../components/Badge";
import StatCard from "../components/StatCard";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { listPricePredictions, triggerPricePrediction } from "../api/monitoring";
import { extractErrorMessage } from "../api/client";
import { formatDate, formatDateTime } from "../lib/utils";

export default function PricePrediction() {
  const [horizon, setHorizon] = useState(7);
  const [latest, setLatest] = useState(null);
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = () =>
    listPricePredictions().then((d) => {
      const list = d.results ?? d;
      setHistory(list);
      setLatest(list[0] ?? null);
    });

  useEffect(() => {
    load();
  }, []);

  const handleTrigger = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await triggerPricePrediction(horizon);
      setLatest(res);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const chartData = latest
    ? [
        { date: formatDate(latest.last_known_date), price: latest.last_known_price_pkr, isActual: true },
        ...latest.forecast.map((f) => ({ date: formatDate(f.date), price: f.price_pkr, isActual: false })),
      ]
    : [];

  return (
    <div>
      <PageHeader
        eyebrow="UC-03 · LSTM + XGBoost"
        title="Market Price Forecast"
        description="Lahore farm-gate broiler price forecast from a trained LSTM (price) + XGBoost (direction) hybrid model."
        action={
          <div className="flex items-center gap-2">
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="px-3 py-2.5 rounded-xl border border-ink-light text-sm bg-white outline-none focus:border-ink/40"
            >
              {[3, 5, 7, 10, 14, 30].map((n) => (
                <option key={n} value={n}>
                  {n}-day forecast
                </option>
              ))}
            </select>
            <Button onClick={handleTrigger} loading={loading}>
              <Sparkles size={16} />
              Generate
            </Button>
          </div>
        }
      />

      {error && <Card className="mb-6 text-sm text-rust bg-rust-light border-none">{error}</Card>}

      {horizon > 7 && (
        <Card className="mb-6 bg-gold-light border-none text-sm text-ink-darker">
          Accuracy drops sharply past ~7 days — treat longer horizons as directional guidance, not precise
          numbers.
        </Card>
      )}

      {history === null ? (
        <LoadingSpinner label="Loading forecasts…" />
      ) : !latest ? (
        <Card>
          <EmptyState
            icon={TrendingUp}
            title="No forecast yet"
            description="Click Generate to produce your first market price forecast from the trained model."
          />
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <StatCard
              icon={Calendar}
              tone="ink"
              label="Last known price"
              value={`${latest.last_known_price_pkr} PKR`}
              sub={`as of ${formatDate(latest.last_known_date)}`}
            />
            <StatCard
              icon={Target}
              tone="ink"
              label="Model accuracy"
              value={`${(latest.model_accuracy * 100).toFixed(0)}%`}
              sub="held-out test accuracy (direction)"
            />
            <StatCard
              icon={TrendingUp}
              tone="gold"
              label="Net change"
              value={`${latest.summary.net_change_pkr > 0 ? "+" : ""}${latest.summary.net_change_pkr} PKR`}
              sub={`${(latest.summary.net_change_pct * 100).toFixed(1)}% over ${latest.horizon_days} days`}
            />
          </div>

          <Card className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-base font-semibold text-ink-darker">
                {latest.horizon_days}-day forecast
              </h3>
              <span className="text-xs text-slate/45">Generated {formatDateTime(latest.created_at)}</span>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#EFEEE9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#6B675C" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#6B675C" }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, border: "1px solid #EFEEE9", fontSize: 13 }}
                    formatter={(value) => [`${value} PKR`, "Price"]}
                  />
                  <ReferenceLine x={chartData[0]?.date} stroke="#D6D3C8" strokeDasharray="3 3" />
                  {/* Black line with yellow points: #FFC800 as a 2px stroke on
                      white is ~1.6:1 and disappears, so the ink carries the
                      shape and the accent marks the data points. */}
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#1A1A18"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: "#FFC800", stroke: "#1A1A18", strokeWidth: 1.5 }}
                    activeDot={{ r: 6, fill: "#FFC800", stroke: "#1A1A18", strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-xs text-slate/40 mt-2">
              Dashed line marks the last known actual price — everything to the right is forecast.
            </p>
          </Card>

          <Card padded={false}>
            <h3 className="font-display text-base font-semibold text-ink-darker px-6 pt-6 pb-3">
              Day-by-day breakdown
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate/50 border-y border-ink-light">
                    <th className="px-6 py-2.5 font-semibold">Date</th>
                    <th className="px-6 py-2.5 font-semibold">Price</th>
                    <th className="px-6 py-2.5 font-semibold">Direction</th>
                    <th className="px-6 py-2.5 font-semibold">Confidence</th>
                    <th className="px-6 py-2.5 font-semibold">RSI14</th>
                    <th className="px-6 py-2.5 font-semibold">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-light">
                  {latest.forecast.map((f, i) => (
                    <tr key={i}>
                      <td className="px-6 py-2.5 text-ink-darker">{formatDate(f.date)}</td>
                      <td className="px-6 py-2.5 font-semibold text-ink-darker">
                        {f.price_pkr} PKR
                        <span className={"ml-1.5 text-xs font-normal " + (f.delta_pkr >= 0 ? "text-mint" : "text-rust")}>
                          ({f.delta_pkr >= 0 ? "+" : ""}
                          {f.delta_pkr})
                        </span>
                      </td>
                      <td className="px-6 py-2.5">
                        <Badge tone={f.direction === "UP" ? "mint" : "rust"}>{f.direction}</Badge>
                      </td>
                      <td className="px-6 py-2.5 text-slate/60">
                        {(f.confidence * 100).toFixed(0)}%
                        {f.low_confidence && (
                          <span className="ml-1.5 text-xs text-gold-dark font-semibold">low</span>
                        )}
                      </td>
                      <td className="px-6 py-2.5 text-slate/60">{f.rsi14}</td>
                      <td className="px-6 py-2.5">
                        <div className="flex flex-wrap gap-1">
                          {f.events.map((ev, j) => (
                            <span key={j} className="text-xs bg-ink-light text-ink px-2 py-0.5 rounded-full">
                              {ev}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
