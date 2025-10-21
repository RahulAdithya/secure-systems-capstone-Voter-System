type CardProps = {
  children: React.ReactNode;
  className?: string;
};

export default function Card({ children, className = "" }: CardProps): React.ReactElement {
  return (
    <div
      className={[
        "rounded-2xl border border-border/80 bg-card shadow-card transition-colors duration-200",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </div>
  );
}
