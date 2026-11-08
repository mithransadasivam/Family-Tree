import { buildGraph, FEMALE_TYPES, MALE_TYPES, parentEdgeOf, type Graph } from './graph'
import { fullName, type Member, type Relationship } from './types'

/**
 * Generations: which row each person belongs on, worked out from the links ALONE.
 *
 * Every link pins generations down: a couple share one, a parent is above their child (a
 * grandparent two above). Drawing by "how deep am I in the branch I was reached through" breaks
 * whenever two branches disagree (a married-in spouse whose family is recorded deeper than their
 * partner's). Solving for rows directly makes them a pure function of the relationships: the
 * order people or links were entered in, and which family is drawn first, cannot change them.
 *
 * A tree can also contain links that cannot all be true together - typically one stored the wrong
 * way round - e.g. Ann is Ben's father, Ben is Cara's father, and Ann and Cara are a couple. No
 * rows satisfy that. `drawableGraph` finds such contradictions, sets aside the link most likely
 * to be wrong (for drawing only; nothing is changed in the data) and says which.
 */

/** Weight of a parent link: 1 row, or 2 for a grandparent link drawn without the middle person. */
type Edge = readonly [ancestor: number, descendant: number, rows: number]

interface Contracted {
  find: (x: number) => number
  out: Map<number, Map<number, number>> // couple-node -> child couple-node -> rows
  nodes: Set<number>
  /** Couple-nodes on a contradiction: a parent link back to themselves, or a loop of them. */
  bad: Set<number>
  scc: Map<number, number>
}

function contract(g: Graph, ids: Iterable<number>): Contracted {
  const parent = new Map<number, number>()
  const find = (x: number): number => {
    if (!parent.has(x)) parent.set(x, x)
    let r = x
    while (parent.get(r) !== r) r = parent.get(r)!
    while (parent.get(x) !== r) {
      const next = parent.get(x)!
      parent.set(x, r)
      x = next
    }
    return r
  }
  const people = new Set<number>(ids)
  g.spouses.forEach((set, a) => set.forEach((b) => parent.set(find(a), find(b))))
  const edges: Edge[] = []
  g.children.forEach((kids, a) => kids.forEach((d) => edges.push([a, d, g.skips.has(`${a}>${d}`) ? 2 : 1])))
  edges.forEach(([a, d]) => {
    people.add(a)
    people.add(d)
  })

  const out = new Map<number, Map<number, number>>()
  const bad = new Set<number>()
  const nodes = new Set<number>()
  people.forEach((p) => nodes.add(find(p)))
  for (const [a, d, w] of edges) {
    const ca = find(a)
    const cd = find(d)
    if (ca === cd) {
      bad.add(ca)
      continue
    }
    if (!out.has(ca)) out.set(ca, new Map())
    out.get(ca)!.set(cd, Math.max(w, out.get(ca)!.get(cd) ?? 0))
  }

  // Strongly connected components (iterative Tarjan): any of 2+ nodes is a loop.
  const index = new Map<number, number>()
  const low = new Map<number, number>()
  const onStack = new Set<number>()
  const stack: number[] = []
  const scc = new Map<number, number>()
  let counter = 0
  for (const root of [...nodes].sort((x, y) => x - y)) {
    if (index.has(root)) continue
    const work: [number, Iterator<number>][] = [[root, (out.get(root)?.keys() ?? [].values()) as Iterator<number>]]
    index.set(root, counter)
    low.set(root, counter++)
    stack.push(root)
    onStack.add(root)
    while (work.length) {
      const [node, it] = work[work.length - 1]
      let descended = false
      for (let n = it.next(); !n.done; n = it.next()) {
        const nxt = n.value
        if (!index.has(nxt)) {
          index.set(nxt, counter)
          low.set(nxt, counter++)
          stack.push(nxt)
          onStack.add(nxt)
          work.push([nxt, (out.get(nxt)?.keys() ?? [].values()) as Iterator<number>])
          descended = true
          break
        }
        if (onStack.has(nxt)) low.set(node, Math.min(low.get(node)!, index.get(nxt)!))
      }
      if (descended) continue
      work.pop()
      if (work.length) {
        const up = work[work.length - 1][0]
        low.set(up, Math.min(low.get(up)!, low.get(node)!))
      }
      if (low.get(node) === index.get(node)) {
        const members: number[] = []
        let w: number
        do {
          w = stack.pop()!
          onStack.delete(w)
          members.push(w)
        } while (w !== node)
        members.forEach((m) => scc.set(m, node))
        if (members.length > 1) members.forEach((m) => bad.add(m))
      }
    }
  }
  return { find, out, nodes, bad, scc }
}

/** The parent links (as `${ancestor}>${descendant}`) and people caught in a contradiction. */
export function generationConflicts(g: Graph, ids: Iterable<number> = []) {
  const c = contract(g, ids)
  const edges = new Set<string>()
  const people = new Set<number>()
  g.children.forEach((kids, a) =>
    kids.forEach((d) => {
      const ca = c.find(a)
      const cd = c.find(d)
      if (ca === cd || (c.bad.has(ca) && c.scc.get(ca) === c.scc.get(cd))) {
        edges.add(`${a}>${d}`)
        people.add(a)
        people.add(d)
      }
    }),
  )
  return { edges, people }
}

/**
 * Row (0 = top) for every person. Parents sit directly above their lowest child; couples share a
 * row; each separate family starts at 0. Only meaningful for a graph with no contradiction
 * (see `drawableGraph`); people on one are left on row 0.
 */
