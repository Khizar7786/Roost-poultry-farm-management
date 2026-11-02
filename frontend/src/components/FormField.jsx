import { cx } from "../lib/utils";

export default function FormField({ label, error, className, ...inputProps }) {
  return (
    <label className={cx("block", className)}>
      <span className="block text-sm font-semibold text-ink-darker mb-1.5">{label}</span>
      <input
        className={cx(
          "w-full px-3.5 py-2.5 rounded-xl border text-sm bg-white transition-colors",
          "placeholder:text-slate/35 outline-none",
          error
            ? "border-rust focus:border-rust"
            : "border-ink-light focus:border-ink/40"
        )}
        {...inputProps}
      />
      {error && <span className="block text-xs text-rust mt-1.5">{error}</span>}
    </label>
  );
}
