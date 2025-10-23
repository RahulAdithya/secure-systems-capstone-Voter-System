import React from "react";
import { Link } from "react-router-dom";

export default function Forbidden(): React.ReactElement {
  return (
    <div className="mx-auto flex min-h-[70vh] w-full max-w-xl flex-col items-center justify-center gap-4 text-center">
      <div className="space-y-2">
        <p className="text-sm uppercase tracking-wide text-red-500">403</p>
        <h1 className="text-3xl font-semibold">Access denied</h1>
        <p className="text-sm text-muted">
          You don&apos;t have permission to view this area. If you believe this is a mistake, contact an administrator.
        </p>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
        <Link className="rounded-lg border border-border px-4 py-2 text-primary hover:bg-primary/10" to="/">
          Return to dashboard
        </Link>
        <Link className="rounded-lg border border-border px-4 py-2 text-muted hover:bg-bg-elev" to="/login">
          Go to login
        </Link>
      </div>
    </div>
  );
}
