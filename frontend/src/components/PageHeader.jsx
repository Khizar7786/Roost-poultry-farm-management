export default function PageHeader({ eyebrow, title, description, action }) {
  return (
    <div className="flex items-start justify-between gap-4 mb-8 flex-wrap">
      <div>
        {eyebrow && (
          <div className="text-xs font-bold tracking-widest text-gold-dark uppercase mb-1.5">
            {eyebrow}
          </div>
        )}
        <h1 className="font-display text-3xl font-semibold text-ink-darker">{title}</h1>
        {description && <p className="text-sm text-slate/60 mt-1.5 max-w-xl">{description}</p>}
      </div>
      {action}
    </div>
  );
}
