import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { assignGenerations, drawableGraph, generationConflicts } from './generations'
import { buildGraph, parentEdgeOf } from './graph'
import { layoutForest, unitWidth } from './layout'
import TreeConflictNotice from './TreeConflictNotice'
import { computeTreeLayout } from './treeLayout'
import type { Member, Relationship } from './types'

const person = (id: number, first_name: string, gender: Member['gender'] = '', birth_date: string | null = null): Member =>
  ({ id, tree: 1, first_name, last_name: '', gender, phone: '', phone_public: false, email: '', address: '',
     user: null, photo_url: '', birth_date, birth_place: '', death_date: null, death_place: '' }) as Member
let relId = 1000
const rel = (a: number, type: string, b: number): Relationship =>
  ({ id: relId++, tree: 1, member_1: a, member_2: b, relationship_type: 0, relationship_type_name: type }) as Relationship

/** Row of each person BY NAME after the full pipeline (what the page draws). */
function rowsByName(members: Member[], rels: Relationship[]) {
  const { forest, byId } = computeTreeLayout(members, rels)
  const out = new Map<string, number>()
  layoutForest(forest).placed.forEach((p) => p.unit.people.forEach((m) => out.set(byId.get(m.id)!.first_name, p.depth)))
  return out
}

function permutations<T>(xs: T[]): T[][] {
  if (xs.length <= 1) return [xs]
  return xs.flatMap((x, i) => permutations([...xs.slice(0, i), ...xs.slice(i + 1)]).map((p) => [x, ...p]))
}

// The family from the bug report: "Siva Sankar". Row 134 was stored the wrong way round.
const ROLES = ['Sivananthan', 'Jayalakshmi', 'Sivasankaran', 'Amutha', 'Pooja', 'Teja', 'Inbashri']
const GENDER: Record<string, Member['gender']> = { Sivananthan: 'male', Jayalakshmi: 'female', Sivasankaran: 'male', Amutha: 'female' }
type Edge = [string, string, string]
const common: Edge[] = [
  ['Sivasankaran', 'Son', 'Sivananthan'], // row 140
  ['Pooja', 'Daughter', 'Sivasankaran'], ['Teja', 'Daughter', 'Sivasankaran'], ['Inbashri', 'Daughter', 'Sivasankaran'],
  ['Amutha', 'Spouse', 'Sivasankaran'], ['Sivananthan', 'Spouse', 'Jayalakshmi'],
]
const build = (ids: number[], extra: Edge[]) => {
  const id = (n: string) => ids[ROLES.indexOf(n)]
  const members = ROLES.map((n) => person(id(n), n, GENDER[n] ?? '')).sort((a, b) => a.id - b.id)
  return { members, rels: [...common, ...extra].map(([a, t, b]) => rel(id(a), t, id(b))) }
}
const EXPECT = { Sivananthan: 0, Jayalakshmi: 0, Sivasankaran: 1, Amutha: 1, Pooja: 2, Teja: 2, Inbashri: 2 }

describe('the reported family (row 134 stored backwards)', () => {
  const backwards: Edge[] = [['Sivasankaran', 'Mother', 'Jayalakshmi']]
  const correct: Edge[] = [['Jayalakshmi', 'Mother', 'Sivasankaran']]

  it('draws the same, correct rows for every order the people could have been added in', () => {
    for (const ids of permutations([1, 2, 3, 4, 5, 6, 7])) {
      const { members, rels } = build(ids, backwards)
      expect(Object.fromEntries(rowsByName(members, rels))).toEqual(EXPECT)
    }
  })

  it('names the backwards link and leaves it out of the drawing', () => {
    const { members, rels } = build([1, 2, 3, 4, 5, 6, 7], backwards)
    const { conflicts } = computeTreeLayout(members, rels)
    expect(conflicts.map((c) => c.reads)).toEqual(['Sivasankaran is the Mother of Jayalakshmi'])
    expect(conflicts[0].why).toMatch(/gender/)
  })

  it('reports nothing when the same link is entered correctly', () => {
    const { members, rels } = build([1, 2, 3, 4, 5, 6, 7], correct)
    expect(computeTreeLayout(members, rels).conflicts).toEqual([])
    expect(Object.fromEntries(rowsByName(members, rels))).toEqual(EXPECT)
  })

  it('leaves the stored relationships untouched', () => {
    const { members, rels } = build([1, 2, 3, 4, 5, 6, 7], backwards)
    const before = JSON.stringify(rels)
    computeTreeLayout(members, rels)
    expect(JSON.stringify(rels)).toBe(before)
  })
})

