import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "outline" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  loading?: boolean;
};

const variantStyles: Record<Variant, string> = {
  primary:
    "bg-primary text-white dark:text-black hover:brightness-95 active:brightness-90 focus-visible:ring-ring disabled:hover:brightness-100",
  outline:
    "border border-border bg-transparent text-text hover:bg-bg-elev/60 active:bg-bg-elev focus-visible:ring-ring",
  ghost: "text-text hover:bg-bg-elev/60 active:bg-bg-elev focus-visible:ring-ring",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className = "", variant = "primary", loading = false, disabled, children, ...rest },
  ref,
) {
  const classes = [
    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-bg",
    "disabled:cursor-not-allowed disabled:opacity-60",
    variantStyles[variant],
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button ref={ref} className={classes} disabled={disabled || loading} {...rest}>
      {loading ? <span className="animate-pulse">…</span> : children}
    </button>
  );
});

export default Button;
