import { useState } from 'react'
import { Link, Navigate, Outlet, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { isAuthError, logout } from './auth'
import { CreateFamilyDialog, JoinFamilyDialog } from './FamilyDialogs'
import { Moon, Plus, Sun, Users } from './Icons'
import Logo, { LogoMark } from './Logo'
import { useTrees } from './queries'
import { useTheme } from './theme'

/** What pages under this layout can ask the top bar to do. */
export interface ShellContext {
  openCreate: () => void
  openJoin: () => void
}

/** Session gate: the trees request doubles as the "am I signed in?" probe. */
export default function Protected() {
  const { isLoading, error } = useTrees()
  const qc = useQueryClient()
  const nav = useNavigate()
  const { theme, toggle } = useTheme()
  const [dialog, setDialog] = useState<'create' | 'join' | null>(null)

  if (isLoading) {
    return (
      <div className="splash" role="status" aria-label="Loading">
        <LogoMark size={56} />
      </div>
    )
  }
  if (isAuthError(error)) return <Navigate to="/login" replace />

  const ctx: ShellContext = { openCreate: () => setDialog('create'), openJoin: () => setDialog('join') }

  return (
    <>
      <header className="topbar">
        <Link to="/" aria-label="Kinship home" style={{ textDecoration: 'none' }}>
          <Logo />
        </Link>
        <div className="topbar-actions">
          <button className="ghost" onClick={ctx.openJoin} title="Join a family with a code">
            <Users size={16} /> <span className="label">Join with a code</span>
          </button>
          <button onClick={ctx.openCreate} title="Create a family">
            <Plus size={16} /> <span className="label">Create a family</span>
          </button>
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
        <Outlet context={ctx} />
      </div>
      {dialog === 'create' && <CreateFamilyDialog onClose={() => setDialog(null)} />}
      {dialog === 'join' && <JoinFamilyDialog onClose={() => setDialog(null)} />}
    </>
  )
}
