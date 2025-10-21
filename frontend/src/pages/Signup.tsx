import React, { FormEvent, useState } from "react";
import { isAxiosError } from "axios";

import { api } from "../lib/api";

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
    <div style={{ maxWidth: 460, margin: "3rem auto", fontFamily: "system-ui" }}>
      <h2>Create Account</h2>
      <form onSubmit={handleSignup} style={{ display: "grid", gap: "0.75rem" }}>
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="your_name"
            style={{ width: "100%", marginTop: "0.25rem" }}
            autoComplete="username"
          />
        </label>
        <label>
          Email
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            style={{ width: "100%", marginTop: "0.25rem" }}
            autoComplete="email"
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Strong password"
            style={{ width: "100%", marginTop: "0.25rem" }}
            autoComplete="new-password"
          />
        </label>
        <label>
          Confirm password
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="Repeat password"
            style={{ width: "100%", marginTop: "0.25rem" }}
            autoComplete="new-password"
          />
        </label>
        <small style={{ color: "#666" }}>
          Password must be 8–128 chars and include upper, lower, digit, and special.
        </small>

        {error && <p style={{ color: "crimson" }}>{error}</p>}
        {success && <p style={{ color: "seagreen" }}>{success}</p>}

        <button type="submit" disabled={loading} style={{ padding: "0.6rem 1rem" }}>
          Create account
        </button>
      </form>
      <div style={{ marginTop: "1.5rem" }}>
        <a href="/login">Back to login</a>
      </div>
    </div>
  );
}
