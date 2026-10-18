import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { isAuthError, logout } from './auth'
import { CreateFamilyDialog, JoinFamilyDialog } from './FamilyDialogs'
import { Moon, Plus, Sun, Users } from './Icons'
import Logo, { LogoMark } from './Logo'
import { AccountAvatar } from './ProfilePage'
import { useMe, useTrees } from './queries'
import { useTheme } from './theme'

/** What pages under this layout can ask the top bar to do. */
export interface ShellContext {
  openCreate: () => void
  openJoin: () => void
}

/** Session gate: the trees request doubles as the "am I signed in?" probe. */
export default function Protected() {
  const { isLoading, error } = useTrees()
  const me = useMe()
  const qc = useQueryClient()
  const nav = useNavigate()
  // Create / Join belong to the families list. Inside a family they would only be in the way.
  const onFamiliesPage = useLocation().pathname === '/'
  const { theme, toggle } = useTheme()
  const [dialog, setDialog] = useState<'create' | 'join' | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!menuOpen) return
    const away = (e: MouseEvent) => menuRef.current && !menuRef.current.contains(e.target as Node) && setMenuOpen(false)
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setMenuOpen(false)
    document.addEventListener('mousedown', away)
    document.addEventListener('keydown', esc)
    return () => {
      document.removeEventListener('mousedown', away)
      document.removeEventListener('keydown', esc)
    }
  }, [menuOpen])

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
          {onFamiliesPage && (
            <>
              <button className="ghost" onClick={ctx.openJoin} title="Join a family with a code">
                <Users size={16} /> <span className="label">Join with a code</span>
              </button>
              <button onClick={ctx.openCreate} title="Create a family">
                <Plus size={16} /> <span className="label">Create a family</span>
              </button>
            </>
          )}
          <button
            className="ghost icon-btn"
            onClick={toggle}
            aria-label={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            title={theme === 'dark' ? 'Light theme' : 'Dark theme'}
          >
            {theme === 'dark' ? <Sun /> : <Moon />}
          </button>
          {me.data && (
            <div className="menu-wrap" ref={menuRef}>
              <button
                className="profile-chip"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                title="Account"
                onClick={() => setMenuOpen((o) => !o)}
              >
                <AccountAvatar user={me.data} size={28} />
                <span className="label">{me.data.first_name || 'Profile'}</span>
                <span className="chev" aria-hidden>
                  ▾
                </span>
              </button>
              {menuOpen && (
                <div className="menu" role="menu">
                  <Link to="/profile" role="menuitem" onClick={() => setMenuOpen(false)}>
                    My profile
                  </Link>
                  <button
                    role="menuitem"
                    onClick={async () => {
                      setMenuOpen(false)
                      await logout().catch(() => undefined)
                      qc.clear()
                      nav('/login')
                    }}
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          )}
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
