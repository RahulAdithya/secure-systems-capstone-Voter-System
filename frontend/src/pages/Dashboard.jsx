import React from 'react'
import { apiMe, apiBallots } from '../api'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [me, setMe] = React.useState(null)
  const [ballots, setBallots] = React.useState([])

  React.useEffect(() => {
    apiMe().then(setMe)
    apiBallots().then(setBallots)
  }, [])

  return (
    <div style={{ padding: 16 }}>
      <h2>Dashboard</h2>
      <p>User: {me ? `${me.full_name} (@${me.username})` : 'Loading...'}</p>
      <h3>Open Ballots</h3>
      <ul>
        {ballots.map(b => (
          <li key={b.id}>
            <Link to={`/vote/${b.id}`}>{b.title}</Link> — total votes: {b.totalVotes}
          </li>
        ))}
      </ul>
    </div>
  )
}
