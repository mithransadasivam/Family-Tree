// Fixtures shared by the component tests.
import type { Member, Relationship, RelationshipType, Tree, User } from './types'

export const OWNER: User = { id: 1, email: 'owner@example.com', first_name: 'Olive', last_name: 'Owner' }
export const GUEST: User = { id: 2, email: 'guest@example.com', first_name: 'Gus', last_name: 'Guest' }

export const TREE: Tree = {
  id: 1,
  tree_name: 'The Tests',
  description: '',
  owner: OWNER,
  member_count: 2,
  approval_required: true,
}

const person = (id: number, first_name: string): Member => ({
  id,
  tree: 1,
  first_name,
  last_name: 'Test',
  gender: '',
  phone: '',
  phone_public: false,
  email: '',
  address: '',
  user: null,
  photo_url: '',
  birth_date: null,
  birth_place: '',
  death_date: null,
  death_place: '',
})

export const ANN = person(1, 'Ann')
export const BEN = person(2, 'Ben')
export const MEMBERS: Member[] = [ANN, BEN]

export const TYPES: RelationshipType[] = [
  { id: 1, type_name: 'Brother', category: 'biological', description: '' },
  { id: 2, type_name: 'Sister', category: 'biological', description: '' },
  { id: 3, type_name: 'Father', category: 'biological', description: '' },
  { id: 4, type_name: 'Son', category: 'biological', description: '' },
]

/** Ann is the Brother of Ben (no parent/child, so neither person is a "root" that can't be deleted). */
export const SIBLINGS: Relationship[] = [
  { id: 10, tree: 1, member_1: 1, member_2: 2, relationship_type: 1, relationship_type_name: 'Brother' },
]

/** Ann is the Father of Ben, so Ann has descendants. */
export const PARENT_CHILD: Relationship[] = [
  { id: 11, tree: 1, member_1: 1, member_2: 2, relationship_type: 3, relationship_type_name: 'Father' },
]
