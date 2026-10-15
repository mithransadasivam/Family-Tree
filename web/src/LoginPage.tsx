import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { loadGoogleScript, loginWithGoogle } from './auth'
import { Ring, Users, Fit } from './Icons'
import { LogoMark } from './Logo'

interface GoogleId {
  initialize(cfg: { client_id: string; callback: (r: { credential: string }) => void }): void
  renderButton(el: HTMLElement, opts: Record<string, unknown>): void
}
declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } }
  }
}

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

export default function LoginPage() {
  const btn = useRef<HTMLDivElement>(null)
  const nav = useNavigate()
  const qc = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const signIn = async (credential: string) => {
    try {
      setError(null)
      await loginWithGoogle(credential)
      await qc.invalidateQueries({ queryKey: ['trees'] })
      nav('/', { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sign-in failed')
    }
  }

  useEffect(() => {
    if (!CLIENT_ID) return
    let cancelled = false
    loadGoogleScript()
      .then(() => {
        if (cancelled || !btn.current || !window.google) return
        window.google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: (r) => void signIn(r.credential),
        })
        window.google.accounts.id.renderButton(btn.current, {
          theme: 'filled_black',
          size: 'large',
          shape: 'pill',
          width: 280,
        })
      })
      .catch((e: Error) => setError(e.message))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <main className="login">
      <section className="login-hero">
        <span className="eyebrow rise">Your family, in one place</span>
        <h1 className="rise" style={{ '--i': 1 } as React.CSSProperties}>
          Every family has a <em>story</em> worth keeping.
        </h1>
        <p className="lead rise" style={{ '--i': 2 } as React.CSSProperties}>
          Build your tree, add the people who made you, and share it with the ones who come next.
        </p>
        <ul className="features rise" style={{ '--i': 3 } as React.CSSProperties}>
          <li>
            <span className="dot">
              <Fit />
            </span>
            See every generation laid out and explore it by dragging and zooming
          </li>
          <li>
            <span className="dot">
              <Users />
            </span>
            Invite relatives with a private family code
          </li>
          <li>
            <span className="dot">
              <Ring />
            </span>
            Works with the same account as the Kinship app on your phone
          </li>
        </ul>
      </section>

      <section className="login-card glass rise" style={{ '--i': 2 } as React.CSSProperties}>
        <LogoMark size={52} />
        <h2>Welcome back</h2>
        <p className="muted">Sign in to open your family trees.</p>
        {CLIENT_ID ? (
          <div ref={btn} className="google-slot" />
        ) : (
          <div className="stack" style={{ alignItems: 'center', marginTop: 4 }}>
            <p className="muted">
              Set <code>VITE_GOOGLE_CLIENT_ID</code> to enable Google sign-in.
            </p>
            {import.meta.env.DEV && (
              <button onClick={() => void signIn('dev-credential')}>Dev sign-in</button>
            )}
          </div>
        )}
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <p className="fineprint">We only use your Google account to sign you in.</p>
      </section>
    </main>
  )
}
