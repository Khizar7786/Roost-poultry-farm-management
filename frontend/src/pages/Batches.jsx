import { useEffect, useState } from "react";
import { Plus, Bird, X } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Button from "../components/Button";
import Badge from "../components/Badge";
import FormField from "../components/FormField";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { listBatches, createBatch } from "../api/batches";
import { extractErrorMessage } from "../api/client";
import { formatDate } from "../lib/utils";

const STATUS_TONE = { ACTIVE: "mint", SOLD: "ink", CULLED: "rust" };

export default function Batches() {
  const { user } = useAuth();
  const [batches, setBatches] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ batch_number: "", arrival_date: "", initial_count: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => listBatches().then((d) => setBatches(d.results ?? d));

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createBatch({ ...form, initial_count: Number(form.initial_count) });
      setForm({ batch_number: "", arrival_date: "", initial_count: "" });
      setShowForm(false);
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
        eyebrow="Flock management"
        title="Batches"
        description="Every flock batch on your farm, from arrival to sale."
        action={
          user?.role === "OWNER" && (
            <Button onClick={() => setShowForm((s) => !s)}>
              {showForm ? <X size={16} /> : <Plus size={16} />}
              {showForm ? "Cancel" : "New batch"}
            </Button>
          )
        }
      />

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
            <FormField
              label="Batch number"
              value={form.batch_number}
              onChange={(e) => setForm({ ...form, batch_number: e.target.value })}
              placeholder="B-001"
              required
            />
            <FormField
              label="Arrival date"
              type="date"
              value={form.arrival_date}
              onChange={(e) => setForm({ ...form, arrival_date: e.target.value })}
              required
            />
            <FormField
              label="Initial count"
              type="number"
              min="1"
              value={form.initial_count}
              onChange={(e) => setForm({ ...form, initial_count: e.target.value })}
              placeholder="500"
              required
            />
            {error && <div className="sm:col-span-3 text-sm text-rust">{error}</div>}
            <Button type="submit" loading={saving} className="sm:col-span-3 sm:w-fit">
              Create batch
            </Button>
          </form>
        </Card>
      )}

      {batches === null ? (
        <LoadingSpinner label="Loading batches…" />
      ) : batches.length === 0 ? (
        <Card>
          <EmptyState
            icon={Bird}
            title="No batches yet"
            description={
              user?.role === "OWNER"
                ? "Create your first batch to start tracking counts, mortality, and health records."
                : "Your farm owner hasn't added any batches yet."
            }
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {batches.map((b) => (
            <Card key={b.id} className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="font-display font-semibold text-ink-darker">
                  Batch {b.batch_number}
                </span>
                <Badge tone={STATUS_TONE[b.status]}>{b.status}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <div className="text-slate/50 text-xs">Current count</div>
                  <div className="font-semibold text-ink-darker">{b.current_count}</div>
                </div>
                <div>
                  <div className="text-slate/50 text-xs">Age</div>
                  <div className="font-semibold text-ink-darker">{b.age_days} days</div>
                </div>
                <div>
                  <div className="text-slate/50 text-xs">Mortality</div>
                  <div className="font-semibold text-ink-darker">{b.mortality_rate_pct}%</div>
                </div>
                <div>
                  <div className="text-slate/50 text-xs">Arrived</div>
                  <div className="font-semibold text-ink-darker">{formatDate(b.arrival_date)}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
