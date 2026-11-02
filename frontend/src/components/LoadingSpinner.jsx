export default function LoadingSpinner({ label = "Loading…", full }) {
  return (
    <div
      className={
        "flex items-center justify-center gap-3 text-slate/50 " + (full ? "min-h-[50vh]" : "py-10")
      }
    >
      <span className="h-5 w-5 rounded-full border-2 border-ink/20 border-t-ink animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
