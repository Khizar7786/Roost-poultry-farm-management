import { Bird, Camera, Skull, TrendingUp } from "lucide-react";

const FEATURES = [
  { icon: Camera, text: "Real-time chick counts from a single photo" },
  { icon: Skull, text: "Automatic mortality alerts" },
  { icon: TrendingUp, text: "Day-ahead market price forecasts" },
];

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen flex">
      {/* Brand panel */}
      <div className="hidden lg:flex lg:w-[44%] relative bg-ink-darker text-white flex-col justify-between p-12 overflow-hidden">
        {/* Decorative concentric rings motif */}
        <div className="pointer-events-none absolute -right-32 -top-32 h-[30rem] w-[30rem] rounded-full border border-white/10" />
        <div className="pointer-events-none absolute -right-16 -top-16 h-96 w-96 rounded-full border border-white/10" />
        <div className="pointer-events-none absolute -right-4 top-4 h-64 w-64 rounded-full border border-gold/20" />
        <div className="pointer-events-none absolute left-[-6rem] bottom-[-6rem] h-80 w-80 rounded-full bg-ink-dark/60 blur-2xl" />

        <div className="relative z-10 flex items-center gap-2.5">
          <span className="h-10 w-10 rounded-full bg-gold flex items-center justify-center">
            <Bird size={20} className="text-ink-darker" strokeWidth={2.3} />
          </span>
          <span className="font-display text-2xl font-semibold tracking-tight">Roost</span>
        </div>

        <div className="relative z-10 max-w-md">
          <h1 className="font-display text-4xl font-medium leading-[1.15] mb-5">
            The farm watches itself, so you don't have to.
          </h1>
          <p className="text-white/60 text-[15px] leading-relaxed mb-9">
            Computer vision and price forecasting — running quietly in the
            background of every shed, every day.
          </p>
          <div className="space-y-4">
            {FEATURES.map((f, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="h-9 w-9 rounded-full bg-white/10 flex items-center justify-center shrink-0">
                  <f.icon size={16} strokeWidth={2} className="text-gold" />
                </span>
                <span className="text-sm text-white/80">{f.text}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-xs text-white/30">
          AI-Integrated Poultry Farm Monitoring &amp; Management System
        </p>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-canvas">
        <div className="w-full max-w-[26rem]">
          <div className="lg:hidden flex items-center gap-2.5 mb-8 justify-center">
            <span className="h-9 w-9 rounded-full bg-ink flex items-center justify-center">
              <Bird size={18} className="text-white" strokeWidth={2.3} />
            </span>
            <span className="font-display text-xl font-semibold text-ink-darker">Roost</span>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
