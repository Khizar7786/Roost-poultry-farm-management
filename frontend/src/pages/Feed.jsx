import { useEffect, useState } from "react";
import { Plus, Wheat, X } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Button from "../components/Button";
import Badge from "../components/Badge";
import FormField from "../components/FormField";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { listFeedStock, createFeedStock, listFeedLogs, createFeedLog } from "../api/feed";
import { listBatches } from "../api/batches";
import { extractErrorMessage } from "../api/client";
import { formatDate } from "../lib/utils";

export default function Feed() {
  const { user } = useAuth();
  const [stock, setStock] = useState(null);
  const [logs, setLogs] = useState(null);
  const [batches, setBatches] = useState([]);
  const [showStockForm, setShowStockForm] = useState(false);
  const [showLogForm, setShowLogForm] = useState(false);
  const [stockForm, setStockForm] = useState({ feed_type: "", quantity_kg: "", reorder_threshold_kg: "50" });
  const [logForm, setLogForm] = useState({ batch: "", feed_stock: "", quantity_kg: "", log_date: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => {
    listFeedStock().then((d) => setStock(d.results ?? d));
    listFeedLogs().then((d) => setLogs(d.results ?? d));
  };

  useEffect(() => {
    load();
    listBatches().then((d) => setBatches(d.results ?? d));
  }, []);

  const handleAddStock = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createFeedStock(stockForm);
      setStockForm({ feed_type: "", quantity_kg: "", reorder_threshold_kg: "50" });
      setShowStockForm(false);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleAddLog = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createFeedLog(logForm);
      setLogForm({ batch: "", feed_stock: "", quantity_kg: "", log_date: "" });
      setShowLogForm(false);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PageHeader
        eyebrow="Operations"
        title="Feed & Inventory"
        description="Track feed stock and log daily consumption per batch."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card padded={false}>
          <div className="flex items-center justify-between px-6 pt-6 pb-4">
            <h3 className="font-display text-base font-semibold text-ink-darker">Feed stock</h3>
            {user?.role === "OWNER" && (
              <button
                onClick={() => setShowStockForm((s) => !s)}
                className="text-sm font-semibold text-ink flex items-center gap-1 hover:underline"
              >
                {showStockForm ? <X size={14} /> : <Plus size={14} />}
                {showStockForm ? "Cancel" : "Restock"}
              </button>
            )}
          </div>

          {showStockForm && (
            <form onSubmit={handleAddStock} className="px-6 pb-5 grid grid-cols-3 gap-3 items-end border-b border-ink-light">
              <FormField label="Feed type" value={stockForm.feed_type} onChange={(e) => setStockForm({ ...stockForm, feed_type: e.target.value })} placeholder="Starter Feed" required />
              <FormField label="Quantity (kg)" type="number" value={stockForm.quantity_kg} onChange={(e) => setStockForm({ ...stockForm, quantity_kg: e.target.value })} required />
              <FormField label="Reorder at (kg)" type="number" value={stockForm.reorder_threshold_kg} onChange={(e) => setStockForm({ ...stockForm, reorder_threshold_kg: e.target.value })} required />
              {error && <div className="col-span-3 text-sm text-rust">{error}</div>}
              <Button type="submit" size="sm" loading={saving} className="col-span-3 w-fit">
                Add stock
              </Button>
            </form>
          )}

          {stock === null ? (
            <LoadingSpinner label="Loading…" />
          ) : stock.length === 0 ? (
            <EmptyState icon={Wheat} title="No feed stock yet" />
          ) : (
            <ul className="divide-y divide-ink-light">
              {stock.map((s) => (
                <li key={s.id} className="px-6 py-3.5 flex items-center justify-between">
                  <div>
                    <div className="font-medium text-ink-darker text-sm">{s.feed_type}</div>
                    <div className="text-xs text-slate/45">Reorder below {s.reorder_threshold_kg}kg</div>
                  </div>
                  <Badge tone={s.needs_reorder ? "rust" : "mint"}>{s.quantity_kg}kg</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card padded={false}>
          <div className="flex items-center justify-between px-6 pt-6 pb-4">
            <h3 className="font-display text-base font-semibold text-ink-darker">Consumption logs</h3>
            <button
              onClick={() => setShowLogForm((s) => !s)}
              className="text-sm font-semibold text-ink flex items-center gap-1 hover:underline"
            >
              {showLogForm ? <X size={14} /> : <Plus size={14} />}
              {showLogForm ? "Cancel" : "Log usage"}
            </button>
          </div>

          {showLogForm && (
            <form onSubmit={handleAddLog} className="px-6 pb-5 space-y-3 border-b border-ink-light">
              <div className="grid grid-cols-2 gap-3">
                <label className="block">
                  <span className="block text-sm font-semibold text-ink-darker mb-1.5">Batch</span>
                  <select
                    value={logForm.batch}
                    onChange={(e) => setLogForm({ ...logForm, batch: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-ink-light text-sm bg-white outline-none focus:border-ink/40"
                    required
                  >
                    <option value="">Select…</option>
                    {batches.map((b) => (
                      <option key={b.id} value={b.id}>Batch {b.batch_number}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="block text-sm font-semibold text-ink-darker mb-1.5">Feed type</span>
                  <select
                    value={logForm.feed_stock}
                    onChange={(e) => setLogForm({ ...logForm, feed_stock: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-ink-light text-sm bg-white outline-none focus:border-ink/40"
                    required
                  >
                    <option value="">Select…</option>
                    {(stock ?? []).map((s) => (
                      <option key={s.id} value={s.id}>{s.feed_type}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Quantity (kg)" type="number" value={logForm.quantity_kg} onChange={(e) => setLogForm({ ...logForm, quantity_kg: e.target.value })} required />
                <FormField label="Date" type="date" value={logForm.log_date} onChange={(e) => setLogForm({ ...logForm, log_date: e.target.value })} required />
              </div>
              {error && <div className="text-sm text-rust">{error}</div>}
              <Button type="submit" size="sm" loading={saving}>Log consumption</Button>
            </form>
          )}

          {logs === null ? (
            <LoadingSpinner label="Loading…" />
          ) : logs.length === 0 ? (
            <EmptyState icon={Wheat} title="No consumption logged yet" />
          ) : (
            <ul className="divide-y divide-ink-light max-h-96 overflow-y-auto">
              {logs.map((l) => (
                <li key={l.id} className="px-6 py-3 flex items-center justify-between text-sm">
                  <div>
                    <div className="text-ink-darker font-medium">{l.quantity_kg}kg logged</div>
                    <div className="text-xs text-slate/45">{formatDate(l.log_date)} · {l.logged_by_name}</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
