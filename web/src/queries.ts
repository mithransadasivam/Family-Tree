import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, api, ENDPOINTS, json } from './api'
import { useTreeSource, type TreeSource } from './treeSource'
import type {
  Gender,
  EditHistory,
  JoinRequest,
  JoinResult,
  Member,
  Relationship,
  RelationshipType,
  StaffStash,
  StaffStashRestored,
  StaffTreeDetail,
  StaffTreeList,
  Tree,
  User,
} from './types'

export const useMe = () =>
  useQuery({ queryKey: ['me'], queryFn: () => api<User>(ENDPOINTS.me), staleTime: Infinity })

export interface ProfileInput {
  first_name: string
  last_name: string
  phone: string
  address: string
}

/** Update the signed-in user's own details (email and photo come from Google and cannot be edited). */
export function useUpdateMe() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: ProfileInput) => api<User>(ENDPOINTS.me, json('PATCH', input)),
    onSuccess: (me) => {
      qc.setQueryData(['me'], me)
      return qc.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

/** Upload (a ready-made JPEG blob) or remove the signed-in user's own profile picture. */
export function useAvatar() {
  const qc = useQueryClient()
  const done = (me: User) => {
    qc.setQueryData(['me'], me)
    return qc.invalidateQueries({ queryKey: ['me'] })
  }
  return {
    upload: useMutation({
      mutationFn: (jpeg: Blob) => {
        const body = new FormData()
        body.append('file', jpeg, 'avatar.jpg')
        return api<User>(ENDPOINTS.avatar, { method: 'POST', body })
      },
      onSuccess: done,
    }),
    remove: useMutation({
      mutationFn: () => api<User>(ENDPOINTS.avatar, { method: 'DELETE' }),
      onSuccess: done,
    }),
  }
}

export const useJoinRequests =(treeId: number, enabled: boolean) =>
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

/** Superuser-only: every tree in the system (the server refuses anyone else with 403). */
export const useStaffTrees = (q: string, offset: number, limit: number) =>
  useQuery({
    queryKey: ['staff-trees', q, offset, limit],
    queryFn: () => api<StaffTreeList>(ENDPOINTS.staffTrees(q, offset, limit)),
    placeholderData: keepPreviousData,
  })

/** Superuser-only: one tree's people and relationships, read-only. */
export const useStaffTree = (treeId: number) =>
  useQuery({
    queryKey: ['staff-tree', treeId],
    queryFn: () => api<StaffTreeDetail>(ENDPOINTS.staffTree(treeId)),
  })

/** Superuser-only: people staff deleted from this tree who can still be restored (names and dates only). */
export const useStaffStashes = (treeId: number, enabled: boolean) =>
  useQuery({
    queryKey: ['staff-stashes', treeId],
    queryFn: () => api<StaffStash[]>(ENDPOINTS.staffRestores(treeId)),
    enabled,
  })

/** Superuser-only: put one staff-deleted person back from the server's stash (private data included). */
export function useRestoreStash(treeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (stashId: number) =>
      api<StaffStashRestored>(ENDPOINTS.staffRestore(treeId, stashId), json('POST', {})),
    onSettled: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['staff-tree', treeId] }),
        qc.invalidateQueries({ queryKey: ['staff-stashes', treeId] }),
        qc.invalidateQueries({ queryKey: ['staff-trees'] }),
      ]),
  })
}

/** Mark a write's other dependents stale (staff mode only; empty for the normal family page). */
const alsoStale = (qc: ReturnType<typeof useQueryClient>, src: TreeSource) =>
  src.alsoStale.map((queryKey) => qc.invalidateQueries({ queryKey }))

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

/** What the edit form can change. Death details are intentionally not editable here. */
export interface MemberInput {
  first_name: string
  last_name: string
  gender: Gender
  birth_date: string
  birth_place: string
  photo_url: string
  phone: string
  phone_public: boolean
}

// Blank dates must be null for DRF's DateField; blank text fields are fine as ''.
const toPayload = (i: MemberInput) => ({ ...i, birth_date: i.birth_date || null })
// Staff never see a private number, so staff edit mode never sends one (the server ignores it too).
const withoutPhone = ({ phone: _p, phone_public: _v, ...rest }: ReturnType<typeof toPayload>) => rest

export function useSaveMember(treeId: number) {
  const qc = useQueryClient()
  const src = useTreeSource()
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: MemberInput }) =>
      api<Member>(src.member(id), json('PATCH', src.staff ? withoutPhone(toPayload(input)) : toPayload(input))),
    onSuccess: () =>
      Promise.all([qc.invalidateQueries({ queryKey: src.membersKey(treeId) }), ...alsoStale(qc, src)]),
  })
}

export interface NewPerson {
  first_name: string
  last_name: string
  gender: Gender
  /** Who they are connected to and how: "[new person] is the <type> of <otherId>". Omit only for the first person. */
  relationship?: { otherId: number; typeId: number }
}

/**
 * Create a person together with their first relationship. If the relationship cannot be
 * created the person is removed again, so nobody ends up floating unconnected in the tree.
 */
