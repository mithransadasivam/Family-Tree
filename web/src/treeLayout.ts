import { useMemo } from 'react'
import { buildForest, canonicalOrder, countPeople, findRoots, inferGenders } from './graph'
import { assignGenerations, drawableGraph } from './generations'
import type { Member, Relationship } from './types'

/**
 * The tree for a family's people and relationships, as plain data (the hook below wraps this).
 *
 * Rows come from `assignGenerations`, a function of the links alone, so the picture does not
 * depend on the order people or links were added in. If links contradict each other (usually one
 * stored the wrong way round) the most likely culprit is left out of the DRAWING and listed in
 * `conflicts` so the page can say so; the data itself is never touched.
 */
export function computeTreeLayout(memberList: Member[], relList: Relationship[]) {
  const byId = new Map(memberList.map((m) => [m.id, m]))
  const { graph, ignored } = drawableGraph(relList, memberList)
  const gens = assignGenerations(graph, memberList.map((m) => m.id))
  // Every family line is drawn, so in-laws' parents are never hidden. The biggest connected
  // family goes first (leftmost); smaller or unconnected ones follow. Equal sizes are settled by
  // who the people are, never by ids.
  const candidates = findRoots(memberList, graph).map((m) => m.id)
  if (candidates.length === 0 && memberList.length > 0) {
    candidates.push([...memberList].sort(canonicalOrder)[0].id)
  }
  let forest: ReturnType<typeof buildForest> = []
  let bestSize = -1
  for (const id of candidates) {
    const f = buildForest(id, byId, graph, gens)
    const size = f[0] ? countPeople(f[0]) : 0
    if (size > bestSize) {
      forest = f
      bestSize = size
    }
  }
  const generations = memberList.length ? Math.max(...memberList.map((m) => gens.get(m.id) ?? 0)) + 1 : 0
  return { byId, graph, gens, forest, generations, conflicts: ignored }
}

/**
 * Everything the tree canvas needs, worked out from a family's people and relationships.
 * Shared by the family page and the superuser's read-only staff view so both draw identically.
 */
export function useTreeLayout(members: Member[] | undefined, relationships: Relationship[] | undefined) {
  const memberList = useMemo(() => members ?? [], [members])
  const relList = useMemo(() => relationships ?? [], [relationships])
  const { byId, forest, generations, conflicts } = useMemo(
    () => computeTreeLayout(memberList, relList),
    [memberList, relList],
  )
  const genders = useMemo(() => inferGenders(relList, memberList), [relList, memberList])
  return { memberList, relList, byId, forest, generations, genders, conflicts }
}
