import type { CSSProperties } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { Arrow, Plus, Users } from './Icons'
import type { ShellContext } from './Protected'
import { useMe, useMyJoinRequests, useTrees } from './queries'
import Rings from './Rings'

export default function TreesPage() {
  const { data, error, refetch } = useTrees()
  const me = useMe()
  const mine = useMyJoinRequests()
  const { openCreate, openJoin } = useOutletContext<ShellContext>()

  if (error) {
    return (
      <p role="alert" className="status error">
        Failed to load your families: {error.message} <button onClick={() => void refetch()}>Retry</button>
      </p>
    )
  }

  const first = me.data?.first_name
  const empty = data?.length === 0

  return (
    <main className="page">
      <header className="page-head rise">
        <span className="eyebrow">{first ? `Welcome back, ${first}` : 'Welcome back'}</span>
        <h1>
          Your <em>families</em>
        </h1>
        <p className="muted">
          {empty
            ? 'Create your first family, or join one with a code from a relative.'
            : 'Open a family to explore it. Use the buttons at the top to create or join another.'}
        </p>
      </header>

      {empty && (
        <div className="row wrap rise" style={{ '--i': 1, marginTop: 0, marginBottom: 32 } as CSSProperties}>
          <button onClick={openCreate}>
            <Plus size={16} /> Create a family
          </button>
          <button className="ghost" onClick={openJoin}>
            <Users size={16} /> Join with a code
          </button>
        </div>
      )}

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
              <span>{t.description || 'Open this family'}</span>
              <span className="go">
                <Arrow size={16} />
              </span>
            </div>
          </Link>
        ))}
      </div>

      {mine.data && mine.data.length > 0 && (
        <section className="card rise" style={{ '--i': 3 } as CSSProperties}>
          <h3>Your join requests</h3>
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
    </main>
  )
}
