import React, { FormEvent, useState } from "react";
import { isAxiosError } from "axios";

import { api } from "../lib/api";
import { auth } from "../lib/auth";

type Step = "creds" | "mfa" | "captcha";

export default function AdminLogin(): React.ReactElement {
  const [email, setEmail] = useState("admin@evp-demo.com");
  const [password, setPassword] = useState("secret123");
  const [otp, setOtp] = useState("");
  const [backup, setBackup] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [step, setStep] = useState<Step>("creds");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const body: Record<string, string> = { email, password };
    if (step === "mfa") {
      if (otp) body.otp = otp;
      if (backup) body.backup_code = backup;
    }
    if (captcha) {
      body.captcha_token = captcha;
    }

    try {
      const { data } = await api.post("/auth/login", body);
      auth.set(data.access_token);
      auth.setRole("admin");
      window.location.href = "/";
    } catch (err) {
      let detail: unknown = null;
      if (isAxiosError(err)) {
        detail = err.response?.data?.detail ?? null;
      }

      if (detail === "mfa_required") {
        setStep("mfa");
        setError("Multi-factor authentication required. Enter an OTP or backup code.");
      } else if (detail === "captcha_required_or_invalid") {
        setStep("captcha");
        setError("CAPTCHA required.");
      } else if (detail === "invalid_otp") {
        setError("Invalid OTP.");
      } else if (detail === "invalid_backup_code") {
        setError("Invalid backup code.");
      } else if (
        detail &&
        typeof detail === "object" &&
        "error" in (detail as Record<string, unknown>)
      ) {
        setError("Invalid credentials.");
      } else {
        setError("Login failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "3rem auto", fontFamily: "system-ui" }}>
      <h2>Admin Login</h2>
      <form onSubmit={handleLogin} style={{ display: "grid", gap: "0.75rem" }}>
        {(step === "creds" || step === "captcha") && (
          <>
            <label>
              Email
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ width: "100%", marginTop: "0.25rem" }}
                autoComplete="username"
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
              />
            </label>
            {step === "captcha" && (
              <label>
                CAPTCHA token
                <input
                  value={captcha}
                  onChange={(e) => setCaptcha(e.target.value)}
                  style={{ width: "100%", marginTop: "0.25rem" }}
                />
                <small>Enter the token configured on the backend (default: 1234).</small>
              </label>
            )}
          </>
        )}

        {step === "mfa" && (
          <>
            <label>
              One-Time Password
              <input
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="123456"
                style={{ width: "100%", marginTop: "0.25rem" }}
              />
            </label>
            <div style={{ textAlign: "center", color: "#666" }}>or</div>
            <label>
              Backup code
              <input
                value={backup}
                onChange={(e) => setBackup(e.target.value.toUpperCase())}
                placeholder="Backup code"
                style={{ width: "100%", marginTop: "0.25rem", textTransform: "uppercase" }}
              />
            </label>
          </>
        )}

        {error && <p style={{ color: "crimson" }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ padding: "0.6rem 1rem" }}>
          {step === "mfa" ? "Verify MFA" : "Continue"}
        </button>
      </form>
      <div style={{ marginTop: "1.5rem" }}>
        <a href="/mfa-enroll">Enroll MFA</a>
      </div>
      <div style={{ marginTop: "0.75rem" }}>
        <a href="/login">User login</a>
      </div>
    </div>
  );
}
