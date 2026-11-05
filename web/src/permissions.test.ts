import { describe, expect, it } from 'vitest'
import { isTreeOwner } from './permissions'

const tree = { owner: { id: 7 } }

describe('isTreeOwner', () => {
  it('is true only for the tree owner', () => {
    expect(isTreeOwner(tree, { id: 7 })).toBe(true)
    expect(isTreeOwner(tree, { id: 8 })).toBe(false)
  })

  it('is false while the tree or the signed-in user is still loading', () => {
    // Unknown must mean "hide the delete actions", never "show them".
    expect(isTreeOwner(undefined, { id: 7 })).toBe(false)
    expect(isTreeOwner(tree, undefined)).toBe(false)
    expect(isTreeOwner(undefined, undefined)).toBe(false)
  })
})
