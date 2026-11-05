import { useDeferredValue, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { useStaffTrees } from './queries'
import { fullName } from './types'

const LIMIT = 50
const day = (iso: string) => new Date(iso).toLocaleDateString(undefined, { dateStyle: 'medium' })

/** Superuser only: every family in the system. Read-only; each row opens that family's tree. */
export default function StaffTreesPage() {
  const [text, setText] = useState('')
  const [offset, setOffset] = useState(0)
  const q = useDeferredValue(text.trim())
  const { data, error, isFetching, refetch } = useStaffTrees(q, offset, LIMIT)

  const total = data?.count ?? 0
  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + LIMIT, total)

  return (
    <main className="page">
      <header className="page-head rise">
        <span className="eyebrow">Staff</span>
        <h1>
          All <em>families</em>
        </h1>
        <p className="muted">Every family tree in the system, read-only. Open one to see it as its members do.</p>
      </header>

      <div className="staff-tools rise" style={{ '--i': 1 } as CSSProperties}>
        <input
          type="search"
          placeholder="Search by family name or owner…"
          aria-label="Search families or owners"
          value={text}
          onChange={(e) => {
            setText(e.target.value)
            setOffset(0)
          }}
        />
        <span className="muted small" role="status">
          {isFetching ? 'Loading…' : total === 0 ? 'No families' : `${from}–${to} of ${total}`}
        </span>
      </div>

      {error ? (
        <p role="alert" className="status error">
          Could not load families: {error.message} <button onClick={() => void refetch()}>Retry</button>
        </p>
      ) : (
        <div className="card staff-card rise" style={{ '--i': 2 } as CSSProperties}>
          <table className="staff-table">
            <thead>
              <tr>
                <th>Family</th>
                <th>Owner</th>
                <th className="num">People</th>
                <th className="num">Accounts</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {data?.results.map((t) => (
                <tr key={t.id}>
                  <td>
                    <Link to={`/staff/trees/${t.id}`}>{t.tree_name}</Link>
                    {!t.is_active && <span className="badge rejected staff-flag">deleted</span>}
                  </td>
                  <td>
                    <span>{fullName(t.owner) || '—'}</span>
                    <span className="muted small staff-email">{t.owner.email}</span>
                  </td>
                  <td className="num">{t.people_count}</td>
                  <td className="num">{t.account_count}</td>
                  <td>{day(t.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {total > LIMIT && (
        <div className="row staff-pager">
          <button className="ghost" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))}>
            Previous
          </button>
          <button className="ghost" disabled={to >= total} onClick={() => setOffset(offset + LIMIT)}>
            Next
          </button>
        </div>
      )}
    </main>
  )
}
