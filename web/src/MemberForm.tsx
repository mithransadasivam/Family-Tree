import { useState } from 'react'
import { useSaveMember } from './queries'
import type { Member } from './types'

interface Props {
  treeId: number
  member?: Member
  onClose: () => void
  onSaved: (m: Member) => void
}

export default function MemberForm({ treeId, member, onClose, onSaved }: Props) {
  const save = useSaveMember(treeId)
  const [f, setF] = useState({
    first_name: member?.first_name ?? '',
    last_name: member?.last_name ?? '',
    birth_date: member?.birth_date ?? '',
    birth_place: member?.birth_place ?? '',
    death_date: member?.death_date ?? '',
    death_place: member?.death_place ?? '',
    photo_url: member?.photo_url ?? '',
  })
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setF((p) => ({ ...p, [k]: e.target.value }))

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form
        className="modal"
        onClick={(e) => e.stopPropagation()}
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate(
            { id: member?.id, input: { ...f, first_name: f.first_name.trim(), last_name: f.last_name.trim() } },
            { onSuccess: onSaved },
          )
        }}
      >
        <div>
          <span className="eyebrow">{member ? 'Update details' : 'New person'}</span>
          <h3 style={{ marginTop: 8 }}>{member ? `Edit ${member.first_name}` : 'Add to the tree'}</h3>
        </div>
        <div className="row">
          <label className="field grow">
            First name
            <input required autoFocus value={f.first_name} onChange={set('first_name')} />
          </label>
          <label className="field grow">
            Last name
            <input value={f.last_name} onChange={set('last_name')} />
          </label>
        </div>
        <div className="row">
          <label className="field grow">
            Born
            <input type="date" value={f.birth_date} onChange={set('birth_date')} />
          </label>
          <label className="field grow">
            Birthplace
            <input value={f.birth_place} onChange={set('birth_place')} />
          </label>
        </div>
        <div className="row">
          <label className="field grow">
            Died
            <input type="date" value={f.death_date} onChange={set('death_date')} />
          </label>
          <label className="field grow">
            Place
            <input value={f.death_place} onChange={set('death_place')} />
          </label>
        </div>
        <label className="field">
          Photo link
          <input type="url" placeholder="https://…" value={f.photo_url} onChange={set('photo_url')} />
        </label>
        {save.error && (
          <p role="alert" className="error">
            {save.error.message}
          </p>
        )}
        <div className="row end">
          <button type="button" className="ghost" onClick={onClose}>
            Cancel
          </button>
          <button disabled={save.isPending}>{save.isPending ? 'Saving…' : member ? 'Save changes' : 'Add person'}</button>
        </div>
      </form>
    </div>
  )
}
