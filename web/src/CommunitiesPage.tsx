import { useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { useCommunities, useCreateCommunity, useFindCommunities, useJoinCommunity } from './communityQueries'
import { Arrow, Plus, Search } from './Icons'
import Rings from './Rings'

export default function CommunitiesPage() {
  const list = useCommunities()
  const create = useCreateCommunity()
  const join = useJoinCommunity()
  const [query, setQuery] = useState('')
  const [form, setForm] = useState({ name: '', description: '' })
  const [creating, setCreating] = useState(false)
  const q = query.trim()
  const found = useFindCommunities(q)

  return (
    <main className="page">
      <header className="page-head rise">
        <span className="eyebrow">Places and groups</span>
        <h1>
          Your <em>communities</em>
        </h1>
        <p className="muted">
          A community is a village, congregation or any group. Family owners choose which of their families to share
          with it, and members can search and filter the people in those families.
        </p>
      </header>

      {list.error && (
        <p role="alert" className="status error">
          Could not load your communities: {list.error.message} <button onClick={() => void list.refetch()}>Retry</button>
        </p>
      )}

      <div className="tree-grid">
        {list.data?.map((c, i) => (
          <Link
            key={c.id}
            to={`/communities/${c.id}`}
            className="tree-card rise"
            style={{ '--i': i + 1 } as CSSProperties}
          >
            <Rings className="tree-card-art" seed={c.id * 5 + 1} count={13} />
            <h3>{c.name}</h3>
            <div className="meta">
              <span>
                {c.member_count} {c.member_count === 1 ? 'member' : 'members'} · {c.tree_count}{' '}
                {c.tree_count === 1 ? 'family' : 'families'}
                {c.role === 'owner' ? ' · you own this' : ''}
              </span>
              <span className="go">
                <Arrow size={16} />
              </span>
            </div>
          </Link>
        ))}
      </div>
      {list.data?.length === 0 && (
        <p className="muted rise" style={{ marginBottom: 28 }}>
          You are not in a community yet. Find yours below, or start a new one.
        </p>
      )}

      <section className="card rise" style={{ '--i': 2 } as CSSProperties}>
        <h3>Find a community</h3>
        <p className="muted small">Search by name. The owner approves each request before you can see anything.</p>
        <label className="field search-field">
          <span className="sr-only">Community name</span>
          <div className="row">
            <Search size={16} />
            <input
              className="grow"
              placeholder="Type at least 2 letters of its name"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </label>
        {q.length >= 2 && found.isLoading && <p className="muted">Searching…</p>}
        {found.error && (
          <p role="alert" className="error">
            {found.error.message}
          </p>
        )}
        {q.length >= 2 && found.data?.length === 0 && <p className="muted">No community has that name.</p>}
        <ul className="plain">
          {found.data?.map((c) => (
            <li key={c.id} className="request">
              <div>
                <strong>{c.name}</strong>
                <div className="muted small">
                  {c.member_count} {c.member_count === 1 ? 'member' : 'members'}
                  {c.description ? ` · ${c.description}` : ''}
                </div>
              </div>
              {c.status === 'member' ? (
                <Link to={`/communities/${c.id}`} className="badge">
                  Open
                </Link>
              ) : c.status === 'pending' || join.data?.message && join.variables === c.id ? (
                <span className="badge pending">Request sent</span>
              ) : (
                <button className="ghost" disabled={join.isPending} onClick={() => join.mutate(c.id)}>
                  Ask to join
                </button>
              )}
            </li>
          ))}
        </ul>
        {join.error && (
          <p role="alert" className="error">
            {join.error.message}
          </p>
        )}
      </section>

      <section className="card rise" style={{ '--i': 3 } as CSSProperties}>
        <div className="row between">
          <h3>Start a community</h3>
          {!creating && (
            <button className="ghost" onClick={() => setCreating(true)}>
              <Plus size={16} /> New community
            </button>
          )}
        </div>
        {creating && (
          <form
            className="stack"
            onSubmit={(e) => {
              e.preventDefault()
              create.mutate(
                { name: form.name.trim(), description: form.description.trim() },
                {
                  onSuccess: () => {
                    setForm({ name: '', description: '' })
                    setCreating(false)
                  },
                },
              )
            }}
          >
            <label className="field">
              <span>
                Name
                <span className="req" aria-hidden>
                  {' '}
                  *
                </span>
              </span>
              <input
                required
                autoFocus
                maxLength={120}
                placeholder="e.g. Riverside Village"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              />
            </label>
            <label className="field">
              Description
              <input
                maxLength={500}
                placeholder="Optional. Helps people recognise the right community"
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              />
            </label>
            {create.error && (
              <p role="alert" className="error">
                {create.error.message}
              </p>
            )}
            <div className="row end">
              <button type="button" className="ghost" onClick={() => setCreating(false)}>
                Cancel
              </button>
              <button disabled={create.isPending || form.name.trim().length < 2}>
                {create.isPending ? 'Creating…' : 'Create community'}
              </button>
            </div>
          </form>
        )}
      </section>
    </main>
  )
}
