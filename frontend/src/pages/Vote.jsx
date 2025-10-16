import React from 'react'
import { useParams } from 'react-router-dom'
import { apiBallot, apiVote } from '../api'

export default function Vote() {
  const { id } = useParams()
  const ballotId = Number(id)
  const [ballot, setBallot] = React.useState(null)
  const [message, setMessage] = React.useState(null)

  React.useEffect(() => {
    apiBallot(ballotId).then(setBallot)
  }, [ballotId])

  async function cast(idx) {
    const r = await apiVote(ballotId, idx)
    setMessage(`Voted option #${idx} → new total: ${r.new_total}`)
    const fresh = await apiBallot(ballotId)
    setBallot(fresh)
  }

  if (!ballot) return <div style={{ padding: 16 }}>Loading…</div>

  return (
    <div style={{ padding: 16 }}>
      <h2>{ballot.title}</h2>
      <ul>
        {ballot.options.map((opt, idx) => (
          <li key={idx} style={{ marginBottom: 8 }}>
            {opt} <button onClick={() => cast(idx)}>Vote</button>
          </li>
        ))}
      </ul>
      <p>Total votes: {ballot.totalVotes}</p>
      {message && <p>{message}</p>}
    </div>
  )
}
