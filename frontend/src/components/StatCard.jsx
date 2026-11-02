import Card from "./Card";
import IconBadge from "./IconBadge";

export default function StatCard({ icon, tone = "ink", label, value, sub, trend }) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <IconBadge icon={icon} tone={tone} />
        {trend && (
          <span
            className={
              "text-xs font-semibold " + (trend.direction === "up" ? "text-mint" : "text-rust")
            }
          >
            {trend.direction === "up" ? "↑" : "↓"} {trend.label}
          </span>
        )}
      </div>
      <div>
        <div className="font-display text-3xl font-semibold text-ink-darker leading-none">
          {value}
        </div>
        <div className="text-sm text-slate/70 mt-1.5">{label}</div>
      </div>
      {sub && <div className="text-xs text-slate/50 -mt-1">{sub}</div>}
    </Card>
  );
}
