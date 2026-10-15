import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import DetailPanel from './DetailPanel'
import { Back, Gear, Plus, Search } from './Icons'
import MemberForm from './MemberForm'
import { useMembers, useRelationships, useTrees } from './queries'
import Rings from './Rings'
import TreeView from './TreeView'
import { buildForest, buildGraph, countPeople, depthOf, findRoots } from './graph'
import { fullName, type Member } from './types'

export default function TreePage() {
  const treeId = Number(useParams().treeId)
  const trees = useTrees()
  const members = useMembers(treeId)
  const rels = useRelationships(treeId)

  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [focus, setFocus] = useState<{ id: number; n: number } | null>(null)
  const [editing, setEditing] = useState<Member | 'new' | null>(null)
  const [query, setQuery] = useState('')

  const memberList = useMemo(() => members.data ?? [], [members.data])
  const byId = useMemo(() => new Map(memberList.map((m) => [m.id, m])), [memberList])
  const graph = useMemo(() => buildGraph(rels.data ?? []), [rels.data])
  // Every family line is drawn, so in-laws' parents are never hidden. The biggest connected
  // family goes first (leftmost); smaller or unconnected ones follow.
  const forest = useMemo(() => {
    const candidates = findRoots(memberList, graph).map((m) => m.id)
    if (candidates.length === 0 && memberList.length > 0) candidates.push(memberList[0].id)
    let best: ReturnType<typeof buildForest> = []
    let bestSize = -1
    for (const id of candidates) {
      const f = buildForest(id, byId, graph)
      const size = f[0] ? countPeople(f[0]) : 0
      if (size > bestSize) {
        best = f
        bestSize = size
      }
    }
    return best
  }, [memberList, byId, graph])
  const generations = Math.max(0, ...forest.map(depthOf))

  const selected = selectedId !== null ? byId.get(selectedId) : undefined
  const matches = query.trim()
    ? memberList.filter((m) => fullName(m).toLowerCase().includes(query.trim().toLowerCase())).slice(0, 8)
    : []

  const goTo = (id: number) => {
    setSelectedId(id)
    setFocus((f) => ({ id, n: (f?.n ?? 0) + 1 }))
  }

  const tree = trees.data?.find((t) => t.id === treeId)
  const loading = members.isLoading || rels.isLoading
  const error = members.error ?? rels.error

  return (
    <div className="tree-page">
      <div className="tree-head">
        <div className="tree-title rise">
          <Link to="/" className="back">
            <Back size={15} /> All trees
          </Link>
          <h1>{tree?.tree_name ?? 'Family tree'}</h1>
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
        </div>

        <div className="tree-tools rise" style={{ '--i': 1 } as React.CSSProperties}>
          <div className="search">
            <Search size={16} />
            <input
              type="search"
              placeholder="Find a person…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Search members"
            />
            {query.trim() && (
              <ul className="search-results">
                {matches.map((m) => (
                  <li key={m.id}>
                    <button
                      onClick={() => {
                        goTo(m.id)
                        setQuery('')
                      }}
                    >
                      {fullName(m)}
                    </button>
                  </li>
                ))}
                {matches.length === 0 && <li className="none">No one by that name</li>}
              </ul>
            )}
          </div>
          <Link to={`/trees/${treeId}/manage`} className="btn-link">
            <Gear size={16} /> <span className="label">Manage</span>
          </Link>
          <button onClick={() => setEditing('new')}>
            <Plus size={16} /> Add person
          </button>
        </div>
      </div>

      <div className="workspace">
        <Rings className="workspace-rings" seed={treeId * 7 + 3} count={22} />

        {loading && (
          <div className="empty" role="status">
            <div className="skeleton" style={{ width: 216, height: 80, borderRadius: 22 }} />
            <div className="row">
              <div className="skeleton" style={{ width: 216, height: 80, borderRadius: 22 }} />
              <div className="skeleton" style={{ width: 216, height: 80, borderRadius: 22 }} />
            </div>
          </div>
        )}

        {error && (
          <div className="empty">
            <p role="alert" className="error">
              Failed to load: {error.message}
            </p>
            <button
              onClick={() => {
                void members.refetch()
                void rels.refetch()
              }}
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && forest.length > 0 && (
          <TreeView forest={forest} selectedId={selectedId} onSelect={setSelectedId} focus={focus} />
        )}

        {!loading && !error && forest.length === 0 && (
          <div className="empty">
            <Rings className="art" seed={5} count={9} />
            <h2>Every tree starts with one person</h2>
            <p className="muted">Add the first member, then connect everyone else around them.</p>
            <button onClick={() => setEditing('new')}>
              <Plus size={16} /> Add the first person
            </button>
          </div>
        )}

        {selected && (
          <DetailPanel
            key={selected.id}
            treeId={treeId}
            member={selected}
            members={memberList}
            relationships={rels.data ?? []}
            onEdit={() => setEditing(selected)}
            onDeleted={() => setSelectedId(null)}
            onSelect={goTo}
            onClose={() => setSelectedId(null)}
          />
        )}
      </div>

      {editing && (
        <MemberForm
          treeId={treeId}
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
