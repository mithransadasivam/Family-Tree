import { useState } from 'react'
import Avatar, { lifespan } from './Avatar'
import { classify, GROUP_ORDER, type Group } from './graph'
import { Close, Edit, Trash } from './Icons'
import {
  useAddRelationship,
  useDeleteMember,
  useDeleteRelationship,
  useRelationshipTypes,
  useUpdateRelationship,
} from './queries'
import { useTermPicker } from './TermPicker'
import { fullName, type Member, type Relationship, type RelationshipType } from './types'

interface Props {
  treeId: number
  member: Member
  members: Member[]
  relationships: Relationship[]
  onEdit: () => void
  onDeleted: () => void
  onSelect: (id: number) => void
  onClose: () => void
}

/** Edit one existing relationship in place: who the other person is, and what they are. */
function RelEditor({
  treeId,
  rel,
  member,
  candidates,
  types,
  onDone,
}: {
  treeId: number
  rel: Relationship
  member: Member
  candidates: Member[]
  types: RelationshipType[] | undefined
  onDone: () => void
}) {
  const update = useUpdateRelationship(treeId)
  const selfIsFirst = rel.member_1 === member.id
  const [otherId, setOtherId] = useState(String(selfIsFirst ? rel.member_2 : rel.member_1))
  const { typeId, picker } = useTermPicker(types, rel.relationship_type_name)

  const save = () => {
    if (typeId === undefined || !otherId) return
    // Keep the stored direction: the type says what member_1 IS to member_2.
    const other = Number(otherId)
    update.mutate(
      {
        id: rel.id,
        member_1: selfIsFirst ? member.id : other,
        member_2: selfIsFirst ? other : member.id,
        relationship_type: typeId,
      },
      { onSuccess: onDone },
    )
  }

  const otherSelect = (
    <select value={otherId} onChange={(e) => setOtherId(e.target.value)} aria-label="Related person">
      {candidates.map((m) => (
        <option key={m.id} value={m.id}>
          {fullName(m)}
        </option>
      ))}
    </select>
  )

  return (
    <div className="sentence editing">
      {selfIsFirst ? (
        <span className="connector">
          <b>{fullName(member)}</b> is the
        </span>
      ) : (
        <>
          {otherSelect}
          <span className="connector">is the</span>
        </>
      )}
      {picker}
      {selfIsFirst ? (
        <>
          <span className="connector">of</span>
          {otherSelect}
        </>
      ) : (
        <span className="connector">
          of <b>{fullName(member)}</b>
        </span>
      )}
      {update.error && (
        <p role="alert" className="error">
          {update.error.message}
        </p>
      )}
      <div className="row end" style={{ marginTop: 0 }}>
        <button type="button" className="ghost" onClick={onDone}>
          Cancel
        </button>
        <button disabled={typeId === undefined || update.isPending} onClick={save}>
          {update.isPending ? 'Saving…' : 'Save'}
        </button>
      </div>
    </div>
  )
}

