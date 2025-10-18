const API_BASE = 'http://127.0.0.1:8000';

export async function apiHealth() {
  const r = await fetch(`${API_BASE}/health`);
  return r.json();
}

export async function apiLogin(username, password) {
  const r = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!r.ok) throw new Error('Login failed');
  return r.json(); // { token: "dummy-token" }
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
