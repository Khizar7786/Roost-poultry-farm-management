import { cx } from "../lib/utils";

export default function Card({ children, className, padded = true, ...props }) {
  return (
    <div
      className={cx(
        "bg-white rounded-2xl border border-ink-light shadow-card",
        padded && "p-6",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
