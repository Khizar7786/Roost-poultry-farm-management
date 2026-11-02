import { cx } from "../lib/utils";

const VARIANTS = {
  primary: "bg-ink text-white hover:bg-ink-dark active:bg-ink-darker",
  gold: "bg-gold text-ink-darker hover:bg-gold-deep",
  ghost: "bg-transparent text-ink hover:bg-ink-light",
  outline: "bg-white text-ink border border-ink/20 hover:border-ink/40 hover:bg-ink-light",
  danger: "bg-rust text-white hover:bg-rust/90",
};

const SIZES = {
  sm: "text-sm px-3 py-1.5 rounded-lg",
  md: "text-sm px-4 py-2.5 rounded-xl",
  lg: "text-base px-6 py-3 rounded-xl",
};

export default function Button({
  as: Comp = "button",
  variant = "primary",
  size = "md",
  className,
  disabled,
  loading,
  children,
  ...props
}) {
  return (
    <Comp
      className={cx(
        "inline-flex items-center justify-center gap-2 font-semibold transition-colors duration-150",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        VARIANTS[variant],
        SIZES[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="h-3.5 w-3.5 rounded-full border-2 border-current border-t-transparent animate-spin" />
      )}
      {children}
    </Comp>
  );
}
