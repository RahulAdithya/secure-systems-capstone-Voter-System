import { useEffect, useState } from "react";

import { auth } from "../../lib/auth";
type Props = {
  children: React.ReactNode;
};

export default function AppChrome({ children }: Props): React.ReactElement {
  const [role, setRole] = useState<"admin" | "voter" | null>(null);

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

  return (
    <div className="min-h-screen bg-bg text-text transition-colors duration-200">
      <header className="sticky top-0 z-10 border-b border-border/70 bg-bg/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <span className="text-lg font-semibold tracking-tight">Voter System</span>
          <div className="flex items-center gap-3">
            {role && (
              <span className="rounded-full border border-border bg-bg-elev px-3 py-1 text-xs uppercase tracking-wide text-muted">
                role: {role}
              </span>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
    </div>
  );
}
