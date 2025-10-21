import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { api } from "../lib/api";
import { auth } from "../lib/auth";

type BallotSummary = { id: number; title: string; options: string[]; totalVotes: number };
type BallotDetail = BallotSummary;

function votedKey(ballotId: number): string {
  return `voted:ballot:${ballotId}`;
}

export default function UserDashboard(): React.ReactElement {
  const [ballots, setBallots] = useState<BallotSummary[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<BallotDetail | null>(null);
  const [choice, setChoice] = useState<number | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);
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
      .get<BallotSummary[]>("/ballots")
      .then(({ data }) => {
        if (!mounted) return;
        setBallots(data);
        if (data.length > 0) setSelected(data[0].id);
      })
      .catch(() => setError("Failed to load ballots"));
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (selected == null) return;
    let mounted = true;
    Promise.all([
      api.get<BallotDetail>(`/ballots/${selected}`),
      api.get<{ already_voted: boolean }>(`/ballots/${selected}/status`).catch(() => ({ data: { already_voted: false } } as any)),
    ])
      .then(([ballotRes, statusRes]) => {
        if (!mounted) return;
        setDetail(ballotRes.data);
        if (statusRes?.data?.already_voted) {
          localStorage.setItem(votedKey(selected), "1");
        } else {
          localStorage.removeItem(votedKey(selected));
        }
      })
      .catch(() => setError("Failed to load ballot"));
    return () => {
      mounted = false;
    };
  }, [selected]);

  const hasVoted = useMemo(() => {
    return selected != null && !!localStorage.getItem(votedKey(selected));
  }, [selected]);

  async function submitVote(e: FormEvent) {
    e.preventDefault();
    setError("");
    setMessage("");
    if (selected == null || choice == null) return;
    if (hasVoted) {
      setMessage("You have already voted on this ballot.");
      return;
    }
    setLoading(true);
    try {
      await api.post(`/ballots/${selected}/vote`, { option_index: choice });
      localStorage.setItem(votedKey(selected), "1");
      setMessage("Thanks! Your vote has been recorded.");
    } catch (err) {
      if (isAxiosError(err) && err.response?.status === 409) {
        setMessage("You have already voted on this ballot.");
      } else {
        setError("Failed to submit vote");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: "system-ui", maxWidth: 720, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Voter Dashboard</h2>
        <button
          onClick={() => {
            auth.clear();
            window.location.href = "/login";
          }}
        >
          Sign out
        </button>
      </div>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      <div style={{ marginTop: 8 }}>
        <label>
          Select ballot
          <select
            value={selected ?? ""}
            onChange={(e) => setSelected(parseInt(e.target.value))}
            style={{ marginLeft: 8 }}
          >
            {ballots.map((b) => (
              <option key={b.id} value={b.id}>
                {b.title}
              </option>
            ))}
          </select>
        </label>
      </div>

      {detail && (
        <form onSubmit={submitVote} style={{ marginTop: 16, border: "1px solid #ddd", padding: 12, borderRadius: 8 }}>
          <strong>{detail.title}</strong>
          <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
            {detail.options.map((opt, idx) => (
              <label key={idx} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="radio"
                  name="choice"
                  value={idx}
                  disabled={hasVoted}
                  checked={choice === idx}
                  onChange={() => setChoice(idx)}
                />
                <span>{opt}</span>
              </label>
            ))}
          </div>
          <button type="submit" disabled={loading || hasVoted} style={{ marginTop: 12 }}>
            {hasVoted ? "Already voted" : "Submit vote"}
          </button>
          {message && <p style={{ color: "seagreen", marginTop: 8 }}>{message}</p>}
        </form>
      )}
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
