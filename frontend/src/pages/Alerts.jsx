import { useEffect, useState } from "react";
import { Bell, CheckCircle2, Filter } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Badge from "../components/Badge";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { listAlerts, acknowledgeAlert } from "../api/alerts";
import { formatDateTime } from "../lib/utils";
import { cx } from "../lib/utils";

const SEVERITY_TONE = { HIGH: "rust", MEDIUM: "gold", LOW: "ink" };

export default function Alerts() {
  const [alerts, setAlerts] = useState(null);
  const [filter, setFilter] = useState(false);

  const load = (unackOnly) => listAlerts(unackOnly).then((d) => setAlerts(d.results ?? d));

  useEffect(() => {
    load(filter);
  }, [filter]);

  const handleAck = async (id) => {
    await acknowledgeAlert(id);
    load(filter);
  };

  return (
    <div>
      <PageHeader
        eyebrow="UC-08"
        title="Alerts"
        description="Mortality and system notifications for your farm."
        action={
          <button
            onClick={() => setFilter((f) => !f)}
            className={cx(
              "text-sm font-semibold px-4 py-2.5 rounded-xl border flex items-center gap-2 transition-colors",
              filter ? "bg-ink text-white border-ink" : "bg-white text-ink border-ink-light"
            )}
          >
            <Filter size={14} />
            {filter ? "Showing unacknowledged" : "Show all"}
          </button>
        }
      />

      <Card padded={false}>
        {alerts === null ? (
          <LoadingSpinner label="Loading alerts…" />
        ) : alerts.length === 0 ? (
          <EmptyState icon={CheckCircle2} title="All clear" description="No alerts to show." />
        ) : (
          <ul className="divide-y divide-ink-light">
            {alerts.map((a) => (
              <li key={a.id} className="px-6 py-4 flex items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <span className="mt-0.5">
                    <Bell size={16} className={a.severity === "HIGH" ? "text-rust" : "text-slate/40"} />
                  </span>
                  <div>
                    <p className="text-sm font-medium text-ink-darker">{a.message}</p>
                    <p className="text-xs text-slate/45 mt-1 flex items-center gap-2">
                      {formatDateTime(a.created_at)}
                      {a.escalated && <Badge tone="rust">Escalated</Badge>}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Badge tone={SEVERITY_TONE[a.severity]}>{a.severity}</Badge>
                  {a.acknowledged ? (
                    <span className="text-xs text-mint font-semibold flex items-center gap-1">
                      <CheckCircle2 size={13} /> Acknowledged
                    </span>
                  ) : (
                    <button
                      onClick={() => handleAck(a.id)}
                      className="text-xs font-semibold text-ink hover:underline"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
