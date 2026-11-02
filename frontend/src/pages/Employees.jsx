import { useEffect, useState } from "react";
import { Plus, Users, X, UserMinus } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import Button from "../components/Button";
import Badge from "../components/Badge";
import FormField from "../components/FormField";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { listEmployees, registerEmployee, deactivateEmployee } from "../api/auth";
import { extractErrorMessage } from "../api/client";
import { initials } from "../lib/utils";

export default function Employees() {
  const [employees, setEmployees] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ full_name: "", email: "", username: "", password: "", phone_number: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => listEmployees().then((d) => setEmployees(d.results ?? d));

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await registerEmployee(form);
      setForm({ full_name: "", email: "", username: "", password: "", phone_number: "" });
      setShowForm(false);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (id) => {
    if (!confirm("Deactivate this employee? They will no longer be able to log in.")) return;
    await deactivateEmployee(id);
    load();
  };

  return (
    <div>
      <PageHeader
        eyebrow="Team · Owner only"
        title="Staff"
        description="Manage the employee accounts on your farm."
        action={
          <Button onClick={() => setShowForm((s) => !s)}>
            {showForm ? <X size={16} /> : <Plus size={16} />}
            {showForm ? "Cancel" : "Add employee"}
          </Button>
        }
      />

      {showForm && (
        <Card className="mb-6">
          <form onSubmit={handleCreate} className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-end">
            <FormField label="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} placeholder="Sara Ahmed" required />
            <FormField label="Phone (optional)" value={form.phone_number} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} placeholder="03XX-XXXXXXX" />
            <FormField label="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} placeholder="saraahmed" required />
            <FormField label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="sara@farm.com" required />
            <FormField label="Temporary password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="At least 8 characters" required />
            {error && <div className="sm:col-span-2 text-sm text-rust">{error}</div>}
            <Button type="submit" loading={saving} className="sm:col-span-2 sm:w-fit">Create account</Button>
          </form>
        </Card>
      )}

      {employees === null ? (
        <LoadingSpinner label="Loading staff…" />
      ) : employees.length === 0 ? (
        <Card>
          <EmptyState icon={Users} title="No employees yet" description="Add your first team member to delegate day-to-day tasks like image capture and feed logging." />
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {employees.map((e) => (
            <Card key={e.id} className="flex items-center gap-3.5">
              <span className="h-11 w-11 rounded-full bg-ink-light flex items-center justify-center text-sm font-bold text-ink shrink-0">
                {initials(`${e.first_name} ${e.last_name}`)}
              </span>
              <div className="min-w-0 flex-1">
                <div className="font-semibold text-ink-darker text-sm truncate">
                  {e.first_name} {e.last_name}
                </div>
                <div className="text-xs text-slate/50 truncate">{e.email}</div>
              </div>
              {e.is_active_employee ? (
                <button
                  onClick={() => handleDeactivate(e.id)}
                  title="Deactivate"
                  className="text-slate/40 hover:text-rust transition-colors shrink-0"
                >
                  <UserMinus size={17} />
                </button>
              ) : (
                <Badge tone="rust">Inactive</Badge>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