export default function DetailPanel({
  treeId,
  member,
  members,
  relationships,
  onEdit,
  onDeleted,
  onSelect,
  onClose,
}: Props) {
  const del = useDeleteMember(treeId)
  const addRel = useAddRelationship(treeId)
  const delRel = useDeleteRelationship(treeId)
  const types = useRelationshipTypes()
  const [otherId, setOtherId] = useState('')
  const [editingRel, setEditingRel] = useState<number | null>(null)
  const { typeId, picker, reset } = useTermPicker(types.data)

  const byId = new Map(members.map((m) => [m.id, m]))
  const candidates = members.filter((m) => m.id !== member.id)

  const grouped = new Map<Group, { rel: Relationship; other: number; label: string }[]>()
  for (const rel of relationships) {
    if (rel.member_1 !== member.id && rel.member_2 !== member.id) continue
    const { group, other, label } = classify(rel, member.id)
    grouped.set(group, [...(grouped.get(group) ?? []), { rel, other, label }])
  }

  // The relationship type says what member_1 IS to member_2, so "[other] is the [type] of
  // [this member]" is stored as member_1 = other, member_2 = this member.
  const submit = () => {
    if (!otherId || typeId === undefined) return
    addRel.mutate(
      { member_1: Number(otherId), member_2: member.id, relationship_type: typeId },
      {
        onSuccess: () => {
          setOtherId('')
          reset()
        },
      },
    )
  }

  const facts = [
    member.birth_date && `Born ${member.birth_date}${member.birth_place ? ` · ${member.birth_place}` : ''}`,
    member.death_date && `Died ${member.death_date}${member.death_place ? ` · ${member.death_place}` : ''}`,
  ].filter(Boolean)

  return (
    <aside className="panel" aria-label={`Details for ${fullName(member)}`}>
      <button className="ghost icon-btn panel-close" onClick={onClose} aria-label="Close details">
        <Close size={16} />
      </button>

      <div className="person-head">
        <div className="avatar-halo">
          <Avatar member={member} size={84} />
        </div>
        <h2>{fullName(member)}</h2>
        {lifespan(member) && <span className="eyebrow">{lifespan(member)}</span>}
        <div className="facts">
          {facts.length === 0 && <span>No dates recorded yet</span>}
          {facts.map((f) => (
            <span key={String(f)}>{f}</span>
          ))}
        </div>
      </div>

      <div className="actions">
        <button className="ghost" onClick={onEdit}>
          <Edit size={15} /> Edit
        </button>
        <button
          className="danger"
          disabled={del.isPending}
          onClick={() => {
            if (confirm(`Delete ${fullName(member)}? Their relationships will be removed too.`)) {
              del.mutate(member.id, { onSuccess: onDeleted })
            }
          }}
        >
          <Trash size={15} /> Delete
        </button>
      </div>
      {del.error && (
        <p role="alert" className="error" style={{ marginTop: 10, textAlign: 'center' }}>
          {del.error.message}
        </p>
      )}

      {grouped.size === 0 && (
        <>
          <h4>Family</h4>
          <p className="muted">No relationships yet. Connect {member.first_name} below.</p>
        </>
      )}
      {GROUP_ORDER.filter((g) => grouped.has(g)).map((g) => (
        <section key={g}>
          <h4>{g}</h4>
          <ul className="people">
            {grouped.get(g)!.map(({ rel, other, label }) => {
              const o = byId.get(other)
              if (editingRel === rel.id) {
                return (
                  <li key={rel.id} className="editing-row">
                    <RelEditor
                      treeId={treeId}
                      rel={rel}
                      member={member}
                      candidates={candidates}
                      types={types.data}
                      onDone={() => setEditingRel(null)}
                    />
                  </li>
                )
              }
              return (
                <li key={rel.id}>
                  {o ? <Avatar member={o} size={36} /> : <span className="avatar" style={{ width: 36, height: 36 }} />}
                  <div className="who">
                    <button className="link" onClick={() => onSelect(other)}>
                      {o ? fullName(o) : `#${other}`}
                    </button>
                    <span>{label}</span>
                  </div>
                  <button
                    className="ghost icon-btn mini x"
                    aria-label={`Edit relationship with ${o ? fullName(o) : other}`}
                    onClick={() => setEditingRel(rel.id)}
                  >
                    <Edit size={14} />
                  </button>
                  <button
                    className="ghost icon-btn mini x"
                    aria-label={`Remove relationship with ${o ? fullName(o) : other}`}
                    disabled={delRel.isPending}
                    onClick={() => delRel.mutate(rel.id)}
                  >
                    <Close size={14} />
                  </button>
                </li>
              )
            })}
          </ul>
        </section>
      ))}

      <h4>Connect someone</h4>
      {candidates.length === 0 ? (
        <p className="muted">Add another person first, then connect them here.</p>
      ) : (
        <div className="sentence">
          <select value={otherId} onChange={(e) => setOtherId(e.target.value)} aria-label="Related member">
            <option value="">Choose a person…</option>
            {candidates.map((m) => (
              <option key={m.id} value={m.id}>
                {fullName(m)}
              </option>
            ))}
          </select>
          <span className="connector">is the</span>
          {picker}
          <span className="connector">
            of <b>{fullName(member)}</b>
          </span>
          <button disabled={!otherId || typeId === undefined || addRel.isPending} onClick={submit}>
            {addRel.isPending ? 'Connecting…' : 'Connect'}
          </button>
        </div>
      )}
      {types.error && (
        <p role="alert" className="error" style={{ marginTop: 8 }}>
          Could not load relationship types: {types.error.message}
        </p>
      )}
      {addRel.error && (
        <p role="alert" className="error" style={{ marginTop: 8 }}>
          {addRel.error.message}
        </p>
      )}
      {delRel.error && (
        <p role="alert" className="error" style={{ marginTop: 8 }}>
          {delRel.error.message}
        </p>
      )}
    </aside>
  )
}
