import { useState, type CSSProperties } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Back, Check, Copy, Plus } from './Icons'
import {
  useDecideJoinRequest,
  useEditHistory,
  useGenerateCode,
  useJoinRequests,
  useMe,
  useRemoveTree,
  useTrees,
  useUpdateTreeSettings,
} from './queries'

const fmt = (iso: string) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })

function CodePill({ code }: { code: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <span className="code-pill">
      {code}
      <button
        className="ghost icon-btn mini"
        aria-label={copied ? 'Copied' : `Copy code ${code}`}
        onClick={() => {
          void navigator.clipboard?.writeText(code).then(() => {
            setCopied(true)
            setTimeout(() => setCopied(false), 1500)
          })
        }}
      >
        {copied ? <Check size={15} /> : <Copy size={15} />}
      </button>
    </span>
  )
}

export default function ManagePage() {
  const treeId = Number(useParams().treeId)
  const nav = useNavigate()
  const trees = useTrees()
  const me = useMe()
  const tree = trees.data?.find((t) => t.id === treeId)
  const isOwner = !!tree && !!me.data && tree.owner.id === me.data.id

  const settings = useUpdateTreeSettings(treeId)
  const genCode = useGenerateCode(treeId)
  const requests = useJoinRequests(treeId, isOwner)
  const decide = useDecideJoinRequest(treeId)
  const history = useEditHistory(treeId)
  const remove = useRemoveTree(treeId)
  const [codes, setCodes] = useState<string[]>([])

  if (trees.isLoading || me.isLoading) return <p className="status">Loading…</p>
  if (!tree) return <p className="status error">Tree not found.</p>

  const i = (n: number) => ({ '--i': n }) as CSSProperties

  return (
    <main className="page narrow">
      <header className="page-head rise">
        <Link to={`/trees/${treeId}`} className="back">
          <Back size={15} /> Back to the tree
        </Link>
        <span className="eyebrow" style={{ display: 'block' }}>
          {isOwner ? 'You own this tree' : `Owned by ${tree.owner.first_name || tree.owner.email}`}
        </span>
        <h1>
          Manage <em>{tree.tree_name}</em>
        </h1>
        <p className="muted">
          {tree.member_count} {tree.member_count === 1 ? 'account has' : 'accounts have'} access to this tree.
        </p>
      </header>

      {isOwner && (
        <section className="card rise" style={i(1)}>
          <h3>Invite family</h3>
          <p className="muted">Each code works once. Send it to the person you want to invite.</p>
          <div className="row" style={{ marginTop: 14 }}>
            <button
              disabled={genCode.isPending}
              onClick={() => genCode.mutate(undefined, { onSuccess: (r) => setCodes((c) => [r.code, ...c]) })}
            >
              <Plus size={16} /> New invite code
            </button>
          </div>
          {codes.length > 0 && (
            <div className="codes">
              {codes.map((c) => (
                <CodePill key={c} code={c} />
              ))}
            </div>
          )}
          {genCode.error && (
            <p role="alert" className="error" style={{ marginTop: 10 }}>
              {genCode.error.message}
            </p>
          )}

          <div className="section-gap">
            <h3>Joining</h3>
            <label className="check">
              <input
                type="checkbox"
                checked={tree.approval_required}
                disabled={settings.isPending}
                onChange={(e) => settings.mutate(e.target.checked)}
              />
              <span>Ask for my approval before anyone joins</span>
            </label>
            {settings.error && (
              <p role="alert" className="error" style={{ marginTop: 10 }}>
                {settings.error.message}
              </p>
            )}
          </div>

          <div className="section-gap">
            <h3>Join requests</h3>
            {requests.isLoading && <p className="muted">Loading…</p>}
            {requests.error && (
              <p role="alert" className="error">
                {requests.error.message}
              </p>
            )}
            {requests.data?.length === 0 && <p className="muted">Nobody is waiting right now.</p>}
            <ul className="plain">
              {requests.data?.map((r) => (
                <li key={r.id} className="request">
                  <div>
                    <strong style={{ fontFamily: 'var(--serif)', fontSize: '1.05rem', fontWeight: 500 }}>
                      {r.requester_name}
                    </strong>{' '}
                    <span className="muted">{r.requester_email}</span>
                    {r.message && <div style={{ marginTop: 2 }}>“{r.message}”</div>}
                    <div className="muted">{fmt(r.created_at)}</div>
                  </div>
                  <div className="row">
                    <button disabled={decide.isPending} onClick={() => decide.mutate({ id: r.id, status: 'approved' })}>
                      Approve
                    </button>
                    <button
                      className="danger"
                      disabled={decide.isPending}
                      onClick={() => decide.mutate({ id: r.id, status: 'rejected' })}
                    >
                      Decline
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            {decide.error && (
              <p role="alert" className="error">
                {decide.error.message}
              </p>
            )}
          </div>
        </section>
      )}

      <section className="card rise" style={i(2)}>
        <h3>Recent changes</h3>
        {history.isLoading && <p className="muted">Loading…</p>}
        {history.error && (
          <p role="alert" className="error">
            {history.error.message}
          </p>
        )}
        {history.data?.length === 0 && <p className="muted">Nothing has changed yet.</p>}
        <ul className="timeline">
          {history.data?.map((h) => (
            <li key={h.id}>
              <div>{h.change_description}</div>
              <div className="muted">
                {h.edited_by ? h.edited_by.first_name || h.edited_by.email : 'Former member'} · {fmt(h.edited_at)}
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="card danger-zone rise" style={i(3)}>
        <h3>{isOwner ? 'Delete this tree' : 'Leave this tree'}</h3>
        <p className="muted" style={{ marginBottom: 14 }}>
          {isOwner
            ? 'The tree disappears for everyone who has access.'
            : 'You will lose access unless someone invites you again.'}
        </p>
        <button
          className="danger"
          disabled={remove.isPending}
          onClick={() => {
            const mode = isOwner ? 'delete' : 'leave'
            const msg = isOwner ? `Delete “${tree.tree_name}” for everyone?` : `Leave “${tree.tree_name}”?`
            if (confirm(msg)) remove.mutate(mode, { onSuccess: () => nav('/', { replace: true }) })
          }}
        >
          {isOwner ? 'Delete tree' : 'Leave tree'}
        </button>
        {remove.error && (
          <p role="alert" className="error" style={{ marginTop: 10 }}>
            {remove.error.message}
          </p>
        )}
      </section>
    </main>
  )
}
