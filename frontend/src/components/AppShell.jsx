import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu } from "lucide-react";
import Sidebar from "./Sidebar";
import ChatbotWidget from "./ChatbotWidget";

export default function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-canvas">
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      <div className="flex-1 min-w-0">
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 bg-white border-b border-ink-light sticky top-0 z-20">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 rounded-lg hover:bg-ink-light text-ink"
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
          <span className="font-display text-lg font-semibold text-ink-darker">Roost</span>
        </header>

        <main className="px-5 sm:px-8 py-8 max-w-7xl mx-auto">
          <Outlet />
        </main>
      </div>

      <ChatbotWidget />
    </div>
  );
}
