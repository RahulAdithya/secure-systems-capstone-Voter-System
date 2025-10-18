import React, { useEffect } from 'react'
import { apiLogin } from '../api'
import { resetAutoLogout,loginWithAutoLogout } from '../authWithAutoLogout.js';

export default function Login() {
  const [username, setUsername] = React.useState('demo')
  const [password, setPassword] = React.useState('demo')
  const [result, setResult] = React.useState(null)
  const [error, setError] = React.useState(null)
  const [message, setMessage] = React.useState("")  

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      // const r = await apiLogin(username, password)
      const r = await loginWithAutoLogout(username, password, setMessage);
      
      setResult(r)
      setMessage("✅ Login successful! Timer started.");
      // later: store real token and navigate
    } catch (err) {
      setError(err.message)
    }
  }

  // Reset auto-logout timer on user activity
  useEffect(() => {
    const reset = () => resetAutoLogout(setMessage); // optional: call resetAutoLogout
    window.addEventListener("mousemove", reset);
    window.addEventListener("keydown", reset);
    window.addEventListener("click", reset);
    window.addEventListener("scroll", reset);
    return () => {
      window.removeEventListener("mousemove", reset);
      window.removeEventListener("keydown", reset);
      window.removeEventListener("click", reset);
      window.removeEventListener("scroll", reset);
    };
  }, []); // run once after mount

  return (
    <div style={{ padding: 16 }}>
      <h2>Login (Base)</h2>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 8, maxWidth: 320 }}>
        <input value={username} onChange={e => setUsername(e.target.value)} placeholder="username" />
        <input value={password} onChange={e => setPassword(e.target.value)} placeholder="password" type="password" />
        <button type="submit">Login</button>
      </form>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
      {message && <p style={{ color: 'green' }}>{message}</p>}
    </div>
  )
}