export function assignGenerations(g: Graph, ids: Iterable<number>): Map<number, number> {
  const c = contract(g, ids)
  const gen = new Map<number, number>()
  const indeg = new Map<number, number>()
  c.nodes.forEach((n) => indeg.set(n, 0))
  c.out.forEach((kids) => kids.forEach((_, k) => indeg.set(k, (indeg.get(k) ?? 0) + 1)))

  // Topological order (ties broken by node id only so the walk itself is repeatable; the
  // resulting rows do not depend on it).
  const order: number[] = []
  const ready = [...c.nodes].filter((n) => indeg.get(n) === 0).sort((a, b) => a - b)
  while (ready.length) {
    const n = ready.shift()!
    order.push(n)
    c.out.get(n)?.forEach((_, k) => {
      indeg.set(k, indeg.get(k)! - 1)
      if (indeg.get(k) === 0) ready.push(k)
    })
  }
  const cyclic = order.length !== c.nodes.size
  if (cyclic) return new Map([...ids].map((id) => [id, 0]))

  order.forEach((n) => gen.set(n, gen.get(n) ?? 0))
  for (const n of order) c.out.get(n)?.forEach((w, k) => gen.set(k, Math.max(gen.get(k) ?? 0, gen.get(n)! + w)))
  // Pull parents down so each sits right above its nearest child instead of floating at the top.
  for (const n of [...order].reverse()) {
    const kids = c.out.get(n)
    if (kids?.size) gen.set(n, Math.min(...[...kids].map(([k, w]) => gen.get(k)! - w)))
  }

  // Each connected family starts at row 0.
  const comp = new Map<number, number>()
  const cparent = new Map<number, number>()
  const cfind = (x: number): number => {
    while ((cparent.get(x) ?? x) !== x) x = cparent.get(x)!
    return x
  }
  c.out.forEach((kids, a) => kids.forEach((_, k) => cparent.set(cfind(a), cfind(k))))
  const min = new Map<number, number>()
  c.nodes.forEach((n) => {
    const r = cfind(n)
    comp.set(n, r)
    min.set(r, Math.min(min.get(r) ?? Infinity, gen.get(n)!))
  })
  const result = new Map<number, number>()
  for (const id of ids) {
    const n = c.find(id)
    result.set(id, gen.get(n)! - min.get(comp.get(n)!)!)
  }
  return result
}

export interface IgnoredLink {
  id: number
  /** "Ann is the Mother of Ben": the way the stored link reads. */
  reads: string
  /** Why this one was chosen. */
  why: string
  /** The other links in the same conflict. Any one of them could be the one entered wrongly. */
  alsoCheck: string[]
  memberIds: [number, number]
}

const reads = (r: Relationship, byId: Map<number, Member>) => {
  const n = (id: number) => {
    const m = byId.get(id)
    return m ? fullName(m) || `#${id}` : `#${id}`
  }
  return `${n(r.member_1)} is the ${r.relationship_type_name} of ${n(r.member_2)}`
}

/** True when the link says member_1 is one gender but their profile records the other. */
function contradictsGender(r: Relationship, byId: Map<number, Member>) {
  const want = MALE_TYPES.has(r.relationship_type_name) ? 'male' : FEMALE_TYPES.has(r.relationship_type_name) ? 'female' : null
  const have = byId.get(r.member_1)?.gender
  return want !== null && (have === 'male' || have === 'female') && have !== want
}

/**
 * The relationship graph to DRAW. If the links contradict each other about generations, set aside
 * one parent link at a time until the rest is consistent. The pick: a link that contradicts its
 * person's recorded gender first (the usual sign of one stored backwards); with no gender evidence,
 * the OLDEST link, because links saved by older app versions (before the direction fix of
 * 2026-11-04) are the ones known to be backwards. Ties fall to how the link reads, never to member
 * ids. Nothing is deleted or edited.
 */
export function drawableGraph(rels: Relationship[], members: Member[]) {
  const byId = new Map(members.map((m) => [m.id, m]))
  const ids = members.map((m) => m.id)
  const ignored: IgnoredLink[] = []
  let kept = rels
  for (let guard = 0; guard <= rels.length; guard++) {
    const graph = buildGraph(kept)
    const bad = generationConflicts(graph, ids)
    if (bad.edges.size === 0) return { graph, ignored, kept }
    const cands = kept
      .filter((r) => {
        const e = parentEdgeOf(r)
        return e !== null && bad.edges.has(`${e[0]}>${e[1]}`)
      })
      .map((r) => ({ r, gender: contradictsGender(r, byId), text: reads(r, byId) }))
      .sort(
        (a, b) =>
          Number(b.gender) - Number(a.gender) || a.r.id - b.r.id || (a.text < b.text ? -1 : a.text > b.text ? 1 : 0),
      )
    if (!cands.length) return { graph, ignored, kept }
    const { r, gender, text } = cands[0]
    ignored.push({
      id: r.id,
      reads: text,
      memberIds: [r.member_1, r.member_2],
      why: gender
        ? 'the person’s recorded gender does not match this link, so it was probably entered the wrong way round'
        : 'it contradicts the other links and is the oldest of them, so it is the likeliest to have been entered the wrong way round',
      alsoCheck: cands.slice(1).map((c) => c.text),
    })
    kept = kept.filter((x) => x !== r)
  }
  return { graph: buildGraph(kept), ignored, kept }
}
