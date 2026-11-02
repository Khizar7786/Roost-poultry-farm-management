import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { LogIn } from "lucide-react";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import Button from "../components/Button";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage } from "../api/client";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.username, form.password);
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (err) {
      setError(
        err?.response?.status === 401
          ? "That username or password isn't right. Please try again."
          : extractErrorMessage(err)
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout>
      <div className="mb-8">
        <h2 className="font-display text-2xl font-semibold text-ink-darker">Welcome back</h2>
        <p className="text-sm text-slate/60 mt-1.5">Log in to your farm's dashboard.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          label="Username"
          type="text"
          autoComplete="username"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          placeholder="yourfarmname"
          required
        />
        <FormField
          label="Password"
          type="password"
          autoComplete="current-password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          placeholder="••••••••"
          required
        />

        {error && (
          <div className="text-sm text-rust bg-rust-light rounded-xl px-3.5 py-2.5">{error}</div>
        )}

        <Button type="submit" className="w-full" loading={loading}>
          <LogIn size={16} />
          Log in
        </Button>
      </form>

      <p className="text-sm text-slate/60 text-center mt-8">
        New to Roost?{" "}
        <Link to="/register" className="text-ink font-semibold hover:underline">
          Register your farm
        </Link>
      </p>
    </AuthLayout>
  );
}
