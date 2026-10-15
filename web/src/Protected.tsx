import { Link, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { isAuthError, logout } from './auth'
import { Moon, Sun } from './Icons'
import Logo, { LogoMark } from './Logo'
import { useTrees } from './queries'
import { useTheme } from './theme'

/** Session gate: the trees request doubles as the "am I signed in?" probe. */
export default function Protected() {
  const { isLoading, error } = useTrees()
  const qc = useQueryClient()
  const nav = useNavigate()
  const { theme, toggle } = useTheme()

  if (isLoading) {
    return (
      <div className="splash" role="status" aria-label="Loading">
        <LogoMark size={56} />
      </div>
    )
  }
  if (isAuthError(error)) return <Navigate to="/login" replace />

  return (
    <>
      <header className="topbar">
        <Link to="/" aria-label="Kinship home" style={{ textDecoration: 'none' }}>
          <Logo />
        </Link>
        <div className="topbar-actions">
          <button
            className="ghost icon-btn"
            onClick={toggle}
            aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            title={theme === 'dark' ? 'Light theme' : 'Dark theme'}
          >
            {theme === 'dark' ? <Sun /> : <Moon />}
          </button>
          <button
            className="ghost"
            onClick={async () => {
              await logout().catch(() => undefined)
              qc.clear()
              nav('/login')
            }}
          >
            Sign out
          </button>
        </div>
      </header>
      <div className="content">
        <Outlet />
      </div>
    </>
  )
}
