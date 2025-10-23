import { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { auth } from "../../lib/auth";
type Props = {
  children: React.ReactNode;
};

export default function AppChrome({ children }: Props): React.ReactElement {
  const [role, setRole] = useState<"admin" | "voter" | null>(null);
  const location = useLocation();

  useEffect(() => {
    setRole(auth.getRole());

    const handleStorage = (event: StorageEvent) => {
      if (event.key === "role") {
        setRole(auth.getRole());
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const navLinks = useMemo(() => {
    if (role === "admin") {
      return [
        { to: "/admin", label: "Admin" },
        { to: "/mfa-enroll", label: "Enroll MFA" },
      ];
    }
    if (role === "voter") {
      return [{ to: "/", label: "Dashboard" }];
    }
    return [
      { to: "/login", label: "User Login" },
      { to: "/admin-login", label: "Admin Login" },
    ];
  }, [role]);

  const linkClasses = (path: string) =>
    [
      "rounded-lg px-3 py-2 text-sm transition",
      location.pathname === path
        ? "bg-primary/10 text-primary"
        : "text-muted hover:text-primary hover:bg-primary/5",
    ].join(" ");

  return (
    <div className="min-h-screen bg-bg text-text transition-colors duration-200">
      <header className="sticky top-0 z-10 border-b border-border/70 bg-bg/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <span className="inline-flex items-center gap-2 text-lg font-semibold tracking-tight">
            <span className="h-2.5 w-2.5 rounded-full bg-primary shadow-[0_0_12px_rgba(34,211,238,0.8)]" />
            Voter System
          </span>
          <nav className="flex items-center gap-3">
            {navLinks.map((link) => (
              <Link key={link.to} to={link.to} className={linkClasses(link.to)}>
                {link.label}
              </Link>
            ))}
            {role && (
              <span className="rounded-full border border-border bg-bg-elev px-3 py-1 text-xs uppercase tracking-wide text-muted">
                role: {role}
              </span>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
    </div>
  );
}
