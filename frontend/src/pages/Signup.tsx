import React, { FormEvent, useState } from "react";
import { isAxiosError } from "axios";

import { api } from "../lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Label from "../components/ui/Label";

function validateUsername(v: string): string | null {
  const trimmed = v.trim();
  if (trimmed !== v) return "Username must not have surrounding spaces";
  if (!/^[A-Za-z0-9][A-Za-z0-9_]*$/.test(v)) {
    return "Use letters, digits and underscores, starting with a letter/digit";
  }
  if (v.length < 3 || v.length > 32) return "Username must be 3-32 characters";
  return null;
}

function validatePassword(v: string): string | null {
  if (v.length < 8 || v.length > 128) return "Password must be 8-128 characters";
  if (v.trim() !== v) return "Password must not have surrounding spaces";
  if ([...v].some((ch) => ch < " ")) return "Password cannot contain control characters";
  if (!/[a-z]/.test(v)) return "Include a lowercase letter";
  if (!/[A-Z]/.test(v)) return "Include an uppercase letter";
  if (!/\d/.test(v)) return "Include a digit";
  if (!/[^A-Za-z0-9]/.test(v)) return "Include a special character";
  return null;
}

export default function Signup(): React.ReactElement {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  function validateAll(): string | null {
    if (!email) return "Email is required";
    // Simple email shape check; server does strict validation
    if (!/.+@.+\..+/.test(email)) return "Enter a valid email";
    const u = validateUsername(username);
    if (u) return u;
    const p = validatePassword(password);
    if (p) return p;
    if (password !== confirm) return "Passwords do not match";
    return null;
  }

  async function handleSignup(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    const v = validateAll();
    if (v) {
      setError(v);
      return;
    }
    setLoading(true);
    try {
      const { status } = await api.post("/auth/signup", {
        username,
        email,
        password,
      });
      if (status === 201) {
        setSuccess("Account created. Redirecting to login...");
        setTimeout(() => {
          window.location.href = "/login";
        }, 900);
      }
    } catch (err) {
      if (isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        if (detail === "username_or_email_already_exists") {
          setError("Username or email already exists");
        } else if (detail === "reserved_identity") {
          setError("This username/email is reserved and cannot be used");
        } else if (typeof detail === "string") {
          setError(detail);
        } else if (detail && typeof detail === "object") {
          // Pydantic validation errors may come structured
          setError("Validation failed. Please check your inputs.");
        } else {
          setError("Signup failed. Try again.");
        }
      } else {
        setError("Signup failed. Try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-[70vh] place-items-center">
      <Card className="w-full max-w-lg p-8">
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold">Create Account</h2>
            <p className="mt-2 text-sm text-muted">
              Register to vote in the demo environment. Your credentials are stored securely with hashed passwords.
            </p>
          </div>
          <form className="space-y-4" onSubmit={handleSignup} noValidate>
            <div>
              <Label htmlFor="signup-username">Username</Label>
              <Input
                id="signup-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="your_name"
                autoComplete="username"
                required
              />
            </div>
            <div>
              <Label htmlFor="signup-email">Email</Label>
              <Input
                id="signup-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
                type="email"
              />
            </div>
            <div>
              <Label htmlFor="signup-password">Password</Label>
              <Input
                id="signup-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Strong password"
                autoComplete="new-password"
                required
              />
            </div>
            <div>
              <Label htmlFor="signup-confirm">Confirm password</Label>
              <Input
                id="signup-confirm"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="Repeat password"
                autoComplete="new-password"
                required
              />
            </div>
            <p className="text-xs text-muted">
              Password must be 8–128 characters and include uppercase, lowercase, digits, and a special symbol.
            </p>

            {error && <p className="text-sm font-medium text-red-500">{error}</p>}
            {success && <p className="text-sm font-medium text-emerald-500">{success}</p>}

            <Button type="submit" loading={loading} disabled={loading} className="w-full">
              Create account
            </Button>
          </form>
          <div className="text-sm">
            <a className="text-primary hover:underline" href="/login">
              Back to login
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
}
