const API_BASE = 'http://127.0.0.1:8000';

export async function apiHealth() {
  const r = await fetch(`${API_BASE}/health`);
  return r.json();
}

export async function apiLogin(username, password, captchaToken) {
  const r = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      username,
      password,
      ...(captchaToken ? { captcha_token: captchaToken } : {})
    })
  });
  const text = await r.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch (parseError) {
      data = null;
    }
  }
  if (!r.ok) {
    const detail = data?.detail;
    const message = typeof detail === 'string'
      ? detail
      : detail?.error || 'Login failed';
    const error = new Error(message);
    error.status = r.status;
    error.detail = detail;
    error.body = data;
    throw error;
  }
  return data; // { access_token: "...", token_type: "bearer" }
}

export async function apiSignup({ username, email, password }) {
  const r = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
  const body = await r.json().catch(() => ({}))
  if (!r.ok) {
    const msg = (body && (body.detail?.message || body.detail)) || `Signup failed (${r.status})`
    throw new Error(typeof msg === 'string' ? msg : 'Signup failed')
  }
  return body
}

export async function apiMe() {
  const r = await fetch(`${API_BASE}/users/me`);
  return r.json();
}

export async function apiBallots() {
  const r = await fetch(`${API_BASE}/ballots`);
  return r.json();
}

export async function apiBallot(id) {
  const r = await fetch(`${API_BASE}/ballots/${id}`);
  return r.json();
}

export async function apiVote(id, optionIndex) {
  const r = await fetch(`${API_BASE}/ballots/${id}/vote`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ option_index: optionIndex })
  });
  if (!r.ok) throw new Error('Vote failed');
  return r.json();
}
