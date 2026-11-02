import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import LoadingSpinner from "./LoadingSpinner";

export default function ProtectedRoute({ children, ownerOnly = false }) {
  const { user, initializing } = useAuth();

  if (initializing) return <LoadingSpinner full label="Loading Roost…" />;
  if (!user) return <Navigate to="/login" replace />;
  if (ownerOnly && user.role !== "OWNER") return <Navigate to="/dashboard" replace />;

  return children;
}
