import { cx } from "../lib/utils";

const TONES = {
  ink: "bg-ink text-white",
  gold: "bg-gold text-ink-darker",
  mint: "bg-mint text-white",
  rust: "bg-rust text-white",
  light: "bg-ink-light text-ink",
};

const SIZES = {
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-14 w-14",
};

export default function IconBadge({ icon: Icon, tone = "ink", size = "md", className }) {
  const iconSize = { sm: 15, md: 18, lg: 26 }[size];
  return (
    <span
      className={cx(
        "inline-flex items-center justify-center rounded-full shrink-0",
        TONES[tone],
        SIZES[size],
        className
      )}
    >
      <Icon size={iconSize} strokeWidth={2.1} />
    </span>
  );
}
