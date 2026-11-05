import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import DetailPanel from './DetailPanel'
import { Back } from './Icons'
import { useStaffTree } from './queries'
import Rings from './Rings'
import { useTreeLayout } from './treeLayout'
import TreeView from './TreeView'
import { fullName } from './types'

const nothing = () => undefined

/**
 * Superuser only: any family drawn exactly as its members see it, but strictly look-don't-touch.
 * The same canvas and the same layout code as the family page; none of the editing controls, and
 * the data comes from the read-only /api/staff/ endpoints (no membership needed, GET only).
 */
export default function StaffTreePage() {
  const treeId = Number(useParams().treeId)
  const detail = useStaffTree(treeId)
  const { memberList, byId, forest, generations, genders } = useTreeLayout(
    detail.data?.members,
    detail.data?.relationships,
  )
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [focus, setFocus] = useState<{ id: number; n: number } | null>(null)

  const tree = detail.data?.tree
  const selected = selectedId !== null ? byId.get(selectedId) : undefined
  const goTo = (id: number) => {
    setSelectedId(id)
    setFocus((f) => ({ id, n: (f?.n ?? 0) + 1 }))
  }

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
      </div>

      {tree && (
        <p className="staff-banner" role="note">
          Viewing as staff · read-only · Owner: {fullName(tree.owner) || tree.owner.email} ({tree.owner.email})
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

        {tree && forest.length > 0 && (
          <TreeView forest={forest} genders={genders} selectedId={selectedId} onSelect={setSelectedId} focus={focus} />
        )}

        {tree && forest.length === 0 && (
          <div className="empty">
            <h2>No one in this family yet</h2>
          </div>
        )}

        {selected && tree && (
          <DetailPanel
            key={selected.id}
            treeId={tree.id}
            member={selected}
            members={memberList}
            relationships={detail.data?.relationships ?? []}
            canDelete={false}
            readOnly
            onEdit={nothing}
            onDeleted={nothing}
            onRelationshipRemoved={nothing}
            onSelect={goTo}
            onClose={() => setSelectedId(null)}
          />
        )}
      </div>
    </div>
  )
}
