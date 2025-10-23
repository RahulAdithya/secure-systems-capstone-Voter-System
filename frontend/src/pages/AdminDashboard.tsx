import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { auth } from "../lib/auth";
import { emitUx } from "../lib/ux";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";

const ADMIN_INACTIVITY_LIMIT = 60 * 1000;
const ADMIN_WARNING_TIME = 30 * 1000;

type Ballot = { id: number; title: string; options: string[]; votes: number[]; totalVotes: number };

export default function AdminDashboard(): React.ReactElement {
  const [ballots, setBallots] = useState<Ballot[]>([]);
  const [error, setError] = useState("");
  const [logoutMessage, setLogoutMessage] = useState("");

  const [lastActivity, setLastActivity] = useState(Date.now());
  
    useEffect(() => {
      const resetActivity = () => setLastActivity(Date.now());
      const events = ["mousemove", "keydown", "click"];
      events.forEach((e) => window.addEventListener(e, resetActivity));
      return () => events.forEach((e) => window.removeEventListener(e, resetActivity));
    }, []);
  
  
    
      useEffect(() => {
      // Emit a signed event when admin dashboard is viewed
      emitUx("view_admin_dashboard");
      const interval = setInterval(() => {
        const elapsed = Date.now() - lastActivity;
  
        if (elapsed >= ADMIN_INACTIVITY_LIMIT) {
          auth.clear(); // remove token
          setLogoutMessage("You have been logged out due to inactivity.");
          window.location.href = "/login";
        } else if (elapsed >= ADMIN_WARNING_TIME) {
          setLogoutMessage("⚠️ You will be logged out soon due to inactivity.");
        } else {
          setLogoutMessage("");
        }
      }, 1000);
  
      return () => clearInterval(interval);
    }, [lastActivity]);
  

  useEffect(() => {
    let mounted = true;
    api
      .get<Ballot[]>("/ballots/tally")
      .then(({ data }) => {
        if (mounted) setBallots(data);
      })
      .catch(() => setError("Failed to load ballots"));
    return () => {
      mounted = false;
    };
  }, []);

  const grandTotal = useMemo(
    () => ballots.reduce((acc, b) => acc + (b.totalVotes || 0), 0),
    [ballots],
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-3xl font-semibold">Admin Dashboard</h2>
          <p className="text-sm text-muted">
            Monitor ballots and vote totals. Inactivity protection will sign you out after one minute.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            // Emit before clearing token
            emitUx("logout_click", { role: "admin" });
            auth.clear();
            window.location.href = "/admin-login";
          }}
        >
          Sign out
        </Button>
      </div>
      <Card className="p-6">
        <p className="text-sm text-muted">
          Total ballots: <span className="font-semibold text-text">{ballots.length}</span> | Total votes cast:{" "}
          <span className="font-semibold text-text">{grandTotal}</span>
        </p>
        {error && <p className="mt-3 text-sm font-medium text-red-500">{error}</p>}
      </Card>
      <div className="grid gap-4">
        {ballots.map((b) => (
          <Card key={b.id} className="p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-lg font-semibold">{b.title}</h3>
              <span className="text-sm text-muted">Total votes: {b.totalVotes}</span>
            </div>
            <div className="mt-4 space-y-2">
              {b.options.map((opt, idx) => (
                <div key={opt} className="flex items-center justify-between rounded-lg border border-border/60 bg-bg-elev px-3 py-2">
                  <span>{opt}</span>
                  <span className="font-mono text-sm">{b.votes?.[idx] ?? 0}</span>
                </div>
              ))}
            </div>
          </Card>
        ))}
        {ballots.length === 0 && (
          <Card className="p-6 text-sm text-muted">No ballots are currently configured. Create one to view tallies here.</Card>
        )}
      </div>
      {logoutMessage && (
        <div className="fixed bottom-5 left-5 z-50 rounded-full border border-amber-400/70 bg-amber-100/90 px-4 py-2 text-sm text-amber-900 shadow-lg dark:border-amber-300/60 dark:bg-amber-200/90">
          {logoutMessage}
        </div>
      )}
    </div>
  );
}
