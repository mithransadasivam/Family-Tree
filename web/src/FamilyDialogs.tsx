import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Close } from './Icons'
import { useCreateTree, useSubmitJoinRequest } from './queries'

function Shell({ title, eyebrow, onClose, children }: { title: string; eyebrow: string; onClose: () => void; children: React.ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="row between" style={{ alignItems: 'flex-start' }}>
          <div>
            <span className="eyebrow">{eyebrow}</span>
            <h3 style={{ marginTop: 8 }}>{title}</h3>
          </div>
          <button className="ghost icon-btn" onClick={onClose} aria-label="Close">
            <Close size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function CreateFamilyDialog({ onClose }: { onClose: () => void }) {
  const create = useCreateTree()
  const nav = useNavigate()
  const [name, setName] = useState('')
  return (
    <Shell eyebrow="Start fresh" title="Create a family" onClose={onClose}>
      <form
        className="stack"
        onSubmit={(e) => {
          e.preventDefault()
          if (!name.trim()) return
          create.mutate(name.trim(), {
            onSuccess: (tree) => {
              onClose()
              nav(`/trees/${tree.id}`)
            },
          })
        }}
      >
        <label className="field">
          <span>
            Family name
            <span className="req" aria-hidden>
              {' '}
              *
            </span>
          </span>
          <input autoFocus required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. The Sadasivam family" />
        </label>
        {create.error && (
          <p role="alert" className="error">
            {create.error.message}
          </p>
        )}
        <div className="row end">
          <button type="button" className="ghost" onClick={onClose}>
            Cancel
          </button>
          <button disabled={create.isPending || !name.trim()}>{create.isPending ? 'Creating…' : 'Create family'}</button>
        </div>
      </form>
    </Shell>
  )
}

export function JoinFamilyDialog({ onClose }: { onClose: () => void }) {
  const join = useSubmitJoinRequest()
  const [code, setCode] = useState('')
  const [message, setMessage] = useState('')
  return (
    <Shell eyebrow="Got an invite?" title="Join a family" onClose={onClose}>
      {join.data ? (
        <>
          <p role="status" style={{ color: 'var(--sage)' }}>
            {join.data.message}
          </p>
          <div className="row end">
            <button onClick={onClose}>Done</button>
          </div>
        </>
      ) : (
        <form
          className="stack"
          onSubmit={(e) => {
            e.preventDefault()
            if (code.trim()) join.mutate({ code: code.trim(), message: message.trim() })
          }}
        >
          <p className="muted">Enter the family code a relative sent you. The owner may need to approve you.</p>
          <label className="field">
            <span>
              Family code
              <span className="req" aria-hidden>
                {' '}
                *
              </span>
            </span>
            <input
              autoFocus
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={{ fontFamily: 'var(--mono)', letterSpacing: '0.1em' }}
            />
          </label>
          <label className="field">
            Message to the owner (optional)
            <input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Say hello" />
          </label>
          {join.error && (
            <p role="alert" className="error">
              {join.error.message}
            </p>
          )}
          <div className="row end">
            <button type="button" className="ghost" onClick={onClose}>
              Cancel
            </button>
            <button disabled={join.isPending || !code.trim()}>{join.isPending ? 'Sending…' : 'Request to join'}</button>
          </div>
        </form>
      )}
    </Shell>
  )
}
