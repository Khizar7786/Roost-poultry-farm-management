import { useEffect, useState } from "react";
import { Plus, DollarSign, X } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Button from "../components/Button";
import StatCard from "../components/StatCard";
import FormField from "../components/FormField";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { listSales, createSale } from "../api/sales";
import { listBatches } from "../api/batches";
import { extractErrorMessage } from "../api/client";
import { formatDate } from "../lib/utils";

export default function Sales() {
  const [sales, setSales] = useState(null);
  const [batches, setBatches] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ batch: "", buyer_name: "", quantity: "", price_per_unit: "", sale_date: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => listSales().then((d) => setSales(d.results ?? d));

  useEffect(() => {
    load();
    listBatches().then((d) => setBatches(d.results ?? d));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createSale({ ...form, batch: form.batch || null });
      setForm({ batch: "", buyer_name: "", quantity: "", price_per_unit: "", sale_date: "" });
      setShowForm(false);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const totalRevenue = sales?.reduce((sum, s) => sum + Number(s.total_amount), 0) ?? 0;
  const totalBirdsSold = sales?.reduce((sum, s) => sum + s.quantity, 0) ?? 0;

  return (
    <div>
      <PageHeader
        eyebrow="Financials · Owner only"
        title="Sales"
        description="Every sale recorded on your farm — this feeds your market price forecasts too."
        action={
          <Button onClick={() => setShowForm((s) => !s)}>
            {showForm ? <X size={16} /> : <Plus size={16} />}
            {showForm ? "Cancel" : "Record sale"}
          </Button>
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <StatCard icon={DollarSign} tone="ink" label="Total revenue" value={`${totalRevenue.toLocaleString()} PKR`} />
        <StatCard icon={DollarSign} tone="gold" label="Birds sold" value={totalBirdsSold.toLocaleString()} />
      </div>

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-end">
            <label className="block sm:col-span-1">
              <span className="block text-sm font-semibold text-ink-darker mb-1.5">Batch (optional)</span>
              <select
                value={form.batch}
                onChange={(e) => setForm({ ...form, batch: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-ink-light text-sm bg-white outline-none focus:border-ink/40"
              >
                <option value="">Not batch-specific</option>
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>Batch {b.batch_number}</option>
                ))}
              </select>
            </label>
            <FormField label="Buyer name" value={form.buyer_name} onChange={(e) => setForm({ ...form, buyer_name: e.target.value })} placeholder="City Market" required />
            <FormField label="Sale date" type="date" value={form.sale_date} onChange={(e) => setForm({ ...form, sale_date: e.target.value })} required />
            <FormField label="Quantity" type="number" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} required />
            <FormField label="Price per unit (PKR)" type="number" step="0.01" value={form.price_per_unit} onChange={(e) => setForm({ ...form, price_per_unit: e.target.value })} required />
            {error && <div className="sm:col-span-3 text-sm text-rust">{error}</div>}
            <Button type="submit" loading={saving} className="sm:col-span-3 sm:w-fit">Record sale</Button>
          </form>
        </Card>
      )}

      <Card padded={false}>
        {sales === null ? (
          <LoadingSpinner label="Loading…" />
        ) : sales.length === 0 ? (
          <EmptyState icon={DollarSign} title="No sales recorded yet" />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate/50 border-b border-ink-light">
                <th className="px-6 py-3 font-semibold">Date</th>
                <th className="px-6 py-3 font-semibold">Buyer</th>
                <th className="px-6 py-3 font-semibold">Batch</th>
                <th className="px-6 py-3 font-semibold">Quantity</th>
                <th className="px-6 py-3 font-semibold">Price/unit</th>
                <th className="px-6 py-3 font-semibold">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-light">
              {sales.map((s) => (
                <tr key={s.id}>
                  <td className="px-6 py-3 text-slate/60">{formatDate(s.sale_date)}</td>
                  <td className="px-6 py-3 text-ink-darker font-medium">{s.buyer_name}</td>
                  <td className="px-6 py-3 text-slate/60">{s.batch_number ? `Batch ${s.batch_number}` : "—"}</td>
                  <td className="px-6 py-3 text-slate/60">{s.quantity}</td>
                  <td className="px-6 py-3 text-slate/60">{s.price_per_unit} PKR</td>
                  <td className="px-6 py-3 font-semibold text-ink-darker">{Number(s.total_amount).toLocaleString()} PKR</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
