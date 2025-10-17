import React from 'react'
import { apiSignup } from '../api'

const helpStyle = { fontSize: 12, color: '#555' }

function validateClient({ username, email, password }) {
  const errors = {}
  // username: 3–32, alnum + underscore, start alnum, no surrounding spaces
  if (!username || username.length < 3 || username.length > 32) {
    errors.username = 'Username must be 3-32 characters'
  } else if (username.trim() !== username) {
    errors.username = 'Username must not have surrounding spaces'
  } else if (!/^[A-Za-z0-9][A-Za-z0-9_]*$/.test(username)) {
    errors.username = 'Only letters, digits, underscore; start with letter/digit'
  }
  // email basic check; server enforces EmailStr
  if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
    errors.email = 'Enter a valid email address'
  }
  // password: 8–128, one lower/upper/digit/special, no control, no surrounding spaces
  if (!password || password.length < 8 || password.length > 128) {
    errors.password = 'Password must be 8-128 characters'
  } else if (password.trim() !== password) {
    errors.password = 'Password must not have surrounding spaces'
  } else if (!/[a-z]/.test(password)) {
    errors.password = 'Include a lowercase letter'
  } else if (!/[A-Z]/.test(password)) {
    errors.password = 'Include an uppercase letter'
  } else if (!/\d/.test(password)) {
    errors.password = 'Include a digit'
  } else if (!/[^A-Za-z0-9]/.test(password)) {
    errors.password = 'Include a special character'
  }
  return errors
}

export default function Signup() {
  const [username, setUsername] = React.useState('')
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [errors, setErrors] = React.useState({})
  const [serverError, setServerError] = React.useState(null)
  const [created, setCreated] = React.useState(null)
  const [submitting, setSubmitting] = React.useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setServerError(null)
    const payload = { username, email, password }
    const errs = validateClient(payload)
    setErrors(errs)
    if (Object.keys(errs).length > 0) return
    try {
      setSubmitting(true)
      const res = await apiSignup(payload)
      setCreated(res)
    } catch (err) {
      setServerError(err.message || 'Signup failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ padding: 16, maxWidth: 480 }}>
      <h2>Create Account</h2>
      <p style={helpStyle}>
        Strong input validation is enforced client-side and server-side to prevent malformed data.
        The server also uses parameterized ORM queries and Argon2 hashing to prevent SQL injection and protect passwords.
      </p>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 10 }} noValidate>
        <label>
          Username
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="alice_01" />
        </label>
        {errors.username && <div style={{ color: 'crimson' }}>{errors.username}</div>}

        <label>
          Email
          <input value={email} onChange={e => setEmail(e.target.value)} placeholder="alice@example.com" type="email" />
        </label>
        {errors.email && <div style={{ color: 'crimson' }}>{errors.email}</div>}

        <label>
          Password
          <input value={password} onChange={e => setPassword(e.target.value)} placeholder="S3cure!Pass" type="password" />
        </label>
        <div style={helpStyle}>Min 8 chars with lower, upper, digit, and special character. No spaces at ends.</div>
        {errors.password && <div style={{ color: 'crimson' }}>{errors.password}</div>}

        <button type="submit" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create account'}
        </button>
      </form>

      {serverError && <p style={{ color: 'crimson', marginTop: 8 }}>{serverError}</p>}
      {created && (
        <div style={{ marginTop: 12 }}>
          <h4>Account Created</h4>
          <pre>{JSON.stringify(created, null, 2)}</pre>
        </div>
      )}
    </div>
  )}

