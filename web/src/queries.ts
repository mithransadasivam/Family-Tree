import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ENDPOINTS, json } from './api'
import type {
  EditHistory,
  JoinRequest,
  JoinResult,
  Member,
  Relationship,
  RelationshipType,
  Tree,
  User,
} from './types'

export const useMe = () =>
  useQuery({ queryKey: ['me'], queryFn: () => api<User>(ENDPOINTS.me), staleTime: Infinity })

export const useJoinRequests = (treeId: number, enabled: boolean) =>
  useQuery({
    queryKey: ['join-requests', treeId],
    queryFn: () => api<JoinRequest[]>(ENDPOINTS.joinRequests(treeId)),
    enabled, // the backend only lets the owner list these
  })

export const useMyJoinRequests = () =>
  useQuery({
    queryKey: ['my-join-requests'],
    queryFn: () => api<JoinRequest[]>(ENDPOINTS.myJoinRequests),
  })

export const useEditHistory = (treeId: number) =>
  useQuery({
    queryKey: ['edit-history', treeId],
    queryFn: () => api<EditHistory[]>(ENDPOINTS.editHistory(treeId)),
  })

export function useSubmitJoinRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { code: string; message: string }) =>
      api<JoinResult>(ENDPOINTS.joinRequestsCreate, json('POST', v)),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['trees'] }),
        qc.invalidateQueries({ queryKey: ['my-join-requests'] }),
      ]),
  })
}

export function useDecideJoinRequest(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: number; status: 'approved' | 'rejected' }) =>
      api<JoinRequest>(ENDPOINTS.joinRequest(v.id), json('PATCH', { status: v.status })),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['join-requests', treeId] }),
        qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
      ]),
  })
}

export function useGenerateCode(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () =>
      api<{ code: string; tree: string }>(ENDPOINTS.generateCode, json('POST', { tree_id: treeId })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
  })
}

export function useUpdateTreeSettings(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (approval_required: boolean) =>
      api<Tree>(ENDPOINTS.tree(treeId), json('PATCH', { approval_required })),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['trees'] }),
        qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
      ]),
  })
}

/** Owner deletes the tree; anyone else leaves it. Both drop it from the user's tree list. */
export function useRemoveTree(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (mode: 'delete' | 'leave') =>
      mode === 'delete'
        ? api<unknown>(ENDPOINTS.tree(treeId), { method: 'DELETE' })
        : api<unknown>(ENDPOINTS.leaveTree(treeId), json('POST', {})),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['trees'] }),
  })
}

export const useTrees = () =>
  useQuery({ queryKey: ['trees'], queryFn: () => api<Tree[]>(ENDPOINTS.trees) })

export const useMembers = (treeId: number) =>
  useQuery({
    queryKey: ['members', treeId],
    queryFn: () => api<Member[]>(ENDPOINTS.members(treeId)),
  })

export const useRelationships = (treeId: number) =>
  useQuery({
    queryKey: ['relationships', treeId],
    queryFn: () => api<Relationship[]>(ENDPOINTS.relationships(treeId)),
  })

export const useRelationshipTypes = () =>
  useQuery({
    queryKey: ['relationship-types'],
    queryFn: () => api<RelationshipType[]>(ENDPOINTS.relationshipTypes),
    staleTime: Infinity,
  })

export function useCreateTree() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (tree_name: string) =>
      api<Tree>(ENDPOINTS.trees, json('POST', { tree_name, description: '' })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['trees'] }),
  })
}

export interface MemberInput {
  first_name: string
  last_name: string
  birth_date: string
  birth_place: string
  death_date: string
  death_place: string
  photo_url: string
}

// Blank dates must be null for DRF's DateField; blank text fields are fine as ''.
const toPayload = (i: MemberInput) => ({
  ...i,
  birth_date: i.birth_date || null,
  death_date: i.death_date || null,
})

export function useSaveMember(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, input }: { id?: number; input: MemberInput }) =>
      id === undefined
        ? api<Member>(ENDPOINTS.membersCreate, json('POST', { tree: treeId, ...toPayload(input) }))
        : api<Member>(ENDPOINTS.member(id), json('PATCH', toPayload(input))),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['members', treeId] }),
  })
}

export function useDeleteMember(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<unknown>(ENDPOINTS.member(id), { method: 'DELETE' }),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['members', treeId] }),
        qc.invalidateQueries({ queryKey: ['relationships', treeId] }),
      ]),
  })
}

export function useAddRelationship(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (r: { member_1: number; member_2: number; relationship_type: number }) =>
      api<Relationship>(ENDPOINTS.relationshipsCreate, json('POST', { tree: treeId, ...r })),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['relationships', treeId] }),
  })
}

export function useUpdateRelationship(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: number; member_1: number; member_2: number; relationship_type: number }) =>
      api<Relationship>(
        ENDPOINTS.relationship(v.id),
        json('PATCH', {
          member_1: v.member_1,
          member_2: v.member_2,
          relationship_type: v.relationship_type,
        }),
      ),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['relationships', treeId] }),
        qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
      ]),
  })
}

export function useDeleteRelationship(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<unknown>(ENDPOINTS.relationship(id), { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['relationships', treeId] }),
  })
}

export interface MemberSnapshot {
  member: Member
  relationships: Relationship[]
}

/**
 * Undo support. The backend deletes permanently, so a restore re-creates the person (they get
 * a new id) and re-links each relationship they had to that new id.
 */
export function useRestore(treeId: number) {
  const qc = useQueryClient()
  const refresh = () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: ['members', treeId] }),
      qc.invalidateQueries({ queryKey: ['relationships', treeId] }),
      qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
    ])

  const relationship = async (r: Pick<Relationship, 'member_1' | 'member_2' | 'relationship_type'>) => {
    try {
      await api<Relationship>(
        ENDPOINTS.relationshipsCreate,
        json('POST', {
          tree: treeId,
          member_1: r.member_1,
          member_2: r.member_2,
          relationship_type: r.relationship_type,
        }),
      )
    } finally {
      await refresh()
    }
  }

  const member = async ({ member: m, relationships }: MemberSnapshot): Promise<Member> => {
    const created = await api<Member>(
      ENDPOINTS.membersCreate,
      json('POST', {
        tree: treeId,
        ...(m.user !== null && m.user !== undefined ? { user: m.user } : {}),
        first_name: m.first_name,
        last_name: m.last_name,
        phone: m.phone,
        email: m.email,
        address: m.address,
        photo_url: m.photo_url,
        birth_date: m.birth_date,
        birth_place: m.birth_place,
        death_date: m.death_date,
        death_place: m.death_place,
      }),
    )
    const swap = (id: number) => (id === m.id ? created.id : id)
    const results = await Promise.allSettled(
      relationships.map((r) =>
        api<Relationship>(
          ENDPOINTS.relationshipsCreate,
          json('POST', {
            tree: treeId,
            member_1: swap(r.member_1),
            member_2: swap(r.member_2),
            relationship_type: r.relationship_type,
          }),
        ),
      ),
    )
    await refresh()
    const failed = results.filter((x) => x.status === 'rejected').length
    if (failed > 0) {
      throw new Error(
        `${m.first_name} was restored, but ${failed} of ${relationships.length} relationships could not be.`,
      )
    }
    return created
  }

  return { member, relationship }
}