describe('production shape: no genders recorded, the wrong link is the older one', () => {
  // Real ids from the "Siva sankar" tree. Row 134 (old Android build) is older than row 140.
  const ms = [person(44, 'Sivasankaran S'), person(45, 'Amutha Siva'), person(50, 'Jayalakshmi'), person(58, 'Sivananthan'),
    person(60, 'Pooja'), person(61, 'Teja'), person(62, 'Inba')]
  const withIds = (ids: [number, number, string, number][]) =>
    ids.map(([id, a, t, b]) => ({ id, tree: 13, member_1: a, member_2: b, relationship_type: 0, relationship_type_name: t }) as Relationship)
  const rels = withIds([[91, 45, 'Spouse', 44], [94, 62, 'Daughter', 44], [95, 61, 'Daughter', 44], [96, 60, 'Daughter', 44],
    [132, 58, 'Spouse', 50], [134, 44, 'Mother', 50], [140, 44, 'Son', 58]])

  it('sets aside the older link, draws the family the right way up, and says what else to check', () => {
    const { conflicts } = computeTreeLayout(ms, rels)
    expect(conflicts.map((c) => c.id)).toEqual([134])
    expect(conflicts[0].alsoCheck).toEqual(['Sivasankaran S is the Son of Sivananthan'])
    expect(Object.fromEntries(rowsByName(ms, rels))).toEqual({
      Sivananthan: 0, Jayalakshmi: 0, 'Sivasankaran S': 1, 'Amutha Siva': 1, Pooja: 2, Teja: 2, Inba: 2,
    })
  })

  it('does the same whatever order the links arrive in', () => {
    expect(computeTreeLayout(ms, [...rels].reverse()).conflicts.map((c) => c.id)).toEqual([134])
  })

  it('names the other conflicting link in the notice', () => {
    const { conflicts } = computeTreeLayout(ms, rels)
    render(<TreeConflictNotice conflicts={conflicts} />)
    expect(screen.getByRole('alert').textContent).toContain('conflicts with: Sivasankaran S is the Son of Sivananthan')
  })
})

describe('generationConflicts', () => {
  const conflicts = (rels: Relationship[]) => generationConflicts(buildGraph(rels))
  it('sees a contradiction that only shows up through a couple', () => {
    const c = conflicts([rel(1, 'Husband', 2), rel(1, 'Father', 3), rel(3, 'Father', 2)])
    expect([...c.people].sort()).toEqual([1, 2, 3])
  })
  it('sees a plain parent loop', () => {
    expect(conflicts([rel(1, 'Father', 2), rel(2, 'Father', 3), rel(3, 'Father', 1)]).edges.size).toBe(3)
  })
  it('does not flag a normal family, or a marriage between two lineages', () => {
    expect(conflicts([rel(1, 'Husband', 2), rel(1, 'Father', 3), rel(2, 'Mother', 3),
      rel(3, 'Husband', 4), rel(5, 'Father', 4)]).edges.size).toBe(0)
  })
})

// ---------------------------------------------------------------------------------------
// Random families: rows must satisfy every link and must not depend on ids.
// ---------------------------------------------------------------------------------------
function rng(seed: number) {
  let s = seed >>> 0
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 2 ** 32)
}

/** People are named by a stable label; ids are assigned later so they can be shuffled. */
function family(seed: number) {
  const r = rng(seed)
  const pick = <T,>(xs: T[]) => xs[Math.floor(r() * xs.length)]
  const names: string[] = []
  const edges: Edge[] = []
  const gen: string[][] = [[], [], [], []]
  const make = (g: number) => { const n = `p${names.length}`; names.push(n); gen[g].push(n); return n }
  const roots = 1 + Math.floor(r() * 2)
  for (let i = 0; i < roots; i++) make(0)
  for (let g = 0; g < 3; g++) {
    for (const p of [...gen[g]]) {
      if (r() < 0.75) {
        const mates: string[] = []
        for (let s = 0, n = r() < 0.2 ? 2 : 1; s < n; s++) { const sp = make(g); mates.push(sp); edges.push([p, pick(['Husband', 'Wife', 'Spouse']), sp]) }
        for (let k = 0, kids = Math.floor(r() * 3); k < kids; k++) {
          const c = make(g + 1)
          const flip = r() < 0.4
          for (const par of r() < 0.8 ? [p, mates[0]] : [p]) edges.push(flip ? [c, pick(['Son', 'Daughter']), par] : [par, pick(['Father', 'Mother']), c])
        }
      }
    }
  }
  for (const n of [...names]) { // married-in people sometimes have their own recorded parents
    if (r() < 0.25 && !edges.some(([, t, b]) => ['Father', 'Mother'].includes(t) && b === n)) {
      const pa = `q${names.length}`
      names.push(pa)
      edges.push([pa, 'Father', n])
    }
  }
  if (r() < 0.3 && gen[2].length) edges.push([gen[0][0], 'Grandfather', gen[2][0]])
  return { names, edges }
}

