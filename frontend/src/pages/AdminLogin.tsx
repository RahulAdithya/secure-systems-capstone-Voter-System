import React, { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { isAxiosError } from "axios";

import { api } from "../lib/api";
import { auth } from "../lib/auth";
import { emitUx } from "../lib/ux";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Label from "../components/ui/Label";

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

  async function refreshCaptchaStatus(currentEmail: string) {
    if (!currentEmail) return;
    try {
      const { data } = await api.get("/auth/captcha/status", { params: { email: currentEmail } });
      const required = Boolean(data?.captcha_required);
      setStep((prev) => {
        if (required) return "captcha";
        if (prev === "captcha") return "creds";
        return prev;
      });
    } catch {
      // Ignore failures; form state remains unchanged.
    }
  }

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    if (lockSeconds > 0) {
      return;
    }
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
      const { data } = await api.post(`/auth/login${forceFailSuffix}`, body);
      auth.set(data.access_token);
      auth.setRole("admin");
      // Emit signed UX event post-login
      emitUx("login_success", { role: "admin" });
      window.location.href = "/";
    } catch (err) {
      let detail: unknown = null;
      let status = 0;
      let payload: unknown;
      if (isAxiosError(err)) {
        status = err.response?.status ?? 0;
        payload = err.response?.data;
        detail = err.response?.data?.detail ?? null;
      }

      if (status === 422) {
        setStep("creds");
        setError("Enter valid details.");
        await refreshCaptchaStatus(email);
        return;
      }

      const captchaHeader = readHeader(
        isAxiosError(err) ? err.response?.headers : undefined,
        "X-Captcha-Required",
      );
      if (captchaHeader === "true") {
        setStep("captcha");
      }

      if (status === 429 && payload && typeof payload === "object" && "error" in payload) {
        const locked = payload as { error?: string; retry_after?: number };
        if (locked.error === "locked") {
          const seconds = Number(locked.retry_after);
          const normalized = Number.isFinite(seconds) && seconds > 0 ? Math.round(seconds) : 30;
          setLockSeconds(normalized);
          setError("Too many attempts. Try again later.");
          await refreshCaptchaStatus(email);
          return;
        }
      }

      if (detail === "mfa_required") {
        setStep("mfa");
        setError("Multi-factor authentication required. Enter an OTP or backup code.");
      } else if (detail === "captcha_required_or_invalid") {
        setStep("captcha");
        setError("CAPTCHA required before continuing.");
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
      } else if (
        status === 401 &&
        payload &&
        typeof payload === "object" &&
        "error" in (payload as Record<string, unknown>)
      ) {
        setError("Invalid credentials.");
      } else {
        setError("Login failed.");
      }
      await refreshCaptchaStatus(email);
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
    <div className="grid min-h-[70vh] place-items-center">
      <Card className="w-full max-w-md p-8">
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold">Admin Login</h2>
            <p className="mt-2 text-sm text-muted">
              Secure access for administrators. You&apos;ll need your password plus a second factor when prompted.
            </p>
          </div>
          <form className="space-y-4" onSubmit={handleLogin} noValidate>
            {(step === "creds" || step === "captcha") && (
              <>
                <div>
                  <Label htmlFor="admin-email">Email</Label>
                  <Input
                    id="admin-email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="username"
                    disabled={loading || lockSeconds > 0}
                    placeholder="admin@evp-demo.com"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="admin-password">Password</Label>
                  <Input
                    id="admin-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    disabled={loading || lockSeconds > 0}
                    required
                  />
                </div>
                {step === "captcha" && (
                  <div>
                    <Label htmlFor="admin-captcha">Captcha token</Label>
                    <Input
                      id="admin-captcha"
                      value={captcha}
                      onChange={(e) => setCaptcha(e.target.value)}
                      disabled={loading || lockSeconds > 0}
                      placeholder="Enter the configured code"
                      required
                    />
                    <p className="mt-2 text-xs text-muted">Enter the token configured on the backend (default: 1234).</p>
                  </div>
                )}
              </>
            )}

            {step === "mfa" && (
              <div className="space-y-4">
                <div>
                  <Label htmlFor="admin-otp">One-time password</Label>
                  <Input
                    id="admin-otp"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="123456"
                    inputMode="numeric"
                    disabled={loading || lockSeconds > 0}
                  />
                </div>
                <div className="text-center text-xs uppercase tracking-wide text-muted">or</div>
                <div>
                  <Label htmlFor="admin-backup">Backup code</Label>
                  <Input
                    id="admin-backup"
                    value={backup}
                    onChange={(e) => setBackup(e.target.value.toUpperCase())}
                    placeholder="AAAA-BBBB"
                    disabled={loading || lockSeconds > 0}
                  />
                </div>
              </div>
            )}

            {displayError && <p className="text-sm font-medium text-red-500">{displayError}</p>}
            <Button type="submit" loading={loading} disabled={loading || lockSeconds > 0} className="w-full">
              {step === "mfa" ? "Verify MFA" : "Continue"}
            </Button>
          </form>
          <div className="flex flex-col gap-2 text-sm">
            <a className="text-primary hover:underline" href="/mfa-enroll">
              Enroll MFA
            </a>
            <a className="text-primary hover:underline" href="/login">
              User login
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
}
