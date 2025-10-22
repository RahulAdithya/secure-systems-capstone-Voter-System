import React, { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { isAxiosError } from "axios";

import { api } from "../lib/api";
import { auth } from "../lib/auth";
import { emitUx } from "../lib/ux";

type Step = "creds" | "captcha";

export default function Login(): React.ReactElement {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [step, setStep] = useState<Step>("creds");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [lockSeconds, setLockSeconds] = useState(0);
  const lastLockRef = useRef(0);

  const forceFailSuffix = useMemo(() => {
    const search = new URLSearchParams(window.location.search);
    const flag = search.get("force_fail");
    if (!flag) return "";
    return `?force_fail=${encodeURIComponent(flag)}`;
  }, []);

  useEffect(() => {
    if (lockSeconds <= 0) {
      return;
    }
    const timer = window.setInterval(() => {
      setLockSeconds((prev) => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [lockSeconds]);

  useEffect(() => {
    if (lockSeconds === 0 && lastLockRef.current > 0) {
      setError("");
    }
    lastLockRef.current = lockSeconds;
  }, [lockSeconds]);

  function readHeader(headers: unknown, name: string): string | undefined {
    if (!headers) return undefined;
    const record = headers as Record<string, unknown> & {
      get?: (key: string) => string | null;
    };
    const lower = name.toLowerCase();
    if (typeof record.get === "function") {
      return record.get(name) ?? record.get(lower) ?? undefined;
    }
    const lowerValue = record[lower];
    if (typeof lowerValue === "string") return lowerValue;
    const value = record[name];
    return typeof value === "string" ? value : undefined;
  }

  async function refreshCaptchaStatus(email: string) {
    if (!email) return;
    try {
      const { data } = await api.get("/auth/captcha/status", { params: { email } });
      if (data?.captcha_required) {
        setStep("captcha");
      } else {
        setStep("creds");
      }
    } catch {
      // Ignore errors; UI stays on the previous step.
    }
  }

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    if (lockSeconds > 0) {
      return;
    }
    setError("");
    setLoading(true);
    const body: Record<string, string> = { email: identifier, password };
    if (captcha) body.captcha_token = captcha;

    try {
      const { data } = await api.post(`/auth/login${forceFailSuffix}`, body);
      auth.set(data.access_token);
      auth.setRole("voter");
      // Emit signed UX event post-login
      emitUx("login_success", { role: "voter" });
      window.location.href = "/";
    } catch (err) {
      let detail: unknown = null;
      let status = 0;
      let data: unknown;
      if (isAxiosError(err)) {
        status = err.response?.status ?? 0;
        data = err.response?.data;
        detail = err.response?.data?.detail ?? null;
      }

      const captchaHeader = readHeader(
        isAxiosError(err) ? err.response?.headers : undefined,
        "X-Captcha-Required",
      );
      if (captchaHeader === "true") {
        setStep("captcha");
      }

      if (status === 429 && data && typeof data === "object" && "error" in data) {
        const locked = data as { error?: string; retry_after?: number };
        if (locked.error === "locked") {
          const seconds = Number(locked.retry_after);
          const normalized = Number.isFinite(seconds) && seconds > 0 ? Math.round(seconds) : 30;
          setLockSeconds(normalized);
          setError("Too many attempts. Try again later.");
          await refreshCaptchaStatus(identifier);
          return;
        }
      }

      if (detail === "captcha_required_or_invalid" || captchaHeader === "true") {
        setStep("captcha");
        setError("CAPTCHA required before continuing.");
      } else if (
        detail &&
        typeof detail === "object" &&
        "error" in (detail as Record<string, unknown>)
      ) {
        setError("Invalid credentials.");
      } else if (
        status === 401 &&
        data &&
        typeof data === "object" &&
        "error" in (data as Record<string, unknown>)
      ) {
        setError("Invalid credentials.");
      } else {
        setError("Login failed.");
      }
      await refreshCaptchaStatus(identifier);
    } finally {
      setLoading(false);
    }
  }

  const countdownMessage =
    lockSeconds > 0
      ? `Too many attempts. Try again in ${lockSeconds} second${lockSeconds === 1 ? "" : "s"}.`
      : "";
  const displayError = countdownMessage || error;

  return (
    <div style={{ maxWidth: 420, margin: "3rem auto", fontFamily: "system-ui" }}>
      <h2>User Login</h2>
      <form onSubmit={handleLogin} style={{ display: "grid", gap: "0.75rem" }}>
        {(step === "creds" || step === "captcha") && (
          <>
            <label>
              Email or username
              <input
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                style={{ width: "100%", marginTop: "0.25rem" }}
                autoComplete="username"
                disabled={loading || lockSeconds > 0}
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ width: "100%", marginTop: "0.25rem" }}
                autoComplete="current-password"
                disabled={loading || lockSeconds > 0}
              />
            </label>
            {step === "captcha" && (
              <label>
                CAPTCHA token
                <input
                  value={captcha}
                  onChange={(e) => setCaptcha(e.target.value)}
                  style={{ width: "100%", marginTop: "0.25rem" }}
                  disabled={loading || lockSeconds > 0}
                />
                <small>Enter the token configured on the backend (default: 1234).</small>
              </label>
            )}
          </>
        )}

        {displayError && <p style={{ color: "crimson" }}>{displayError}</p>}
        <button type="submit" disabled={loading || lockSeconds > 0} style={{ padding: "0.6rem 1rem" }}>
          Continue
        </button>
      </form>
      <div style={{ marginTop: "1.5rem" }}>
        <a href="/signup">Create account</a>
      </div>
      <div style={{ marginTop: "0.75rem" }}>
        <a href="/admin-login">Admin login</a>
      </div>
    </div>
  );
}
