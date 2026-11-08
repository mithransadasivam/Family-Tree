import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import DetailPanel from './DetailPanel'
import { Back, Plus } from './Icons'
import MemberForm from './MemberForm'
import { useRestore, useStaffTree, type MemberSnapshot } from './queries'
import RecentlyDeleted from './RecentlyDeleted'
import Rings from './Rings'
import { staffSource, TreeSourceContext } from './treeSource'
import { useTreeLayout } from './treeLayout'
import TreeConflictNotice from './TreeConflictNotice'
import TreeView from './TreeView'
import UndoBar, { type Undoable } from './UndoBar'
import { fullName, type Member, type Relationship } from './types'

const nothing = () => undefined

/**
 * Superuser only: any family drawn exactly as its members see it. It opens strictly look-don't-touch;
 * "Edit this tree" turns on staff edit mode, which brings back the same Add / Edit / Connect / Delete
 * controls the family page has (the owner-only delete rule does not apply to staff).
 *
 * All reads and writes go through /api/staff/ (no membership needed). The page provides the staff
 * data source to the shared editing components, so nothing outside this route can reach those URLs.
 * The controls are a convenience: the server refuses every write from anyone who is not a superuser.
 */
export default function StaffTreePage() {
  const treeId = Number(useParams().treeId)
  const source = useMemo(() => staffSource(treeId), [treeId])
  return (
    <TreeSourceContext.Provider value={source}>
      <StaffTreeEditor treeId={treeId} />
    </TreeSourceContext.Provider>
  )
}

function StaffTreeEditor({ treeId }: { treeId: number }) {
  const detail = useStaffTree(treeId)
  const { memberList, byId, forest, generations, genders, conflicts } = useTreeLayout(
    detail.data?.members,
    detail.data?.relationships,
  )
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [focus, setFocus] = useState<{ id: number; n: number } | null>(null)
  // Off every time the page opens: staff must choose to edit, and it is never remembered.
  const [editMode, setEditMode] = useState(false)
  const [editing, setEditing] = useState<Member | 'new' | null>(null)
  const [undo, setUndo] = useState<Undoable | null>(null)
  const [showDeleted, setShowDeleted] = useState(false)
  const restore = useRestore(treeId)

  const tree = detail.data?.tree
  // A family its owner deleted can be looked at but not changed (the server refuses writes too).
  const editable = !!tree?.is_active
  const editingOn = editMode && editable
  const selected = selectedId !== null ? byId.get(selectedId) : undefined
  const goTo = (id: number) => {
    setSelectedId(id)
    setFocus((f) => ({ id, n: (f?.n ?? 0) + 1 }))
  }

  const toggleEditMode = () => {
    if (editMode) {
      setEditing(null)
      setUndo(null)
      setShowDeleted(false)
    }
    setEditMode(!editMode)
  }

  const offerUndo = (message: string, run: () => Promise<void>) =>
    setUndo((u) => ({ key: (u?.key ?? 0) + 1, message, run }))
  const onDeleted = (snapshot: MemberSnapshot) => {
    setSelectedId(null)
    offerUndo(`Deleted ${fullName(snapshot.member)}`, async () => {
      const back = await restore.member(snapshot)
      goTo(back.id)
    })
  }
  const onRelationshipRemoved = (rel: Relationship, description: string) =>
    offerUndo(description, () => restore.relationship(rel))

  return (
    <div className="tree-page">
      <div className="tree-head">
        <div className="tree-title rise">
          <Link to="/staff/trees" className="back">
            <Back size={15} /> All trees
          </Link>
          <h1>{tree?.tree_name ?? 'Family tree'}</h1>
          {tree && (
            <div className="stats">
              <span className="chip">
                <b>{memberList.length}</b> {memberList.length === 1 ? 'person' : 'people'}
              </span>
              {generations > 0 && (
                <span className="chip">
                  <b>{generations}</b> {generations === 1 ? 'generation' : 'generations'}
                </span>
              )}
            </div>
          )}
        </div>

        {tree && (
          <div className="tree-tools rise" style={{ '--i': 1 } as React.CSSProperties}>
            {editingOn && (
              <button onClick={() => setEditing('new')}>
                <Plus size={16} /> Add person
              </button>
            )}
            {editingOn && (
              <button className="ghost" onClick={() => setShowDeleted(true)}>
                Recently deleted
              </button>
            )}
            <button
              className={editingOn ? 'danger' : 'ghost'}
              aria-pressed={editingOn}
              disabled={!editable}
              title={editable ? undefined : 'This family was deleted by its owner, so it cannot be edited'}
              onClick={toggleEditMode}
            >
              {editingOn ? 'Stop editing' : 'Edit this tree'}
            </button>
          </div>
        )}
      </div>

      {tree && (
        <p className={`staff-banner${editingOn ? ' editing' : ''}`} role="note">
          {editingOn
            ? 'Editing as staff · changes are live, recorded in this family’s edit history as staff edits, and visible to its owner'
            : 'Viewing as staff · read-only'}
          {' · '}Owner: {fullName(tree.owner) || tree.owner.email} ({tree.owner.email})
          {!tree.is_active && ' · Deleted by its owner'}
        </p>
      )}

      <div className="workspace">
        <Rings className="workspace-rings" seed={treeId * 7 + 3} count={22} />

        {detail.isLoading && (
          <div className="empty" role="status">
            <div className="skeleton" style={{ width: 216, height: 80, borderRadius: 22 }} />
          </div>
        )}

        {detail.error && (
          <div className="empty">
            <p role="alert" className="error">
              Failed to load: {detail.error.message}
            </p>
            <button onClick={() => void detail.refetch()}>Retry</button>
          </div>
        )}

        {tree && <TreeConflictNotice conflicts={conflicts} />}
        {tree && forest.length > 0 && (
          <TreeView forest={forest} genders={genders} selectedId={selectedId} onSelect={setSelectedId} focus={focus} />
        )}

        {tree && forest.length === 0 && (
          <div className="empty">
            <h2>No one in this family yet</h2>
            {editingOn && (
              <button onClick={() => setEditing('new')}>
                <Plus size={16} /> Add the first person
              </button>
            )}
          </div>
        )}

        {selected && tree && (
          <DetailPanel
            key={selected.id}
            treeId={tree.id}
            member={selected}
            members={memberList}
            relationships={detail.data?.relationships ?? []}
            canDelete={editingOn}
            readOnly={!editingOn}
            onEdit={() => setEditing(selected)}
            onDeleted={editingOn ? onDeleted : nothing}
            onRelationshipRemoved={editingOn ? onRelationshipRemoved : nothing}
            onSelect={goTo}
            onClose={() => setSelectedId(null)}
          />
        )}
      </div>

      {editingOn && undo && <UndoBar undo={undo} onDone={() => setUndo(null)} />}

      {editingOn && showDeleted && (
        <RecentlyDeleted
          treeId={treeId}
          onClose={() => setShowDeleted(false)}
          onRestored={(id) => {
            setShowDeleted(false)
            goTo(id)
          }}
        />
      )}

      {editingOn && editing && tree && (
        <MemberForm
          treeId={tree.id}
          members={memberList}
          member={editing === 'new' ? undefined : editing}
          onClose={() => setEditing(null)}
          onSaved={(m) => {
            setEditing(null)
            goTo(m.id)
          }}
        />
      )}
    </div>
  )
}
