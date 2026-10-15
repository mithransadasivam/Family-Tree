import { useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { Arrow, Plus } from './Icons'
import { useCreateTree, useMe, useMyJoinRequests, useSubmitJoinRequest, useTrees } from './queries'
import Rings from './Rings'

export default function TreesPage() {
  const { data, error, refetch } = useTrees()
  const me = useMe()
  const create = useCreateTree()
  const join = useSubmitJoinRequest()
  const mine = useMyJoinRequests()
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [message, setMessage] = useState('')

  if (error) {
    return (
      <p role="alert" className="status error">
        Failed to load trees: {error.message} <button onClick={() => void refetch()}>Retry</button>
      </p>
    )
  }

  const first = me.data?.first_name

  return (
    <main className="page">
      <header className="page-head rise">
        <span className="eyebrow">{first ? `Welcome back, ${first}` : 'Welcome back'}</span>
        <h1>
          Your <em>families</em>
        </h1>
        <p className="muted">
          {data?.length
            ? 'Open a tree to explore it, or start a new one.'
            : 'Start your first tree, or join one with a family code.'}
        </p>
      </header>

      <div className="tree-grid">
        {data?.map((t, i) => (
          <Link
            key={t.id}
            to={`/trees/${t.id}`}
            className="tree-card rise"
            style={{ '--i': i + 1 } as CSSProperties}
          >
            <Rings className="tree-card-art" seed={t.id * 7 + 3} count={13} />
            <h3>{t.tree_name}</h3>
            <div className="meta">
              <span>{t.description || 'Open this family tree'}</span>
              <span className="go">
                <Arrow size={16} />
              </span>
            </div>
          </Link>
        ))}

        <form
          className="tree-card new rise"
          style={{ '--i': (data?.length ?? 0) + 1 } as CSSProperties}
          onSubmit={(e) => {
            e.preventDefault()
            if (!name.trim()) return
            create.mutate(name.trim(), { onSuccess: () => setName('') })
          }}
        >
          <h3>Plant a new tree</h3>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. The Pell family"
            aria-label="New tree name"
          />
          <button disabled={create.isPending || !name.trim()} style={{ alignSelf: 'flex-start' }}>
            <Plus size={16} /> Create tree
          </button>
          {create.error && (
            <p role="alert" className="error">
              {create.error.message}
            </p>
          )}
        </form>
      </div>

      <div className="two-col">
        <section className="card rise" style={{ '--i': 3 } as CSSProperties}>
          <h3>Join a family</h3>
          <p className="muted" style={{ marginBottom: 16 }}>
            Got a code from a relative? Enter it to ask for access.
          </p>
          <form
            className="stack"
            onSubmit={(e) => {
              e.preventDefault()
              if (!code.trim()) return
              join.mutate(
                { code: code.trim(), message: message.trim() },
                {
                  onSuccess: () => {
                    setCode('')
                    setMessage('')
                  },
                },
              )
            }}
          >
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Family code"
              aria-label="Family code"
              style={{ fontFamily: 'var(--mono)', letterSpacing: '0.1em' }}
            />
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Say hello to the owner (optional)"
              aria-label="Message"
            />
            <button disabled={join.isPending || !code.trim()}>Request to join</button>
          </form>
          {join.data && (
            <p role="status" style={{ marginTop: 12, color: 'var(--sage)' }}>
              {join.data.message}
            </p>
          )}
          {join.error && (
            <p role="alert" className="error" style={{ marginTop: 12 }}>
              {join.error.message}
            </p>
          )}
        </section>

        {mine.data && mine.data.length > 0 && (
          <section className="card rise" style={{ '--i': 4 } as CSSProperties}>
            <h3>Your requests</h3>
            <ul className="plain">
              {mine.data.map((r) => (
                <li key={r.id} className="request">
                  <span>{r.tree_name}</span>
                  <span className={`badge ${r.status}`}>{r.status}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  )
}