export function useCreatePerson(treeId: number) {
  const qc = useQueryClient()
  const src = useTreeSource()
  return useMutation({
    mutationFn: async (p: NewPerson) => {
      const person = await api<Member>(
        src.membersCreate,
        json('POST', { tree: treeId, first_name: p.first_name, last_name: p.last_name, gender: p.gender }),
      )
      if (p.relationship) {
        try {
          await api<Relationship>(
            src.relationshipsCreate,
            json('POST', {
              tree: treeId,
              member_1: person.id,
              member_2: p.relationship.otherId,
              relationship_type: p.relationship.typeId,
            }),
          )
        } catch (e) {
          await api<unknown>(src.member(person.id), { method: 'DELETE' }).catch(() => undefined)
          throw e
        }
      }
      return person
    },
    onSettled: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: src.membersKey(treeId) }),
        qc.invalidateQueries({ queryKey: src.relationshipsKey(treeId) }),
        qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
        ...alsoStale(qc, src),
      ]),
  })
}

export function useDeleteMember(treeId: number) {
  const qc = useQueryClient()
  const src = useTreeSource()
  return useMutation({
    // A staff delete answers with restore_id: the server kept the whole row so Undo can be exact.
    mutationFn: (id: number) => api<{ restore_id?: number } | undefined>(src.member(id), { method: 'DELETE' }),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: src.membersKey(treeId) }),
        qc.invalidateQueries({ queryKey: src.relationshipsKey(treeId) }),
        ...alsoStale(qc, src),
      ]),
  })
}

export function useAddRelationship(treeId: number) {
  const qc = useQueryClient()
  const src = useTreeSource()
  return useMutation({
    mutationFn: (r: { member_1: number; member_2: number; relationship_type: number }) =>
      api<Relationship>(src.relationshipsCreate, json('POST', { tree: treeId, ...r })),
    onSuccess: () =>
      Promise.all([qc.invalidateQueries({ queryKey: src.relationshipsKey(treeId) }), ...alsoStale(qc, src)]),
  })
}

export function useUpdateRelationship(treeId: number) {
  const qc = useQueryClient()
  const src = useTreeSource()
  return useMutation({
    mutationFn: (v: { id: number; member_1: number; member_2: number; relationship_type: number }) =>
      api<Relationship>(
        src.relationship(v.id),
        json('PATCH', {
          member_1: v.member_1,
          member_2: v.member_2,
          relationship_type: v.relationship_type,
        }),
      ),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: src.relationshipsKey(treeId) }),
        qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
        ...alsoStale(qc, src),
      ]),
  })
}

export function useDeleteRelationship(treeId: number) {
  const qc = useQueryClient()
  const src = useTreeSource()
  return useMutation({
    mutationFn: (id: number) => api<unknown>(src.relationship(id), { method: 'DELETE' }),
    onSuccess: () =>
      Promise.all([qc.invalidateQueries({ queryKey: src.relationshipsKey(treeId) }), ...alsoStale(qc, src)]),
  })
}

export interface MemberSnapshot {
  member: Member
  relationships: Relationship[]
  /** Staff deletes only: the server-side stash that can restore this person exactly. */
  restoreId?: number
}

/**
 * Undo support. The backend deletes permanently, so a restore re-creates the person (they get
 * a new id) and re-links each relationship they had to that new id.
 */
export function useRestore(treeId: number) {
  const qc = useQueryClient()
  const src = useTreeSource()
  const refresh = () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: src.membersKey(treeId) }),
      qc.invalidateQueries({ queryKey: src.relationshipsKey(treeId) }),
      qc.invalidateQueries({ queryKey: ['edit-history', treeId] }),
      ...alsoStale(qc, src),
    ])

  const relationship = async (r: Pick<Relationship, 'member_1' | 'member_2' | 'relationship_type'>) => {
    try {
      await api<Relationship>(
        src.relationshipsCreate,
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

  // Staff mode: ask the server to put the person back from its own stash. Unlike the payload path
  // below (which can only resend what staff were shown), this restores the private phone number and
  // the account link too, and keeps the same id. Returns undefined when there is no usable stash
  // (none was recorded, it expired, or it was already used), so the caller falls back to the payload.
  const fromStash = async (m: Member, restoreId: number | undefined): Promise<Member | undefined> => {
    if (restoreId === undefined || !src.stash) return undefined
    let result: StaffStashRestored
    try {
      result = await api<StaffStashRestored>(src.stash(restoreId), json('POST', {}))
    } catch (e) {
      if (e instanceof ApiError && (e.status === 404 || e.status === 410)) return undefined
      throw e
    }
    await refresh()
    const skipped = result.skipped_relationships
    if (skipped.length > 0) {
      throw new Error(
        `${m.first_name} was restored, but ${skipped.length} of ${skipped.length + result.restored_relationships} ` +
          `relationships could not be: ${skipped.map((s) => `${s.link} (${s.reason})`).join('; ')}.`,
      )
    }
    return result.member
  }

  const member = async ({ member: m, relationships, restoreId }: MemberSnapshot): Promise<Member> => {
    const exact = await fromStash(m, restoreId)
    if (exact) return exact
    const created = await api<Member>(
      src.membersCreate,
      json('POST', {
        tree: treeId,
        ...(m.user !== null && m.user !== undefined ? { user: m.user } : {}),
        first_name: m.first_name,
        last_name: m.last_name,
        gender: m.gender ?? '',
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
          src.relationshipsCreate,
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
