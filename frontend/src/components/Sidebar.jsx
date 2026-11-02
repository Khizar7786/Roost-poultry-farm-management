import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Bird,
  Camera,
  TrendingUp,
  Wheat,
  Syringe,
  DollarSign,
  Bell,
  Users,
  LogOut,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { cx, initials } from "../lib/utils";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["OWNER", "EMPLOYEE"] },
  { to: "/batches", label: "Batches", icon: Bird, roles: ["OWNER", "EMPLOYEE"] },
  { to: "/chick-counting", label: "Chick Counting", icon: Camera, roles: ["OWNER", "EMPLOYEE"] },
  { to: "/price-prediction", label: "Price Forecast", icon: TrendingUp, roles: ["OWNER"] },
  { to: "/feed", label: "Feed", icon: Wheat, roles: ["OWNER", "EMPLOYEE"] },
  { to: "/health", label: "Vaccinations", icon: Syringe, roles: ["OWNER", "EMPLOYEE"] },
  { to: "/sales", label: "Sales", icon: DollarSign, roles: ["OWNER"] },
  { to: "/alerts", label: "Alerts", icon: Bell, roles: ["OWNER", "EMPLOYEE"] },
  { to: "/employees", label: "Staff", icon: Users, roles: ["OWNER"] },
];

export default function Sidebar({ mobileOpen, onClose }) {
  const { user, logout } = useAuth();
  const items = NAV_ITEMS.filter((i) => i.roles.includes(user?.role));

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={cx(
          "fixed lg:sticky top-0 left-0 h-screen w-64 bg-ink-darker text-white flex flex-col z-40",
          "transition-transform duration-200 lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center gap-2.5 px-6 py-6">
          <span className="h-9 w-9 rounded-full bg-gold flex items-center justify-center">
            <Bird size={19} className="text-ink-darker" strokeWidth={2.3} />
          </span>
          <span className="font-display text-xl font-semibold tracking-tight">Roost</span>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                cx(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-colors",
                  // The accent carries the active state. A darker-ink fill is
                  // only ~1.04:1 against the ink-darker sidebar — invisible.
                  isActive
                    ? "bg-gold text-ink-darker font-semibold"
                    : "text-white/60 hover:text-white hover:bg-white/10"
                )
              }
            >
              <item.icon size={17} strokeWidth={2} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-white/10">
          <div className="flex items-center gap-2.5 px-3 py-2">
            <span className="h-8 w-8 rounded-full bg-ink-dark flex items-center justify-center text-xs font-bold text-gold shrink-0">
              {initials(`${user?.first_name} ${user?.last_name}`)}
            </span>
            <div className="min-w-0">
              <div className="text-sm font-semibold truncate">
                {user?.first_name} {user?.last_name}
              </div>
              <div className="text-xs text-white/50">
                {user?.role === "OWNER" ? "Farm Owner" : "Farm Employee"}
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 mt-1 rounded-xl text-sm font-medium text-white/60 hover:text-white hover:bg-white/10 transition-colors"
          >
            <LogOut size={17} strokeWidth={2} />
            Log out
          </button>
        </div>
      </aside>
    </>
  );
}
