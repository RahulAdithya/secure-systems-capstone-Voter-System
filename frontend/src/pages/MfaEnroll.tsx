import React, { FormEvent, useState } from "react";
import QRCode from "qrcode.react";
import { isAxiosError } from "axios";

import { api } from "../lib/api";

export default function MfaEnroll(): React.ReactElement {
  const [email, setEmail] = useState("admin@evp-demo.com");
  const [password, setPassword] = useState("secret123");
  const [uri, setUri] = useState<string | null>(null);
  const [codes, setCodes] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function enroll(event: FormEvent) {
    event.preventDefault();
    setError("");
    setUri(null);
    setCodes([]);
    setLoading(true);
    try {
      const { data } = await api.post("/auth/mfa/enroll", { email, password });
      setUri(data.otpauth_uri);
      setCodes(Array.isArray(data.backup_codes) ? data.backup_codes : []);
    } catch (err) {
      if (isAxiosError(err)) {
        const detail = err.response?.data?.detail;
        setError(typeof detail === "string" ? detail : "Enroll failed");
      } else {
        setError("Enroll failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "3rem auto", fontFamily: "system-ui" }}>
      <h1>MFA Enrollment</h1>
      <form onSubmit={enroll} style={{ display: "grid", gap: "0.75rem", maxWidth: 420 }}>
        <label>
          Admin email
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: "100%", marginTop: "0.25rem" }}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", marginTop: "0.25rem" }}
          />
        </label>
        <button type="submit" disabled={loading} style={{ padding: "0.6rem 1rem", maxWidth: 180 }}>
          {loading ? "Enrolling..." : "Enroll"}
        </button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      {uri && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Scan in Google Authenticator</h3>
          <QRCode value={uri} size={180} />
          <pre style={{ wordBreak: "break-all", background: "#f5f5f5", padding: "1rem" }}>{uri}</pre>
          <h3>Backup Codes</h3>
          <p>Store these codes somewhere safe. Each one can be used exactly once.</p>
          <ul>
            {codes.map((code) => (
              <li key={code}>
                <code>{code}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
