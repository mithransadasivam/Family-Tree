import { useState } from 'react'
import { useRestoreStash, useStaffStashes } from './queries'
import type { StaffStashRestored } from './types'

const day = (iso: string) => new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

/**
 * Staff edit mode only: people staff deleted from this family who can still be brought back.
 *
 * The server keeps the whole row for a limited time after a staff delete, so a restore here is exact:
 * same id, the private phone number and the account link included (which the quick Undo bar after a delete
 * could not recover before). Only names and dates are listed; none of the person's data is shown.
 */
export default function RecentlyDeleted({
  treeId,
  onClose,
  onRestored,
}: {
  treeId: number
  onClose: () => void
  onRestored: (personId: number) => void
}) {
  const list = useStaffStashes(treeId, true)
  const restore = useRestoreStash(treeId)
  const [done, setDone] = useState<{ name: string; result: StaffStashRestored } | null>(null)

  const run = (id: number, name: string) => {
    setDone(null)
    restore.mutate(id, { onSuccess: (result) => setDone({ name, result }) })
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-label="Recently deleted people" onClick={(e) => e.stopPropagation()}>
        <div>
          <span className="eyebrow">Staff</span>
          <h3 style={{ marginTop: 8 }}>Recently deleted</h3>
          <p className="muted small">
            People removed through staff edit mode can be restored for a limited time, exactly as they were (private
            phone number and account link included).
          </p>
        </div>

        {list.isLoading && <p className="muted">Loading…</p>}
        {list.error && (
          <p role="alert" className="error">
            {list.error.message}
          </p>
        )}
        {list.data?.length === 0 && <p className="muted">Nobody has been deleted recently.</p>}

        <ul className="people">
          {list.data?.map((s) => (
            <li key={s.id}>
              <div className="who">
                <b>{s.name}</b>
                <span>
                  Deleted {day(s.deleted_at)} by {s.deleted_by ?? 'a former account'} · {s.relationship_count}{' '}
                  {s.relationship_count === 1 ? 'relationship' : 'relationships'} · restorable until {day(s.expires_at)}
                </span>
              </div>
              <button disabled={restore.isPending} onClick={() => run(s.id, s.name)}>
                Restore
              </button>
            </li>
          ))}
        </ul>

        {restore.error && (
          <p role="alert" className="error">
            {restore.error.message}
          </p>
        )}
        {done && (
          <div role="status" className="muted">
            <p>
              Restored {done.name}
              {done.result.restored_relationships + done.result.skipped_relationships.length > 0 &&
                ` with ${done.result.restored_relationships} of ${
                  done.result.restored_relationships + done.result.skipped_relationships.length
                } relationships`}
              .
            </p>
            {done.result.skipped_relationships.map((s) => (
              <p key={s.link} className="error">
                Could not restore: {s.link} ({s.reason}).
              </p>
            ))}
            {done.result.account_link === 'dropped' && (
              <p className="error">Their account link was not restored: that account is no longer in this family.</p>
            )}
            <button type="button" className="ghost" onClick={() => onRestored(done.result.member.id)}>
              Show them in the tree
            </button>
          </div>
        )}

        <div className="row end">
          <button type="button" className="ghost" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
