import { describe, expect, it } from 'vitest'
import { assignGenerations, drawableGraph } from './generations'
import { buildForest, classify, inferGenders, type Unit } from './graph'
import type { Member, Relationship } from './types'

/**
 * Random family trees, thrown at the layout code. Part of the Groot run (groot/run_all.py): each
 * run uses a new seed, printed on failure, and GROOT_SEED=<n> replays one exactly.
 */
// Provided by the test runner (Node); the website's own type settings do not include Node's types.
declare const process: { env: Record<string, string | undefined> }
const SEED = Number(process.env.GROOT_SEED) || Math.floor(Math.random() * 1e9)
const ROUNDS = Math.min(Number(process.env.GROOT_ROUNDS) || 300, 400)

// Small seeded random numbers, so a failing run can be replayed.
function rng(seed: number) {
  let a = seed >>> 0
  const next = () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  return {
    next,
    int: (n: number) => Math.floor(next() * n),
    pick: <T,>(xs: T[]) => xs[Math.floor(next() * xs.length)],
    shuffle: <T,>(xs: T[]) => {
      const a2 = [...xs]
      for (let i = a2.length - 1; i > 0; i--) {
        const j = Math.floor(next() * (i + 1))
        ;[a2[i], a2[j]] = [a2[j], a2[i]]
      }
      return a2
    },
  }
}

const person = (id: number, gender: Member['gender'], birth: string | null): Member =>
  ({ id, first_name: `P${id}`, last_name: 'Fz', gender, birth_date: birth }) as unknown as Member
let relId = 0
const rel = (a: number, type: string, b: number): Relationship =>
  ({ id: ++relId, member_1: a, member_2: b, relationship_type_name: type, relationship_type: 1 }) as unknown as Relationship

const ALL_TYPES = [
  'Father', 'Mother', 'Son', 'Daughter', 'Husband', 'Wife', 'Spouse', 'Partner', 'Brother', 'Sister', 'Grandfather',
  'Grandmother', 'Grandson', 'Granddaughter', 'Stepfather', 'Adopted Son', 'Uncle', 'Aunt', 'Cousin', 'Fiance', 'Guardian',
]

function cardsOf(forest: Unit[]) {
  const out: number[] = []
  const walk = (u: Unit) => {
    u.people.forEach((p) => out.push(p.id))
    u.children.forEach(walk)
  }
  forest.forEach(walk)
  return out
}

function draw(members: Member[], rels: Relationship[]) {
  const { graph, ignored } = drawableGraph(rels, members)
  const gens = assignGenerations(graph, members.map((m) => m.id))
  const forest = buildForest(members[0]?.id ?? null, new Map(members.map((m) => [m.id, m])), graph, gens)
  return { graph, ignored, gens, forest, cards: cardsOf(forest) }
}

/** A tidy family: couples, their children, a few generations. Parent links always point downwards. */
function tidyFamily(r: ReturnType<typeof rng>) {
  const members: Member[] = []
  const rels: Relationship[] = []
  let next = 1
  const add = (g: Member['gender'], year: number) => {
    const m = person(next++, g, `${year}-01-01`)
    members.push(m)
    return m
  }
  let couples: [Member, Member][] = [[add('male', 1900), add('female', 1902)]]
  rels.push(rel(couples[0][0].id, 'Husband', couples[0][1].id))
  for (let gen = 1; gen <= 1 + r.int(3); gen++) {
    const nextCouples: [Member, Member][] = []
    for (const [dad, mum] of couples) {
      for (let k = 0; k < r.int(4); k++) {
        const child = add(r.next() < 0.5 ? 'male' : 'female', 1900 + gen * 25 + k)
        rels.push(rel(dad.id, 'Father', child.id), rel(mum.id, 'Mother', child.id))
        if (r.next() < 0.6) {
          const spouse = add(child.gender === 'male' ? 'female' : 'male', 1900 + gen * 25 + k + 1)
          rels.push(child.gender === 'male' ? rel(child.id, 'Husband', spouse.id) : rel(child.id, 'Wife', spouse.id))
          nextCouples.push(child.gender === 'male' ? [child, spouse] : [spouse, child])
        }
      }
    }
    couples = nextCouples
    if (!couples.length) break
  }
  return { members, rels }
}

function garbage(r: ReturnType<typeof rng>) {
  const n = 2 + r.int(11)
  const members = Array.from({ length: n }, (_, i) => person(i + 1, r.pick(['male', 'female', '', 'other'] as Member['gender'][]), r.next() < 0.7 ? `${1900 + r.int(120)}-01-01` : null))
  const rels: Relationship[] = []
  const seen = new Set<string>()
  for (let i = 0; i < r.int(n * 2) + 1; i++) {
    const a = 1 + r.int(n)
    const b = 1 + r.int(n)
    const key = [a, b].sort().join('-')
    if (a === b || seen.has(key)) continue // the server never stores these two
    seen.add(key)
    rels.push(rel(a, r.pick(ALL_TYPES), b))
  }
  return { members, rels }
}

describe(`random families (seed ${SEED})`, () => {
  it('tidy families: every person drawn once, children one row below parents, no false contradictions, order never matters', () => {
    const r = rng(SEED)
    for (let i = 0; i < ROUNDS; i++) {
      const { members, rels } = tidyFamily(r)
      const base = draw(members, rels)
      const ctx = `round ${i}, seed ${SEED}`
      expect(base.ignored, ctx).toEqual([])
      expect([...base.cards].sort((a, b) => a - b), ctx).toEqual(members.map((m) => m.id))
      for (const x of rels) {
        if (x.relationship_type_name === 'Father' || x.relationship_type_name === 'Mother') {
          expect(base.gens.get(x.member_2), ctx).toBe(base.gens.get(x.member_1)! + 1)
        } else {
          expect(base.gens.get(x.member_1), ctx).toBe(base.gens.get(x.member_2)) // couples share a row
        }
      }
      const shuffled = draw(r.shuffle(members), r.shuffle(rels))
      expect([...shuffled.gens].sort(), `${ctx}: shuffled`).toEqual([...base.gens].sort())
      expect([...shuffled.cards].sort((a, b) => a - b), ctx).toEqual(members.map((m) => m.id))
    }
  })

  it('contradictory or nonsense links never crash, never lose or duplicate anyone, and are laid out the same whatever the order', () => {
    const r = rng(SEED + 1)
    for (let i = 0; i < ROUNDS; i++) {
      const { members, rels } = garbage(r)
      const ctx = `round ${i}, seed ${SEED + 1}`
      const base = draw(members, rels)
      expect([...base.cards].sort((a, b) => a - b), ctx).toEqual(members.map((m) => m.id))
      const again = draw(r.shuffle(members), r.shuffle(rels))
      expect(JSON.stringify([...again.gens].sort()), `${ctx}: rows changed when only the order changed`).toBe(JSON.stringify([...base.gens].sort()))
      expect(again.ignored.map((x) => x.id).sort(), ctx).toEqual(base.ignored.map((x) => x.id).sort())
    }
  })

  it('labels: every link reads sensibly from both sides', () => {
    const r = rng(SEED + 2)
    for (let i = 0; i < ROUNDS; i++) {
      const { members, rels } = garbage(r)
      const genders = inferGenders(rels, members)
      for (const x of rels) {
        for (const self of [x.member_1, x.member_2]) {
          const c = classify(x, self, genders)
          expect(c.label.length, `${x.relationship_type_name}`).toBeGreaterThan(0)
          expect(c.label).not.toContain('Husband / wife')
          expect(c.other).toBe(self === x.member_1 ? x.member_2 : x.member_1)
        }
      }
    }
  })
})
