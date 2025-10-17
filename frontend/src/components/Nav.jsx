import { Link } from 'react-router-dom'

export default function Nav() {
  const navStyle = { display: 'flex', gap: 12, padding: 12, borderBottom: '1px solid #eee' }
  return (
    <nav style={navStyle}>
      <Link to="/">Home</Link>
      <Link to="/login">Login</Link>
      <Link to="/signup">Signup</Link>
      <Link to="/dashboard">Dashboard</Link>
    </nav>
  )
}
