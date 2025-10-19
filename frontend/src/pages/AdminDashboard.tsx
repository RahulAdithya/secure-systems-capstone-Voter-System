import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { auth } from "../lib/auth";

type Ballot = { id: number; title: string; options: string[]; votes: number[]; totalVotes: number };

export default function AdminDashboard(): React.ReactElement {
  const [ballots, setBallots] = useState<Ballot[]>([]);
  const [error, setError] = useState("");

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
    </div>
  );
}
