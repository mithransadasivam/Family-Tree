import type { CSSProperties } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useApprovalRequest, useDecideApproval } from './communityQueries'

/** Where the emailed link lands: who is asking, and one tap to approve or decline. */
export default function ApprovePage() {
  const params = useParams()
  const kind = params.kind === 'tree' ? 'tree' : 'community'
  const id = Number(params.requestId)
  const req = useApprovalRequest(kind, id)
  const decide = useDecideApproval(kind, id)

  if (req.isLoading) return <p className="status">Loading…</p>
  if (req.error || !req.data) {
    return (
      <main className="page narrow">
        <section className="card rise">
          <h3>We could not open this request</h3>
          <p className="muted">
            It may not exist, or it belongs to someone else. Only the owner of the {kind === 'tree' ? 'family' : 'community'}{' '}
            can approve requests, so make sure you are signed in with the right Google account.
          </p>
          <div className="row end">
            <Link to="/">Back to your families</Link>
          </div>
        </section>
      </main>
    )
  }
  const r = req.data
  const noun = kind === 'tree' ? 'family' : 'community'
  const open = kind === 'tree' ? `/trees/${r.target_id}` : `/communities/${r.target_id}`

  return (
    <main className="page narrow">
      <header className="page-head rise">
        <span className="eyebrow">Join request</span>
        <h1>
          {r.requester_name} <em>wants to join</em>
        </h1>
        <p className="muted">
          {r.target_name} · {noun}
        </p>
      </header>
      <section className="card rise" style={{ '--i': 1 } as CSSProperties}>
        <div className="detail-row">
          <div>
            <div className="detail-label">Who</div>
            <div>{r.requester_name}</div>
            <div className="muted small">{r.requester_email}</div>
          </div>
        </div>
        {r.tree_name && (
          <div className="detail-row">
            <div>
              <div className="detail-label">Family they offer to share</div>
              <div>{r.tree_name}</div>
            </div>
          </div>
        )}
        {r.message && (
          <div className="detail-row">
            <div>
              <div className="detail-label">Their message</div>
              <div>{r.message}</div>
            </div>
          </div>
        )}

        {r.status === 'pending' ? (
          <>
            <p className="muted small">
              {kind === 'tree'
                ? 'Approving gives them access to your whole family tree.'
                : 'Approving lets them search the people in the families shared with this community.'}{' '}
              Only approve someone you recognise.
            </p>
            {decide.error && (
              <p role="alert" className="error">
                {decide.error.message}
              </p>
            )}
            <div className="row end">
              <button className="ghost" disabled={decide.isPending} onClick={() => decide.mutate('rejected')}>
                Decline
              </button>
              <button disabled={decide.isPending} onClick={() => decide.mutate('approved')}>
                {decide.isPending ? 'Saving…' : 'Approve'}
              </button>
            </div>
          </>
        ) : (
          <>
            <p role="status" style={{ color: r.status === 'approved' ? 'var(--sage)' : undefined }}>
              {r.status === 'approved' ? `Approved. ${r.requester_name} is now in ${r.target_name}.` : 'Declined.'}
            </p>
            <div className="row end">
              <Link to={open}>Open {r.target_name}</Link>
            </div>
          </>
        )}
      </section>
    </main>
  )
}
