import { useEffect, useState } from "react";
import { Plus, Syringe, X, Check } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Button from "../components/Button";
import Badge from "../components/Badge";
import FormField from "../components/FormField";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { listVaccinations, scheduleVaccination, markVaccinationAdministered } from "../api/health";
import { listBatches } from "../api/batches";
import { extractErrorMessage } from "../api/client";
import { formatDate } from "../lib/utils";

const STATUS_TONE = { SCHEDULED: "gold", ADMINISTERED: "mint", MISSED: "rust" };

export default function Health() {
  const { user } = useAuth();
  const [records, setRecords] = useState(null);
  const [batches, setBatches] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ batch: "", vaccine_name: "", scheduled_date: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => listVaccinations().then((d) => setRecords(d.results ?? d));
  const batchNumber = (id) => batches.find((b) => b.id === id)?.batch_number ?? "—";

  useEffect(() => {
    load();
    listBatches().then((d) => setBatches(d.results ?? d));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await scheduleVaccination(form);
      setForm({ batch: "", vaccine_name: "", scheduled_date: "" });
      setShowForm(false);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleAdminister = async (id) => {
    await markVaccinationAdministered(id);
    load();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Operations"
        title="Vaccinations"
        description="Schedule vaccinations and mark them administered as they happen."
        action={
          user?.role === "OWNER" && (
            <Button onClick={() => setShowForm((s) => !s)}>
              {showForm ? <X size={16} /> : <Plus size={16} />}
              {showForm ? "Cancel" : "Schedule"}
            </Button>
          )
        }
      />

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
            <label className="block">
              <span className="block text-sm font-semibold text-ink-darker mb-1.5">Batch</span>
              <select
                value={form.batch}
                onChange={(e) => setForm({ ...form, batch: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-ink-light text-sm bg-white outline-none focus:border-ink/40"
                required
              >
                <option value="">Select…</option>
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>Batch {b.batch_number}</option>
                ))}
              </select>
            </label>
            <FormField label="Vaccine" value={form.vaccine_name} onChange={(e) => setForm({ ...form, vaccine_name: e.target.value })} placeholder="Newcastle Disease" required />
            <FormField label="Scheduled date" type="date" value={form.scheduled_date} onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })} required />
            {error && <div className="sm:col-span-3 text-sm text-rust">{error}</div>}
            <Button type="submit" loading={saving} className="sm:col-span-3 sm:w-fit">Schedule vaccination</Button>
          </form>
        </Card>
      )}

      <Card padded={false}>
        {records === null ? (
          <LoadingSpinner label="Loading…" />
        ) : records.length === 0 ? (
          <EmptyState icon={Syringe} title="No vaccinations scheduled" />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate/50 border-b border-ink-light">
                <th className="px-6 py-3 font-semibold">Batch</th>
                <th className="px-6 py-3 font-semibold">Vaccine</th>
                <th className="px-6 py-3 font-semibold">Scheduled</th>
                <th className="px-6 py-3 font-semibold">Status</th>
                <th className="px-6 py-3 font-semibold"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-light">
              {records.map((r) => (
                <tr key={r.id}>
                  <td className="px-6 py-3 text-ink-darker font-medium">Batch {batchNumber(r.batch)}</td>
                  <td className="px-6 py-3 text-ink-darker">{r.vaccine_name}</td>
                  <td className="px-6 py-3 text-slate/60">{formatDate(r.scheduled_date)}</td>
                  <td className="px-6 py-3">
                    <Badge tone={STATUS_TONE[r.status]}>{r.status}</Badge>
                  </td>
                  <td className="px-6 py-3 text-right">
                    {r.status === "SCHEDULED" && (
                      <button
                        onClick={() => handleAdminister(r.id)}
                        className="text-xs font-semibold text-ink hover:underline flex items-center gap-1 justify-end w-full"
                      >
                        <Check size={13} /> Mark administered
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
