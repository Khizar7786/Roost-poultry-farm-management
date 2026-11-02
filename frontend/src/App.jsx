import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AppShell from "./components/AppShell";
import LoadingSpinner from "./components/LoadingSpinner";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Batches from "./pages/Batches";
import ChickCounting from "./pages/ChickCounting";
import PricePrediction from "./pages/PricePrediction";
import Feed from "./pages/Feed";
import Health from "./pages/Health";
import Sales from "./pages/Sales";
import Alerts from "./pages/Alerts";
import Employees from "./pages/Employees";

function PublicOnlyRoute({ children }) {
  const { user, initializing } = useAuth();
  if (initializing) return <LoadingSpinner full label="Loading Roost…" />;
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<PublicOnlyRoute><Login /></PublicOnlyRoute>} />
      <Route path="/register" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>} />

      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/batches" element={<Batches />} />
        <Route path="/chick-counting" element={<ChickCounting />} />
        <Route
          path="/price-prediction"
          element={
            <ProtectedRoute ownerOnly>
              <PricePrediction />
            </ProtectedRoute>
          }
        />
        <Route path="/feed" element={<Feed />} />
        <Route path="/health" element={<Health />} />
        <Route
          path="/sales"
          element={
            <ProtectedRoute ownerOnly>
              <Sales />
            </ProtectedRoute>
          }
        />
        <Route path="/alerts" element={<Alerts />} />
        <Route
          path="/employees"
          element={
            <ProtectedRoute ownerOnly>
              <Employees />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
