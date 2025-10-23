import React, { FormEvent, useState } from "react";
import QRCode from "qrcode.react";
import { isAxiosError } from "axios";

import { api } from "../lib/api";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Input from "../components/ui/Input";
import Label from "../components/ui/Label";

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
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      <div>
        <h1 className="text-3xl font-semibold">MFA Enrollment</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Secure the administrator account with TOTP multi-factor authentication. Scan the QR code with your authenticator app
          and store the backup codes in a safe place.
        </p>
      </div>
      <Card className="p-8">
        <form className="grid gap-4 md:grid-cols-2" onSubmit={enroll} noValidate>
          <div className="md:col-span-2 grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="mfa-email">Admin email</Label>
              <Input
                id="mfa-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
              />
            </div>
            <div>
              <Label htmlFor="mfa-password">Password</Label>
              <Input
                id="mfa-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </div>
          {error && <p className="md:col-span-2 text-sm font-medium text-red-500">{error}</p>}
          <div className="md:col-span-2 flex items-center justify-end">
            <Button type="submit" loading={loading} disabled={loading}>
              Enroll
            </Button>
          </div>
        </form>
      </Card>
      {uri && (
        <Card className="p-8">
          <div className="grid gap-6 md:grid-cols-[200px_1fr]">
            <div className="flex items-center justify-center rounded-2xl border border-border bg-bg-elev p-4">
              <QRCode value={uri} size={160} />
            </div>
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold">Authenticator setup</h3>
                <p className="text-sm text-muted">Scan the QR code or copy the URI below to add the account manually.</p>
              </div>
              <pre className="overflow-x-auto rounded-xl border border-border bg-bg-elev p-3 text-sm">{uri}</pre>
              <div>
                <h3 className="text-lg font-semibold">Backup codes</h3>
                <p className="text-sm text-muted">Each code can be used once if you lose access to your authenticator app.</p>
                <ul className="mt-2 grid grid-cols-2 gap-2 text-sm font-mono md:grid-cols-3">
                  {codes.map((code) => (
                    <li key={code} className="rounded-lg border border-border bg-bg-elev px-3 py-2 text-center">
                      {code}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
