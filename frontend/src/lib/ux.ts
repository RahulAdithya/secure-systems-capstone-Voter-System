import { api } from "./api";
import { auth } from "./auth";

function ensureSid(): string {
  let sid = localStorage.getItem("sid");
  if (!sid) {
    // Prefer crypto.randomUUID if available
    const cryptoObj: Crypto | undefined = globalThis.crypto;
    const gen = cryptoObj?.randomUUID
      ? cryptoObj.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    sid = gen;
    localStorage.setItem("sid", sid);
  }
  return sid;
}

export async function emitUx(name: string, details?: Record<string, unknown>): Promise<void> {
  try {
    const token = auth.get();
    if (!token) return; // require signed (authenticated) events only
    const sid = ensureSid();
    const ts = new Date().toISOString();
    await api.post("/auth/ux", { name, sid, ts, details });
  } catch {
    // Best-effort fire-and-forget; ignore failures
  }
}
