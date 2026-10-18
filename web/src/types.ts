// Mirrors the Django serializers in Family-Tree (family_trees, family_members, relationships).
export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  phone?: string
  address?: string
  photo_url?: string
  /** True when the user uploaded their own picture (it then wins over the Google photo). */
  has_avatar?: boolean
  /** Changes with every upload; used to bust the browser cache. */
  avatar_version?: string | null
  created_at?: string
}

export interface Tree {
  id: number
  tree_name: string
  description: string
  owner: User
  /** Number of accounts in the tree, not of family members. */
  member_count: number
  approval_required: boolean
}

export interface JoinRequest {
  id: number
  tree: number
  tree_name: string
  requester_name: string
  requester_email: string
  status: 'pending' | 'approved' | 'rejected'
  message: string
  created_at: string
}

export interface JoinResult {
  auto_approved: boolean
  message: string
  request: JoinRequest
}

export interface EditHistory {
  id: number
  entity_type: string
  entity_id: number
  change_description: string
  edited_by: User | null
  edited_at: string
}

export type Gender = '' | 'male' | 'female' | 'other'

export interface Member {
  id: number
  tree: number
  first_name: string
  last_name: string
  /** '' = not recorded. */
  gender: Gender
  phone: string
  email: string
  address: string
  /** Id of the user account this person is linked to, if any. */
  user: number | null
  photo_url: string
  birth_date: string | null
  birth_place: string
  death_date: string | null
  death_place: string
}

export interface RelationshipType {
  id: number
  type_name: string
  category: string
  description: string
}

/** `relationship_type_name` says what member_1 IS to member_2 (e.g. "Father": member_1 is member_2's father). */
export interface Relationship {
  id: number
  tree: number
  member_1: number
  member_2: number
  relationship_type: number
  relationship_type_name: string
}

export const fullName = (m: Pick<Member, 'first_name' | 'last_name'>) =>
  `${m.first_name} ${m.last_name}`.trim()
