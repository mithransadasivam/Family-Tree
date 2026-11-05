import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AppRoutes } from './App'
import { GUEST, MEMBERS, STAFF_DETAIL, STAFF_TREES, SUPERUSER, SIBLINGS, TYPES } from './testData'
import type { User } from './types'

// The canvas is irrelevant here: a stand-in that lets the test select Ben.
vi.mock('./TreeView', async () => {
  const { createElement } = await import('react')
  return {
    default: ({ onSelect }: { onSelect: (id: number) => void }) =>
      createElement('button', { onClick: () => onSelect(2) }, 'pick Ben'),
  }
})

let calls: { method: string; path: string }[] = []

function fakeBackend(me: User) {
  calls = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      const u = new URL(url, 'http://localhost') // VITE_API_URL may prefix a host
      const method = init?.method ?? 'GET'
      calls.push({ method, path: u.pathname + u.search })
      let body: unknown = {}
      if (method === 'GET') {
        if (u.pathname === '/api/users/me/') body = me
        else if (u.pathname === '/api/family-trees/') body = []
        else if (u.pathname === '/api/join-requests/mine/') body = []
        else if (u.pathname === '/api/relationship-types/') body = TYPES
        else if (u.pathname === '/api/family-members/') body = MEMBERS
        else if (u.pathname === '/api/relationships/') body = SIBLINGS
        else if (u.pathname === '/api/staff/trees/') {
          const q = (u.searchParams.get('q') ?? '').toLowerCase()
          const results = STAFF_TREES.filter((t) => t.tree_name.toLowerCase().includes(q))
          body = { count: results.length, results }
        } else if (u.pathname === '/api/staff/trees/1/') body = STAFF_DETAIL
      }
      return new Response(JSON.stringify(body), { status: 200 })
    }),
  )
}

function visit(path: string, me: User) {
  fakeBackend(me)
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { qc, user: userEvent.setup() }
}

const staffRequests = () => calls.filter((c) => c.path.startsWith('/api/staff/'))

describe('staff pages: who can get in', () => {
  it('sends a regular user from /staff/trees back to their families, without ever asking for staff data', async () => {
    visit('/staff/trees', GUEST)
    expect(await screen.findByRole('heading', { level: 1, name: /your families/i })).toBeTruthy()
    expect(staffRequests()).toEqual([])
  })

  it('does the same for a direct link to one tree', async () => {
    visit('/staff/trees/1', GUEST)
    expect(await screen.findByRole('heading', { level: 1, name: /your families/i })).toBeTruthy()
    expect(staffRequests()).toEqual([])
  })

  it('shows a regular user no staff link in the top bar', async () => {
    visit('/', GUEST)
    await screen.findByRole('heading', { level: 1, name: /your families/i })
    await screen.findByText(GUEST.first_name) // top bar finished loading "me"
    expect(screen.queryByRole('link', { name: /all trees/i })).toBeNull()
  })

  it('shows a superuser the staff link', async () => {
    visit('/', SUPERUSER)
    expect(await screen.findByRole('link', { name: /all trees/i })).toBeTruthy()
  })

  it('sends someone who is signed out to the login page', async () => {
    fakeBackend(SUPERUSER)
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{}', { status: 401 })))
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={['/staff/trees']}>
          <AppRoutes />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    await waitFor(() => expect(screen.queryByRole('heading', { name: /all families/i })).toBeNull())
    expect(screen.queryByText('Smith Family')).toBeNull()
  })
})

describe('staff pages: browsing', () => {
  it('lists every tree with owner, counts and a deleted flag', async () => {
    visit('/staff/trees', SUPERUSER)
    const smith = (await screen.findByRole('link', { name: 'Smith Family' })).closest('tr')!
    expect(within(smith).getByText('owner@example.com')).toBeTruthy()
    expect(within(smith).queryByText(/deleted/i)).toBeNull()
    const jones = screen.getByRole('link', { name: 'Jones Family' }).closest('tr')!
    expect(within(jones).getByText('guest@example.com')).toBeTruthy()
    expect(within(jones).getByText(/deleted/i)).toBeTruthy()
  })

  it('searches', async () => {
    const { user } = visit('/staff/trees', SUPERUSER)
    await screen.findByRole('link', { name: 'Smith Family' })
    await user.type(screen.getByRole('searchbox', { name: /search/i }), 'jones')
    await waitFor(() => expect(screen.queryByRole('link', { name: 'Smith Family' })).toBeNull())
    expect(screen.getByRole('link', { name: 'Jones Family' })).toBeTruthy()
    expect(staffRequests().some((c) => c.path.includes('q=jones'))).toBe(true)
  })

  it('opens a tree read-only: banner, canvas, person details, and no way to change anything', async () => {
    const { user } = visit('/staff/trees', SUPERUSER)
    await user.click(await screen.findByRole('link', { name: 'Smith Family' }))
    expect(await screen.findByRole('note')).toBeTruthy() // the "viewing as staff, read-only" banner
    expect(screen.getByRole('note').textContent).toMatch(/read-only/i)
    expect(screen.getByRole('note').textContent).toContain('owner@example.com')

    await user.click(await screen.findByRole('button', { name: /pick ben/i }))
    await screen.findByRole('complementary', { name: /details for ben/i })
    await waitFor(() => expect(calls.filter((c) => c.path.startsWith('/api/relationship-types')).length).toBeGreaterThan(-1))

    // The details are there...
    expect(screen.getByText(/brother/i)).toBeTruthy()
    // ...but nothing to change them with.
    for (const name of [/^edit$/i, /delete/i, /remove relationship/i, /edit relationship/i, /connect/i, /undo/i]) {
      expect(screen.queryByRole('button', { name }), String(name)).toBeNull()
    }
    expect(screen.queryByRole('heading', { name: /connect someone/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /add person|poster/i })).toBeNull()
    expect(screen.queryByRole('link', { name: /manage/i })).toBeNull()
    // And no request that could change data was ever sent.
    expect(calls.filter((c) => c.method !== 'GET')).toEqual([])
  })
})
