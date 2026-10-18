import { useState } from 'react'
import { useCreatePerson, useRelationshipTypes, useSaveMember } from './queries'
import { useTermPicker } from './TermPicker'
import { fullName, type Member } from './types'

interface Props {
  treeId: number
  /** Present when editing; absent when adding someone new. */
  member?: Member
  /** Everyone already in the family, to connect a new person to. */
  members: Member[]
  onClose: () => void
  onSaved: (m: Member) => void
}

const Req = () => (
  <span className="req" aria-hidden>
    {' '}
    *
  </span>
)

export default function MemberForm({ treeId, member, members, onClose, onSaved }: Props) {
  return member ? (
    <EditForm treeId={treeId} member={member} onClose={onClose} onSaved={onSaved} />
  ) : (
    <AddForm treeId={treeId} members={members} onClose={onClose} onSaved={onSaved} />
  )
}

/** Adding: only what is needed, plus how the person connects to the family. */
function AddForm({ treeId, members, onClose, onSaved }: Omit<Props, 'member'>) {
  const create = useCreatePerson(treeId)
  const types = useRelationshipTypes()
  const { typeId, picker } = useTermPicker(types.data)
  const [first, setFirst] = useState('')
  const [last, setLast] = useState('')
  const [otherId, setOtherId] = useState('')

  // The first person in an empty family has nobody to connect to; everyone after must connect.
  const isFirst = members.length === 0
  const valid = first.trim() !== '' && (isFirst || (otherId !== '' && typeId !== undefined))
  const others = [...members].sort((a, b) => fullName(a).localeCompare(fullName(b)))

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form
        className="modal"
        onClick={(e) => e.stopPropagation()}
        onSubmit={(e) => {
          e.preventDefault()
          if (!valid) return
          create.mutate(
            {
              first_name: first.trim(),
              last_name: last.trim(),
              relationship: isFirst ? undefined : { otherId: Number(otherId), typeId: typeId! },
            },
            { onSuccess: onSaved },
          )
        }}
      >
        <div>
          <span className="eyebrow">New person</span>
          <h3 style={{ marginTop: 8 }}>Add to the family</h3>
        </div>

        <div className="row">
          <label className="field grow">
            <span>
              First name
              <Req />
            </span>
            <input required autoFocus value={first} onChange={(e) => setFirst(e.target.value)} />
          </label>
          <label className="field grow">
            Last name
            <input value={last} onChange={(e) => setLast(e.target.value)} />
          </label>
        </div>

        {isFirst ? (
          <p className="muted">This is the first person in the family, so there is no one to connect them to yet.</p>
        ) : (
          <fieldset className="rel-fieldset">
            <legend>
              How are they related?
              <Req />
            </legend>
            <div className="sentence">
              <span className="connector">
                <b>{first.trim() || 'This person'}</b> is the
              </span>
              {picker}
              <span className="connector">of</span>
              <select
                value={otherId}
                onChange={(e) => setOtherId(e.target.value)}
                aria-label="Related person"
                required
              >
                <option value="">Choose a person…</option>
                {others.map((m) => (
                  <option key={m.id} value={m.id}>
                    {fullName(m)}
                  </option>
                ))}
              </select>
            </div>
          </fieldset>
        )}

        <p className="muted small">
          <Req />
          Required. Birth date, birthplace and a photo can be added later with Edit.
        </p>

        {create.error && (
          <p role="alert" className="error">
            {create.error.message}
          </p>
        )}
        <div className="row end">
          <button type="button" className="ghost" onClick={onClose}>
            Cancel
          </button>
          <button disabled={!valid || create.isPending}>{create.isPending ? 'Adding…' : 'Add person'}</button>
        </div>
      </form>
    </div>
  )
}

/** Editing: the fuller set of details. Death details are not collected. */
function EditForm({ treeId, member, onClose, onSaved }: Omit<Props, 'members' | 'member'> & { member: Member }) {
  const save = useSaveMember(treeId)
  const [f, setF] = useState({
    first_name: member.first_name,
    last_name: member.last_name,
    birth_date: member.birth_date ?? '',
    birth_place: member.birth_place,
    photo_url: member.photo_url,
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
            { id: member.id, input: { ...f, first_name: f.first_name.trim(), last_name: f.last_name.trim() } },
            { onSuccess: onSaved },
          )
        }}
      >
        <div>
          <span className="eyebrow">Update details</span>
          <h3 style={{ marginTop: 8 }}>Edit {member.first_name}</h3>
        </div>
        <div className="row">
          <label className="field grow">
            <span>
              First name
              <Req />
            </span>
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
        <label className="field">
          Photo link
          <input type="url" placeholder="https://…" value={f.photo_url} onChange={set('photo_url')} />
        </label>
        <p className="muted small">
          <Req />
          Required
        </p>
        {save.error && (
          <p role="alert" className="error">
            {save.error.message}
          </p>
        )}
        <div className="row end">
          <button type="button" className="ghost" onClick={onClose}>
            Cancel
          </button>
          <button disabled={save.isPending || f.first_name.trim() === ''}>{save.isPending ? 'Saving…' : 'Save changes'}</button>
        </div>
      </form>
    </div>
  )
}
