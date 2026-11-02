import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { CheckCircle2, UserPlus } from "lucide-react";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import Button from "../components/Button";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../api/client";

const INITIAL = {
  full_name: "",
  email: "",
  username: "",
  password: "",
  farm_name: "",
  farm_location: "",
};

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(INITIAL);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const update = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      setDone(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (done) {
    return (
      <AuthLayout>
        <div className="text-center py-6">
          <span className="inline-flex h-14 w-14 rounded-full bg-mint-light items-center justify-center mb-5">
            <CheckCircle2 size={28} className="text-mint" />
          </span>
          <h2 className="font-display text-2xl font-semibold text-ink-darker mb-2">
            {form.farm_name} is on Roost
          </h2>
          <p className="text-sm text-slate/60 mb-8">
            Your owner account is ready. Log in to see your dashboard and start adding batches.
          </p>
          <Button as={Link} to="/login" className="w-full">
            Continue to log in
          </Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="mb-8">
        <h2 className="font-display text-2xl font-semibold text-ink-darker">Register your farm</h2>
        <p className="text-sm text-slate/60 mt-1.5">
          Creates your owner account and your farm in one step.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField label="Your full name" value={form.full_name} onChange={update("full_name")} placeholder="Ali Khan" required />
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Username" value={form.username} onChange={update("username")} placeholder="alikhan" required />
          <FormField label="Email" type="email" value={form.email} onChange={update("email")} placeholder="ali@farm.com" required />
        </div>
        <FormField label="Password" type="password" autoComplete="new-password" value={form.password} onChange={update("password")} placeholder="At least 8 characters" required />

        <div className="pt-2 border-t border-ink-light" />

        <FormField label="Farm name" value={form.farm_name} onChange={update("farm_name")} placeholder="Green Valley Poultry" required />
        <FormField label="Farm location" value={form.farm_location} onChange={update("farm_location")} placeholder="Lahore, Pakistan" required />

        {error && (
          <div className="text-sm text-rust bg-rust-light rounded-xl px-3.5 py-2.5">{error}</div>
        )}

        <Button type="submit" className="w-full" loading={loading}>
          <UserPlus size={16} />
          Create account
        </Button>
      </form>

      <p className="text-sm text-slate/60 text-center mt-8">
        Already on Roost?{" "}
        <Link to="/login" className="text-ink font-semibold hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
