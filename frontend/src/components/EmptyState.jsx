import IconBadge from "./IconBadge";

export default function EmptyState({ icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center text-center gap-3 py-12 px-6">
      <IconBadge icon={icon} tone="light" size="lg" />
      <div>
        <div className="font-display text-lg font-semibold text-ink-darker">{title}</div>
        {description && <p className="text-sm text-slate/60 mt-1 max-w-sm">{description}</p>}
      </div>
      {action}
    </div>
  );
}
