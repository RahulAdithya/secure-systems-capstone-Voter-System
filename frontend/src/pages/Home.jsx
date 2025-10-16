import React from 'react'
import { apiHealth } from '../api'

export default function Home() {
  const [status, setStatus] = React.useState(null)

  React.useEffect(() => {
    apiHealth().then(setStatus).catch(() => setStatus({ ok: false }))
  }, [])

  return (
    <div style={{ padding: 16 }}>
      <h2>Electronic Voting Platform (Base)</h2>
      <p>Backend health: {status ? JSON.stringify(status) : 'Loading...'}</p>
      <p>This is the base UI. No security is implemented yet.</p>
    </div>
  )
}
