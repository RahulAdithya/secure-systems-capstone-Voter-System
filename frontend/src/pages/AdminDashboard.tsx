import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { auth } from "../lib/auth";
import { emitUx } from "../lib/ux";

type Ballot = { id: number; title: string; options: string[]; votes: number[]; totalVotes: number };

export default function AdminDashboard(): React.ReactElement {
  const [ballots, setBallots] = useState<Ballot[]>([]);
  const [error, setError] = useState("");
  const [logoutMessage, setLogoutMessage] = useState(""); 
  
  const INACTIVITY_LIMIT = 60 * 1000; // 1 min
  const WARNING_TIME = 30 * 1000; // 30 sec before logout
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
  
        if (elapsed >= INACTIVITY_LIMIT) {
          auth.clear(); // remove token
          setLogoutMessage("You have been logged out due to inactivity.");
          window.location.href = "/login";
        } else if (elapsed >= WARNING_TIME) {
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
    <div style={{ padding: 24, fontFamily: "system-ui", maxWidth: 720, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Admin Dashboard</h2>
        <button
          onClick={() => {
            // Emit before clearing token
            emitUx("logout_click", { role: "admin" });
            auth.clear();
            window.location.href = "/admin-login";
          }}
        >
          Sign out
        </button>
      </div>
      <p>Total ballots: {ballots.length} | Total votes cast: {grandTotal}</p>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      <div style={{ marginTop: 16 }}>
        {ballots.map((b) => (
          <div key={b.id} style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8, marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <strong>{b.title}</strong>
              <span>Total votes: {b.totalVotes}</span>
            </div>
            <div style={{ marginTop: 8 }}>
              {b.options.map((opt, idx) => (
                <div key={idx} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{opt}</span>
                  <span>{b.votes?.[idx] ?? 0}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
        {logoutMessage && (
        <div
          style={{
            position: "fixed",
            bottom: 20,
            left: 20,
            background: "rgba(255, 165, 0, 0.9)",
            color: "#000",
            padding: "0.5rem 1rem",
            borderRadius: 5,
            boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
            zIndex: 1000,
          }}
        >
          {logoutMessage}
        </div>
        )}
    </div>
  );
}
