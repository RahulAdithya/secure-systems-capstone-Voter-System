import React from 'react'
import { apiLogin } from '../api'

export default function Login() {
  const [username, setUsername] = React.useState('demo')
  const [password, setPassword] = React.useState('demo')
  const [result, setResult] = React.useState(null)
  const [error, setError] = React.useState(null)
  const [captchaToken, setCaptchaToken] = React.useState('')
  const [needsCaptcha, setNeedsCaptcha] = React.useState(false)
  const [failedAttempts, setFailedAttempts] = React.useState(0)
  const [isSubmitting, setIsSubmitting] = React.useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    setIsSubmitting(true)
    try {
      const tokenToSend = captchaToken.trim()
      const r = await apiLogin(username, password, tokenToSend || undefined)
      setResult(r)
      setNeedsCaptcha(false)
      setCaptchaToken('')
      setFailedAttempts(0)
      // later: store real token and navigate
    } catch (err) {
      let displayMessage = err?.message || 'Login failed'
      const detail = err?.detail
      if (detail && typeof detail === 'object') {
        if (detail.error === 'invalid_credentials') {
          const attempts = detail.failed_attempts ?? 0
          setFailedAttempts(attempts)
          displayMessage = attempts
            ? `Invalid username or password (failed attempts: ${attempts}).`
            : 'Invalid username or password.'
        }
      }
      if (detail === 'captcha_required_or_invalid' || displayMessage === 'captcha_required_or_invalid') {
        setNeedsCaptcha(true)
        setCaptchaToken('')
        displayMessage = 'Multiple failed attempts detected. Enter the CAPTCHA token to continue.'
      }
      setError(displayMessage)
    }
    setIsSubmitting(false)
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Login (Base)</h2>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12, maxWidth: 360 }}>
        <input value={username} onChange={e => setUsername(e.target.value)} placeholder="username" />
        <input value={password} onChange={e => setPassword(e.target.value)} placeholder="password" type="password" />
        {needsCaptcha && (
          <div style={{ display: 'grid', gap: 4 }}>
            <label htmlFor="captcha-token" style={{ fontSize: 14 }}>
              CAPTCHA token
            </label>
            <input
              id="captcha-token"
              value={captchaToken}
              onChange={e => setCaptchaToken(e.target.value)}
              placeholder="Enter CAPTCHA token"
            />
            <p style={{ margin: 0, fontSize: 12, color: '#555' }}>
              For local testing use the token configured on the backend (default: 1234).
            </p>
          </div>
        )}
        <button
          type="submit"
          disabled={isSubmitting || (needsCaptcha && !captchaToken.trim())}
        >
          {isSubmitting ? 'Logging in…' : 'Login'}
        </button>
      </form>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {failedAttempts > 0 && !needsCaptcha && (
        <p style={{ color: '#555' }}>Failed attempts: {failedAttempts}</p>
      )}
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  )
}
