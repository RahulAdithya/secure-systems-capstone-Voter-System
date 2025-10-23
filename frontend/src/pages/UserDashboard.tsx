import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { isAxiosError } from "axios";
import { api } from "../lib/api";
import { auth } from "../lib/auth";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Label from "../components/ui/Label";

const USER_INACTIVITY_LIMIT = 60 * 1000;
const USER_WARNING_TIME = 30 * 1000;

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
  const [lastActivity, setLastActivity] = useState(Date.now());

  // Emit a signed event when voter dashboard is viewed
  useEffect(() => {
    emitUx("view_user_dashboard");
  }, []);

  useEffect(() => {
    const resetActivity = () => setLastActivity(Date.now());
    const events = ["mousemove", "keydown", "click"];
    events.forEach((e) => window.addEventListener(e, resetActivity));
    return () => events.forEach((e) => window.removeEventListener(e, resetActivity));
  }, []);
  


    useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - lastActivity;

      if (elapsed >= USER_INACTIVITY_LIMIT) {
        auth.clear(); // remove token
        setLogoutMessage("You have been logged out due to inactivity.");
        window.location.href = "/login";
      } else if (elapsed >= USER_WARNING_TIME) {
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
    const fallbackStatus: { data: { already_voted: boolean } } = { data: { already_voted: false } };
    Promise.all([
      api.get<BallotDetail>(`/ballots/${selected}`),
      api.get<{ already_voted: boolean }>(`/ballots/${selected}/status`).catch(() => fallbackStatus),
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
      emitUx("vote_submit", { ballot_id: selected, option_index: choice });
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
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-3xl font-semibold">Voter Dashboard</h2>
          <p className="text-sm text-muted">
            Review active ballots and cast your vote. Activity is monitored and you&apos;ll be logged out after one minute of inactivity.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            emitUx("logout_click", { role: "voter" });
            auth.clear();
            window.location.href = "/login";
          }}
        >
          Sign out
        </Button>
      </div>

      {error && <p className="text-sm font-medium text-red-500">{error}</p>}

      <Card className="p-6">
        <div className="grid gap-3 md:grid-cols-[220px_1fr] md:items-center">
          <div>
            <Label htmlFor="ballot-select">Select ballot</Label>
            <select
              id="ballot-select"
              value={selected ?? ""}
              onChange={(e) => setSelected(Number(e.target.value))}
              className="mt-1 w-full rounded-xl border border-border bg-card px-3 py-2 text-sm text-text transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
            >
              {ballots.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.title}
                </option>
              ))}
            </select>
          </div>
          <p className="text-sm text-muted">
            {detail
              ? "Choose your preferred option below. You can vote once per ballot."
              : "Select a ballot to view details and submit your vote."}
          </p>
        </div>
      </Card>

      {detail && (
        <Card className="p-6">
          <form className="space-y-5" onSubmit={submitVote}>
            <div>
              <h3 className="text-lg font-semibold">{detail.title}</h3>
              <p className="mt-1 text-sm text-muted">Options below reflect the current tally in real time.</p>
            </div>
            <div className="space-y-3">
              {detail.options.map((opt, idx) => (
                <label
                  key={opt}
                  className={[
                    "flex cursor-pointer items-center gap-4 rounded-xl border px-4 py-3 transition",
                    choice === idx ? "border-primary bg-primary/10" : "border-border bg-bg-elev",
                    hasVoted ? "cursor-not-allowed opacity-70" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                >
                  <input
                    type="radio"
                    name="choice"
                    value={idx}
                    disabled={hasVoted}
                    checked={choice === idx}
                    onChange={() => setChoice(idx)}
                    className="h-4 w-4 accent-primary"
                  />
                  <span>{opt}</span>
                </label>
              ))}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              {message && <p className="text-sm font-medium text-emerald-500">{message}</p>}
              <Button type="submit" loading={loading} disabled={loading || hasVoted}>
                {hasVoted ? "Already voted" : "Submit vote"}
              </Button>
            </div>
          </form>
        </Card>
      )}
      {logoutMessage && (
        <div className="fixed bottom-5 left-5 z-50 rounded-full border border-amber-400/70 bg-amber-100/90 px-4 py-2 text-sm text-amber-900 shadow-lg dark:border-amber-300/60 dark:bg-amber-200/90">
          {logoutMessage}
        </div>
      )}
    </div>
  );
}
