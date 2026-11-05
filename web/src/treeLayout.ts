import { useMemo } from 'react'
import { buildForest, buildGraph, countPeople, depthOf, findRoots, inferGenders } from './graph'
import type { Member, Relationship } from './types'

/**
 * Everything the tree canvas needs, worked out from a family's people and relationships.
 * Shared by the family page and the superuser's read-only staff view so both draw identically.
 */
export function useTreeLayout(members: Member[] | undefined, relationships: Relationship[] | undefined) {
  const memberList = useMemo(() => members ?? [], [members])
  const relList = useMemo(() => relationships ?? [], [relationships])
  const byId = useMemo(() => new Map(memberList.map((m) => [m.id, m])), [memberList])
  const graph = useMemo(() => buildGraph(relList), [relList])
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
  const genders = useMemo(() => inferGenders(relList, memberList), [relList, memberList])
  return { memberList, relList, byId, forest, generations, genders }
}
