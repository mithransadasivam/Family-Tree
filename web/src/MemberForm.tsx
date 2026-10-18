import { useState } from 'react'
import { FEMALE_TYPES, MALE_TYPES } from './graph'
import { Mars, Venus } from './Icons'
import { useCreatePerson, useRelationshipTypes, useSaveMember } from './queries'
import { useTermPicker } from './TermPicker'
import { fullName, type Gender, type Member } from './types'

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

/**
 * One-click gender toggle: first click = male, next click = female, and so on back and forth.
 * Until the first click nothing is chosen (which is what makes it a required field).
 */
function GenderField({ value, onChange, required }: { value: Gender; onChange: (g: Gender) => void; required?: boolean }) {
  const chosen = value === 'male' || value === 'female'
  const label = value === 'male' ? 'Male' : value === 'female' ? 'Female' : 'Click to choose'
  return (
    <div className="field" role="group" aria-label="Gender">
      <span>
        Gender
        {required && <Req />}
      </span>
      <button
        type="button"
        className={`gender-toggle ${chosen ? value : 'unset'}`}
        onClick={() => onChange(value === 'male' ? 'female' : 'male')}
        aria-label={
          chosen
            ? `Gender: ${label}. Click to switch to ${value === 'male' ? 'female' : 'male'}.`
            : 'Gender: not chosen. Click to choose male; click again for female.'
        }
        title={chosen ? 'Click to switch' : 'Click to choose'}
      >
        {value === 'female' ? (
          <Venus size={22} />
        ) : value === 'male' ? (
          <Mars size={22} />
        ) : (
          <>
            <Mars size={18} />
            <Venus size={18} />
          </>
        )}
        <span>{label}</span>
      </button>
    </div>
  )
}

export default function MemberForm({ treeId, member, members, onClose, onSaved }: Props) {
  return member ? (
    <EditForm treeId={treeId} member={member} onClose={onClose} onSaved={onSaved} />
  ) : (
    <AddForm treeId={treeId} members={members} onClose={onClose} onSaved={onSaved} />
  )
}

/** A man cannot be recorded as a "Mother", a woman as a "Son", and so on. */
const allowFor = (g: Gender) => (type: string) =>
  g === 'male' ? !FEMALE_TYPES.has(type) : g === 'female' ? !MALE_TYPES.has(type) : true

/** Adding: only what is needed, plus how the person connects to the family. */
function AddForm({ treeId, members, onClose, onSaved }: Omit<Props, 'member'>) {
  const create = useCreatePerson(treeId)
  const types = useRelationshipTypes()
  const [first, setFirst] = useState('')
  const [last, setLast] = useState('')
  const [gender, setGender] = useState<Gender>('')
  const [otherId, setOtherId] = useState('')
  const { typeId, picker } = useTermPicker(types.data, undefined, allowFor(gender))

  // The first person in an empty family has nobody to connect to; everyone after must connect.
  const isFirst = members.length === 0
  const valid =
    first.trim() !== '' && last.trim() !== '' && (gender === 'male' || gender === 'female') && (isFirst || (otherId !== '' && typeId !== undefined))
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
              gender,
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
            <span>
              Last name
              <Req />
            </span>
            <input required value={last} onChange={(e) => setLast(e.target.value)} />
          </label>
        </div>

        <GenderField value={gender} onChange={setGender} required />

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
    gender: (member.gender ?? '') as Gender,
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
            <span>
              Last name
              <Req />
            </span>
            <input required value={f.last_name} onChange={set('last_name')} />
          </label>
        </div>
        <GenderField value={f.gender} onChange={(g) => setF((p) => ({ ...p, gender: g }))} />
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
          <button disabled={save.isPending || f.first_name.trim() === '' || f.last_name.trim() === ''}>
            {save.isPending ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </form>
    </div>
  )
}
