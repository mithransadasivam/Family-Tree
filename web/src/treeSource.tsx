import type { QueryKey } from '@tanstack/react-query'
import { createContext, useContext } from 'react'
import { ENDPOINTS } from './api'

/**
 * Where a family page reads and writes its people and relationships.
 *
 * Every editing component (DetailPanel, MemberForm, undo) goes through the write hooks in
 * queries.ts, and those ask this context which URLs to call and which cached data to refresh. The
 * default is the normal family endpoints, so the family page is untouched. Only the staff page
 * (StaffTreePage) provides the staff source, which is how "staff edit mode" reuses the same panel and
 * forms without a second copy of them - and why nothing outside the staff route can reach /api/staff/.
 *
 * This is a routing convenience, not a security boundary: the server decides who may write.
 */
export interface TreeSource {
  /** True for the superuser's staff edit mode. */
  staff: boolean
  membersCreate: string
  member: (id: number) => string
  relationshipsCreate: string
  relationship: (id: number) => string
  /**
   * Staff only: where a deleted person's stash is listed and restored from. The server keeps the whole
   * row (private phone and account link included) for a while after a staff delete, so a restore from
   * there is exact. Absent on the normal family page, which has no such thing.
   */
  stashes?: string
  stash?: (id: number) => string
  /** Cache entries that hold the people / the relationships (the same one in staff mode). */
  membersKey: (treeId: number) => QueryKey
  relationshipsKey: (treeId: number) => QueryKey
  /** Other cached data a write makes stale (staff mode: the all-trees list shows people counts). */
  alsoStale: QueryKey[]
}

export const NORMAL_SOURCE: TreeSource = {
  staff: false,
  membersCreate: ENDPOINTS.membersCreate,
  member: ENDPOINTS.member,
  relationshipsCreate: ENDPOINTS.relationshipsCreate,
  relationship: ENDPOINTS.relationship,
  membersKey: (treeId) => ['members', treeId],
  relationshipsKey: (treeId) => ['relationships', treeId],
  alsoStale: [],
}

export function staffSource(treeId: number): TreeSource {
  return {
    staff: true,
    membersCreate: ENDPOINTS.staffMembersCreate(treeId),
    member: (id) => ENDPOINTS.staffMember(treeId, id),
    relationshipsCreate: ENDPOINTS.staffRelationshipsCreate(treeId),
    relationship: (id) => ENDPOINTS.staffRelationship(treeId, id),
    stashes: ENDPOINTS.staffRestores(treeId),
    stash: (id) => ENDPOINTS.staffRestore(treeId, id),
    membersKey: (id) => ['staff-tree', id],
    relationshipsKey: (id) => ['staff-tree', id],
    alsoStale: [['staff-trees']],
  }
}

export const TreeSourceContext = createContext<TreeSource>(NORMAL_SOURCE)

export const useTreeSource = () => useContext(TreeSourceContext)
