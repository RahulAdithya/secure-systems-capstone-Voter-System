type LabelProps = {
  htmlFor?: string;
  children: React.ReactNode;
  className?: string;
};

export default function Label({ htmlFor, children, className = "" }: LabelProps): React.ReactElement {
  return (
    <label
      htmlFor={htmlFor}
      className={["mb-1 block text-xs font-medium uppercase tracking-wide text-muted", className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </label>
  );
}
