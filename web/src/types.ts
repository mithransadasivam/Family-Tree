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
  /** Only sent for your own account (/users/me/). The server enforces access; this just shows the staff link. */
  is_staff?: boolean
  is_superuser?: boolean
}

/** A tree as the superuser-only /api/staff/trees/ endpoints show it. */
export interface StaffTree {
  id: number
  tree_name: string
  description: string
  owner: User
  /** Deleted trees are hidden from everyone else but still listed here, flagged. */
  is_active: boolean
  approval_required: boolean
  /** Accounts that belong to the tree. */
  account_count: number
  /** People drawn in the tree. */
  people_count: number
  created_at: string
  updated_at: string
}

export interface StaffTreeList {
  count: number
  results: StaffTree[]
}

export interface StaffTreeDetail {
  tree: StaffTree
  members: Member[]
  relationships: Relationship[]
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
  /** Public numbers are visible to the family and shared communities; private ones only to the family owner and the person. */
  phone_public: boolean
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

export interface Community {
  id: number
  name: string
  description: string
  role: 'owner' | 'member'
  member_count: number
  tree_count: number
}

export interface CommunityDetail extends Community {
  /** The family trees you own, and whether each is shared with this community. */
  my_trees: { id: number; tree_name: string; shared: boolean }[]
  pending_requests?: number
}

export interface CommunityFound {
  id: number
  name: string
  description: string
  member_count: number
  status: 'member' | 'pending' | null
}

/** The basic card a community shows for a person. No photo, address or email. */
export interface CommunityPerson {
  id: number
  first_name: string
  last_name: string
  gender: Gender
  age: number | null
  deceased: boolean
  phone: string
}

export interface CommunityRequest {
  id: number
  name: string
  email: string
  message: string
  created_at: string
}

export interface CommunityMemberRow {
  user_id: number
  name: string
  email: string
  role: 'owner' | 'member'
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

/** A pending request to join a community or a family, as the owner sees it when opening the emailed link. */
export interface ApprovalRequest {
  id: number
  kind: 'community' | 'tree'
  target_id: number
  target_name: string
  requester_name: string
  requester_email: string
  message: string
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
}
