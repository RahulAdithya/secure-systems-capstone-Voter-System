import { forwardRef, InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

const Input = forwardRef<HTMLInputElement, InputProps>(function Input({ className = "", ...rest }, ref) {
  const classes = [
    "w-full rounded-xl border border-border bg-card px-3 py-2 text-sm text-text shadow-sm transition",
    "placeholder:text-muted/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg",
    "invalid:border-red-500 invalid:focus-visible:ring-red-500",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return <input ref={ref} className={classes} {...rest} />;
});

export default Input;
