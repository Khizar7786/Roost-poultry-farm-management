import { cx } from "../lib/utils";

const TONES = {
  neutral: "bg-slate/10 text-slate",
  ink: "bg-ink-light text-ink",
  gold: "bg-gold-light text-gold-dark",
  mint: "bg-mint-light text-mint",
  rust: "bg-rust-light text-rust",
};

export default function Badge({ tone = "neutral", children, className }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap",
        TONES[tone],
        className
      )}
    >
      {children}
    </span>
  );
}
