import { Navigate, Outlet } from 'react-router-dom'
import { useMe } from './queries'

/**
 * Route guard for the staff pages. This only spares other people a dead-end page: the real
 * protection is on the server, which answers every /api/staff/ request from a non-superuser
 * with 403 whatever the website shows.
 */
export default function RequireSuperuser() {
  const me = useMe()
  if (me.isLoading) {
    return (
      <p className="status" role="status">
        Loading…
      </p>
    )
  }
  if (!me.data?.is_superuser) return <Navigate to="/" replace />
  return <Outlet />
}
