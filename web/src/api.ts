export const ENDPOINTS = {
  googleAuth: '/api/auth/google/',
  refresh: '/api/auth/refresh/',
  logout: '/api/auth/logout/',
  me: '/api/users/me/',
  trees: '/api/family-trees/',
  tree: (id: number) => `/api/family-trees/${id}/`,
  leaveTree: (id: number) => `/api/family-trees/${id}/leave/`,
  generateCode: '/api/family-codes/generate/',
  joinRequests: (treeId: number) => `/api/join-requests/?tree_id=${treeId}`,
  joinRequestsCreate: '/api/join-requests/',
  joinRequest: (id: number) => `/api/join-requests/${id}/`,
  myJoinRequests: '/api/join-requests/mine/',
  editHistory: (treeId: number) => `/api/edit-history/?tree_id=${treeId}`,
  members: (treeId: number) => `/api/family-members/?tree_id=${treeId}`,
  membersCreate: '/api/family-members/',
  member: (id: number) => `/api/family-members/${id}/`,
  relationships: (treeId: number) => `/api/relationships/?tree_id=${treeId}`,
  relationshipsCreate: '/api/relationships/',
  relationship: (id: number) => `/api/relationships/${id}/`,
  relationshipTypes: '/api/relationship-types/',
} as const

// Empty string = same origin (e.g. behind a Vercel /api proxy).
const BASE = import.meta.env.VITE_API_URL ?? ''

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// Auth lives in httpOnly cookies set by Django; page JavaScript never sees the tokens.
// VITE_DEV_TOKEN is an optional dev-only Bearer token.
const devToken: string | undefined = import.meta.env.VITE_DEV_TOKEN || undefined

async function send(path: string, init: RequestInit): Promise<Response> {
  return fetch(BASE + path, {
    ...init,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(devToken ? { Authorization: `Bearer ${devToken}` } : {}),
      ...init.headers,
    },
  })
}

let refreshing: Promise<boolean> | null = null
function refreshSession(): Promise<boolean> {
  refreshing ??= send(ENDPOINTS.refresh, { method: 'POST', body: '{}' })
    .then((res) => res.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

/** Django returns `{error: "..."}`, `{detail: "..."}` or DRF field errors `{field: ["..."]}`. */
function errorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object') {
    const b = body as Record<string, unknown>
    if (typeof b.error === 'string') return b.error
    if (typeof b.detail === 'string') return b.detail
    const first = Object.entries(b)[0]
    if (first) return `${first[0]}: ${[first[1]].flat().join(' ')}`
  }
  return fallback
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res = await send(path, init)
  if (res.status === 401 && path !== ENDPOINTS.googleAuth && (await refreshSession())) {
    res = await send(path, init)
  }
  if (!res.ok) {
    const body = await res.json().catch(() => undefined)
    throw new ApiError(res.status, errorMessage(body, `${res.status} ${res.statusText}`))
  }
  return res.status === 204 ? (undefined as T) : res.json()
}

export const json = (method: string, body: unknown): RequestInit => ({
  method,
  body: JSON.stringify(body),
})
