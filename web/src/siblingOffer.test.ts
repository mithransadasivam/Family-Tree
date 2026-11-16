import { describe, expect, it } from 'vitest'
import { siblingParentOffer } from './graph'
import type { Relationship } from './types'

// 1 = Dharsan (has parents), 2 = Deepa (new sister), 10 = father, 11 = mother
const rel = (a: number, type: string, b: number) =>
  ({ id: 0, tree: 1, member_1: a, member_2: b, relationship_type: 0, relationship_type_name: type }) as Relationship
const parents = [rel(10, 'Father', 1), rel(11, 'Mother', 1)]
const none = new Map<number, 'male' | 'female'>()

describe('siblingParentOffer', () => {
  it('offers the existing sibling\'s parents to the new one, on either side', () => {
    const want = { childId: 2, links: [{ parentId: 10, typeName: 'Father' }, { parentId: 11, typeName: 'Mother' }] }
    expect(siblingParentOffer('Sister', 2, 1, parents, none)).toEqual(want)
    expect(siblingParentOffer('Brother', 1, 2, parents, none)).toEqual(want)
  })
  it('reads parents stored as Son/Daughter only when the parent gender is known', () => {
    const rels = [rel(1, 'Son', 10), rel(1, 'Son', 11)]
    expect(siblingParentOffer('Sister', 2, 1, rels, none)).toBeUndefined()
    const g = new Map<number, 'male' | 'female'>([[10, 'male'], [11, 'female']])
    expect(siblingParentOffer('Sister', 2, 1, rels, g)?.links.map((l) => l.typeName)).toEqual(['Father', 'Mother'])
  })
  it('offers nothing when neither or both have parents', () => {
    expect(siblingParentOffer('Sister', 2, 1, [], none)).toBeUndefined()
    expect(siblingParentOffer('Sister', 2, 1, [...parents, rel(12, 'Father', 2)], none)).toBeUndefined()
  })
  it('ignores step, adopted and other types', () => {
    expect(siblingParentOffer('Step Sister', 2, 1, parents, none)).toBeUndefined()
    expect(siblingParentOffer('Cousin', 2, 1, parents, none)).toBeUndefined()
  })
})
