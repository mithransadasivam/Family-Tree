// Fixtures shared by the component tests.
import type { Member, Relationship, RelationshipType, StaffTree, StaffTreeDetail, Tree, User } from './types'

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

// --- staff (superuser) pages ---------------------------------------------------------------
export const SUPERUSER: User = {
  id: 9, email: 'root@example.com', first_name: 'Rhea', last_name: 'Root', is_staff: true, is_superuser: true,
}

const staffTree = (over: Partial<StaffTree>): StaffTree => ({
  id: 1, tree_name: 'The Tests', description: '', owner: OWNER, is_active: true, approval_required: true,
  account_count: 2, people_count: 2, created_at: '2026-01-02T03:04:05Z', updated_at: '2026-01-02T03:04:05Z', ...over,
})

export const STAFF_TREES: StaffTree[] = [
  staffTree({ id: 1, tree_name: 'Smith Family' }),
  staffTree({
    id: 2, tree_name: 'Jones Family', owner: GUEST, account_count: 1, people_count: 0, is_active: false,
    created_at: '2026-02-03T00:00:00Z',
  }),
]

export const STAFF_DETAIL: StaffTreeDetail = {
  tree: STAFF_TREES[0],
  members: MEMBERS,
  relationships: SIBLINGS,
}
