import React from 'react'
import { apiLogin } from '../api'

export default function Login() {
  const [username, setUsername] = React.useState('demo')
  const [password, setPassword] = React.useState('demo')
  const [result, setResult] = React.useState(null)
  const [error, setError] = React.useState(null)

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    try {
      const r = await apiLogin(username, password)
      setResult(r)
      // later: store real token and navigate
    } catch (err) {
      setError(err.message)
    }
  }

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
    </div>
  )
}