const instance = (f: ReturnType<typeof family>, ids: number[], order: Edge[]) => ({
  members: f.names.map((n, i) => person(ids[i], n)).sort((a, b) => a.id - b.id),
  rels: order.map(([a, t, b]) => rel(ids[f.names.indexOf(a)], t, ids[f.names.indexOf(b)])),
})

describe('random families', () => {
  it('put every parent strictly above their child (grandparent links two rows), with no overlapping cards', () => {
    let bad = 0
    for (let seed = 1; seed <= 1500; seed++) {
      const f = family(seed)
      const ids = f.names.map((_, i) => i + 1)
      const { members, rels } = instance(f, ids, f.edges)
      const { forest, byId, graph, conflicts } = computeTreeLayout(members, rels)
      expect(conflicts, `seed ${seed}`).toEqual([]) // these families are consistent
      const { placed } = layoutForest(forest)
      const row = new Map<number, number>()
      placed.forEach((p) => p.unit.people.forEach((m) => row.set(m.id, p.depth)))
      for (const r of rels) {
        const e = parentEdgeOf(r)
        if (!e || !graph.children.get(e[0])?.has(e[1])) continue
        const need = graph.skips.has(`${e[0]}>${e[1]}`) ? 2 : 1
        if ((row.get(e[1]) ?? 0) - (row.get(e[0]) ?? 0) < need) bad++
      }
      expect(byId.size).toBe(members.length)
      const rows = new Map<number, { l: number; r: number }[]>()
      for (const p of placed) rows.set(p.depth, [...(rows.get(p.depth) ?? []), { l: p.cx - unitWidth(p.unit) / 2, r: p.cx + unitWidth(p.unit) / 2 }])
      for (const spans of rows.values()) {
        spans.sort((a, b) => a.l - b.l)
        for (let i = 1; i < spans.length; i++) expect(spans[i].l, `seed ${seed} overlap`).toBeGreaterThanOrEqual(spans[i - 1].r - 0.01)
      }
    }
    expect(bad).toBe(0)
  })

  it('draw the same rows however ids and links are ordered', () => {
    for (let seed = 1; seed <= 400; seed++) {
      const f = family(seed)
      const r = rng(seed * 7919)
      const shuffle = <T,>(xs: T[]) => xs.map((x) => [r(), x] as const).sort((a, b) => a[0] - b[0]).map((x) => x[1])
      const base = instance(f, f.names.map((_, i) => i + 1), f.edges)
      const expected = Object.fromEntries(rowsByName(base.members, base.rels))
      for (let k = 0; k < 3; k++) {
        const ids = shuffle(f.names.map((_, i) => i + 1))
        const other = instance(f, ids, shuffle(f.edges))
        expect(Object.fromEntries(rowsByName(other.members, other.rels)), `seed ${seed}`).toEqual(expected)
      }
    }
  })

  it('assign generations as a pure function of the links', () => {
    const g = buildGraph([rel(1, 'Husband', 2), rel(1, 'Father', 3), rel(3, 'Husband', 4), rel(5, 'Father', 4), rel(6, 'Father', 5)])
    const gens = assignGenerations(g, [1, 2, 3, 4, 5, 6])
    expect(Object.fromEntries(gens)).toEqual({ 1: 1, 2: 1, 3: 2, 4: 2, 5: 1, 6: 0 })
  })
})

describe('drawableGraph', () => {
  it('breaks a contradiction deterministically even without gender information', () => {
    const members = [1, 2, 3].map((i) => person(i, `n${i}`))
    const rels = [rel(1, 'Father', 2), rel(2, 'Father', 3), rel(3, 'Father', 1)]
    const a = drawableGraph(rels, members)
    const b = drawableGraph([...rels].reverse(), [...members].reverse())
    expect(a.ignored.map((i) => i.reads)).toEqual(b.ignored.map((i) => i.reads))
    expect(a.ignored).toHaveLength(1)
    expect(generationConflicts(a.graph).edges.size).toBe(0)
  })
})

describe('TreeConflictNotice', () => {
  it('says which link is not drawn, and renders nothing when there is no conflict', () => {
    const { container, rerender } = render(<TreeConflictNotice conflicts={[]} />)
    expect(container.innerHTML).toBe('')
    rerender(<TreeConflictNotice conflicts={[{ id: 134, reads: 'Ann is the Mother of Bob', why: 'it contradicts the other links', alsoCheck: [], memberIds: [1, 2] }]} />)
    expect(screen.getByRole('alert').textContent).toContain('Ann is the Mother of Bob')
  })
})
