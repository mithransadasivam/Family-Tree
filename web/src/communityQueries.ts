import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ENDPOINTS, json } from './api'
import type {
  ApprovalRequest,
  Community,
  CommunityDetail,
  CommunityFound,
  CommunityMemberRow,
  CommunityPerson,
  CommunityRequest,
} from './types'

export const useCommunities = () =>
  useQuery({ queryKey: ['communities'], queryFn: () => api<Community[]>(ENDPOINTS.communities) })

export function useCreateCommunity() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: { name: string; description: string }) =>
      api<Community>(ENDPOINTS.communities, json('POST', input)),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['communities'] }),
  })
}

/** Look communities up by name (2+ letters); nothing is listed until you search. */
export const useFindCommunities = (q: string) =>
  useQuery({
    queryKey: ['communities-find', q],
    queryFn: () => api<CommunityFound[]>(ENDPOINTS.communityFind(q)),
    enabled: q.length >= 2,
  })

export function useJoinCommunity() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: number; treeId?: number }) =>
      api<{ message: string }>(ENDPOINTS.communityJoin(v.id), json('POST', v.treeId ? { tree_id: v.treeId } : {})),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['communities-find'] }),
  })
}

export const useCommunity = (id: number) =>
  useQuery({ queryKey: ['community', id], queryFn: () => api<CommunityDetail>(ENDPOINTS.community(id)) })

export const useCommunityPeople = (id: number, query: string) =>
  useQuery({
    queryKey: ['community-people', id, query],
    queryFn: () => api<{ count: number; results: CommunityPerson[] }>(ENDPOINTS.communityPeople(id, query)),
    placeholderData: keepPreviousData,
  })

export function useShareTree(communityId: number) {
  const qc = useQueryClient()
  const refresh = () =>
    Promise.all([
      qc.invalidateQueries({ queryKey: ['community', communityId] }),
      qc.invalidateQueries({ queryKey: ['community-people', communityId] }),
      qc.invalidateQueries({ queryKey: ['communities'] }),
    ])
  return {
    share: useMutation({
      mutationFn: (treeId: number) => api(ENDPOINTS.communityTrees(communityId), json('POST', { tree_id: treeId })),
      onSuccess: refresh,
    }),
    unshare: useMutation({
      mutationFn: (treeId: number) => api(ENDPOINTS.communityTree(communityId, treeId), { method: 'DELETE' }),
      onSuccess: refresh,
    }),
  }
}

export const useCommunityRequests = (id: number, enabled: boolean) =>
  useQuery({
    queryKey: ['community-requests', id],
    queryFn: () => api<CommunityRequest[]>(ENDPOINTS.communityRequests(id)),
    enabled,
  })

export function useHandleCommunityRequest(communityId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (v: { id: number; status: 'approved' | 'rejected' }) =>
      api(ENDPOINTS.communityRequest(v.id), json('PATCH', { status: v.status })),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['community-requests', communityId] }),
        qc.invalidateQueries({ queryKey: ['community-members', communityId] }),
        qc.invalidateQueries({ queryKey: ['community', communityId] }),
        qc.invalidateQueries({ queryKey: ['communities'] }),
      ]),
  })
}

export const useCommunityMembers = (id: number, enabled: boolean) =>
  useQuery({
    queryKey: ['community-members', id],
    queryFn: () => api<CommunityMemberRow[]>(ENDPOINTS.communityMembers(id)),
    enabled,
  })

export function useCommunityActions(communityId: number) {
  const qc = useQueryClient()
  const all = () => qc.invalidateQueries({ queryKey: ['communities'] })
  return {
    removeMember: useMutation({
      mutationFn: (userId: number) => api(ENDPOINTS.communityMember(communityId, userId), { method: 'DELETE' }),
      onSuccess: () =>
        Promise.all([
          qc.invalidateQueries({ queryKey: ['community-members', communityId] }),
          qc.invalidateQueries({ queryKey: ['community-people', communityId] }),
          qc.invalidateQueries({ queryKey: ['community', communityId] }),
          all(),
        ]),
    }),
    leave: useMutation({
      mutationFn: () => api(ENDPOINTS.communityLeave(communityId), json('POST', {})),
      onSuccess: all,
    }),
    remove: useMutation({
      mutationFn: () => api(ENDPOINTS.community(communityId), { method: 'DELETE' }),
      onSuccess: all,
    }),
  }
}

const approvalPath = (kind: string, id: number) =>
  kind === 'tree' ? ENDPOINTS.joinRequest(id) : ENDPOINTS.communityRequest(id)

export const useApprovalRequest = (kind: string, id: number) =>
  useQuery({
    queryKey: ['approval', kind, id],
    queryFn: () => api<ApprovalRequest>(approvalPath(kind, id)),
  })

export function useDecideApproval(kind: string, id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (status: 'approved' | 'rejected') => api(approvalPath(kind, id), json('PATCH', { status })),
    onSuccess: () =>
      Promise.all([
        qc.invalidateQueries({ queryKey: ['approval', kind, id] }),
        qc.invalidateQueries({ queryKey: ['community-requests'] }),
        qc.invalidateQueries({ queryKey: ['community-members'] }),
        qc.invalidateQueries({ queryKey: ['join-requests'] }),
        qc.invalidateQueries({ queryKey: ['communities'] }),
      ]),
  })
}
