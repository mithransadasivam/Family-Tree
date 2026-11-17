import { describe, expect, it } from 'vitest'
import { assignGenerations, drawableGraph } from './generations'
import { buildForest, classify, inferGenders, type Unit } from './graph'
import type { Member, Relationship } from './types'

const mem = (id: number, first: string, gender: Member['gender'] = '', birth: string | null = null) =>
  ({ id, first_name: first, last_name: 'Arun', gender, birth_date: birth }) as unknown as Member
let rid = 0
// "a is the <type> of b"
const rel = (a: number, type: string, b: number) =>
  ({ id: ++rid, member_1: a, member_2: b, relationship_type_name: type, relationship_type: 1 }) as unknown as Relationship

function rows(members: Member[], rels: Relationship[]) {
  const { graph, ignored } = drawableGraph(rels, members)
  const gens = assignGenerations(graph, members.map((m) => m.id))
  const forest = buildForest(members[0].id, new Map(members.map((m) => [m.id, m])), graph, gens)
  const cards: number[] = []
  const walk = (u: Unit) => {
    u.people.forEach((p) => cards.push(p.id))
    u.children.forEach(walk)
  }
  forest.forEach(walk)
  return { gens, forest, cards, ignored }
}

describe('audit scenarios', () => {
  // Arun Family tree: grandparents entered first, then the parents, then the child.
  const members = [mem(1, 'Gran', 'female'), mem(2, 'Gramps', 'male'), mem(3, 'Dad', 'male'), mem(4, 'Mum', 'female'), mem(5, 'Kid')]
  const links = [
    rel(1, 'Grandmother', 5), // grandparents entered before the parents exist
    rel(2, 'Grandfather', 5),
    rel(1, 'Mother', 3),
    rel(2, 'Father', 3),
    rel(1, 'Wife', 2),
    rel(3, 'Father', 5),
    rel(4, 'Mother', 5),
    rel(3, 'Husband', 4),
  ]

  it('grandparents first, then parents: one connected tree, correct rows, no card twice', () => {
    for (const order of [links, [...links].reverse()]) {
      const { gens, cards, ignored } = rows(members, order)
      expect(ignored).toEqual([])
      expect([gens.get(1), gens.get(2), gens.get(3), gens.get(4), gens.get(5)]).toEqual([0, 0, 1, 1, 2])
      expect([...cards].sort()).toEqual([1, 2, 3, 4, 5])
    }
  })

  it('a person with three spouses is drawn once, beside all of them', () => {
    const ms = [mem(1, 'Raj', 'male'), mem(2, 'A', 'female'), mem(3, 'B', 'female'), mem(4, 'C', 'female'), mem(5, 'Kid1'), mem(6, 'Kid2')]
    const rs = [rel(2, 'Wife', 1), rel(3, 'Wife', 1), rel(4, 'Wife', 1), rel(1, 'Father', 5), rel(3, 'Mother', 6)]
    const { forest, cards, gens } = rows(ms, rs)
    expect([...cards].sort()).toEqual([1, 2, 3, 4, 5, 6])
    expect(forest[0].people.length).toBe(4)
    expect(gens.get(5)).toBe(1)
  })

  it('a link stored backwards is set aside with a notice instead of garbling the tree', () => {
    const ms = [mem(1, 'Vijay', 'male'), mem(2, 'Sangeetha', 'female'), mem(3, 'Kid')]
    // Husband link plus a (wrong way round) "Father" link making the husband the child of his wife.
    const rs = [rel(1, 'Husband', 2), rel(2, 'Father', 1), rel(1, 'Father', 3), rel(2, 'Mother', 3)]
    const { ignored } = rows(ms, rs)
    expect(ignored.length).toBe(1)
    expect(ignored[0].reads).toContain('Sangeetha Arun is the Father of Vijay Arun')
  })

  it('sibling link alone leaves the sibling unconnected (derived, not drawn)', () => {
    const ms = [mem(1, 'Dharsan', 'male'), mem(2, 'Deepa', 'female'), mem(3, 'Mum', 'female'), mem(4, 'Dad', 'male')]
    const rs = [rel(3, 'Mother', 1), rel(4, 'Father', 1), rel(2, 'Sister', 1)]
    const { forest } = rows(ms, rs)
    // Deepa has no parent link: she is a separate root, not hanging under Mum and Dad.
    const roots = forest.map((u) => u.people.map((p) => p.id))
    expect(roots.flat()).toContain(2)
    expect(forest.find((u) => u.people.some((p) => p.id === 3))!.children.some((c) => c.people.some((p) => p.id === 2))).toBe(false)
  })

  it('labels: a spouse with unknown gender is "Spouse", not "Husband / wife"', () => {
    const ms = [mem(1, 'Vijay'), mem(2, 'Sangeetha')]
    const r = rel(1, 'Husband', 2)
    const genders = inferGenders([r], ms)
    expect(classify(r, 1, genders).label).toBe('Spouse')
    expect(classify(r, 2, genders).label).toBe('Husband')
  })
})
