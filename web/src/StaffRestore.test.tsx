import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AppRoutes } from './App'
import { ANN, MEMBERS, STAFF_DETAIL, STAFF_TREES, SUPERUSER, TYPES } from './testData'
import type { StaffStash, StaffStashRestored } from './types'

// The canvas is irrelevant here: a stand-in that lets the test select Ben.
vi.mock('./TreeView', async () => {
  const { createElement } = await import('react')
  return {
    default: ({ onSelect }: { onSelect: (id: number) => void }) =>
      createElement('button', { onClick: () => onSelect(2) }, 'pick Ben'),
  }
})

interface Call {
  method: string
  path: string
  body: Record<string, unknown> | null
}
let calls: Call[] = []
const writes = () => calls.filter((c) => c.method !== 'GET').map((c) => `${c.method} ${c.path}`)

const RESTORED_BEN: StaffStashRestored = {
  member: { ...MEMBERS[1] },
  restored_relationships: 1,
  skipped_relationships: [],
  account_link: 'restored',
}

/** What the fake server answers when asked to restore from the stash. */
let restoreAnswer: { status: number; body: unknown } = { status: 200, body: RESTORED_BEN }
let stashes: StaffStash[] = []

function visit() {
  calls = []
  restoreAnswer = { status: 200, body: RESTORED_BEN }
  stashes = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      const u = new URL(url, 'http://localhost')
      const method = init?.method ?? 'GET'
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null
      calls.push({ method, path: u.pathname, body })
      let out: unknown = {}
      let status = 200
      if (method === 'GET') {
        if (u.pathname === '/api/users/me/') out = SUPERUSER
        else if (u.pathname === '/api/family-trees/') out = []
        else if (u.pathname === '/api/join-requests/mine/') out = []
        else if (u.pathname === '/api/relationship-types/') out = TYPES
        else if (u.pathname === '/api/staff/trees/1/') out = STAFF_DETAIL
        else if (u.pathname === '/api/staff/trees/1/restores/') out = stashes
        else if (u.pathname === '/api/staff/trees/') out = { count: STAFF_TREES.length, results: STAFF_TREES }
      } else if (method === 'DELETE' && u.pathname === '/api/staff/trees/1/members/2/') {
        out = { message: 'Member deleted', restore_id: 7 }
      } else if (method === 'POST' && u.pathname.startsWith('/api/staff/trees/1/restores/')) {
        ;({ status, body: out } = restoreAnswer)
      } else if (method === 'POST' && u.pathname.endsWith('/members/')) {
        out = { ...ANN, id: 99, first_name: String(body?.first_name ?? '') }
      }
      return new Response(JSON.stringify(out), { status })
    }),
  )
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <MemoryRouter initialEntries={['/staff/trees/1']}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return userEvent.setup()
}

/** Open Ben, turn on edit mode, delete him, and press Undo. */
async function deleteBenAndUndo(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole('button', { name: /pick ben/i }))
  await screen.findByRole('complementary', { name: /details for ben/i })
  await user.click(screen.getByRole('button', { name: /edit this tree/i }))
  await user.click(screen.getByRole('button', { name: /^delete$/i }))
  await user.click(await screen.findByRole('button', { name: /undo/i }))
}

describe('undo after a staff delete uses the server-side stash', () => {
  it('asks the server to restore, and re-creates nothing from the web’s own copy', async () => {
    const user = visit()
    await deleteBenAndUndo(user)
    await waitFor(() => expect(writes().length).toBe(2))
    expect(writes()).toEqual(['DELETE /api/staff/trees/1/members/2/', 'POST /api/staff/trees/1/restores/7/'])
    // the person is selected again afterwards (the page shows them, using the id the server returned)
    await screen.findByRole('complementary', { name: /details for ben/i })
  })

  it('falls back to the web’s own copy when the stash is gone (404)', async () => {
    const user = visit()
    restoreAnswer = { status: 404, body: { error: 'There is nothing to restore here.' } }
    await deleteBenAndUndo(user)
    await waitFor(() => expect(writes().length).toBe(4))
    expect(writes()).toEqual([
      'DELETE /api/staff/trees/1/members/2/',
      'POST /api/staff/trees/1/restores/7/',
      'POST /api/staff/trees/1/members/',
      'POST /api/staff/trees/1/relationships/',
    ])
  })

  it('falls back the same way when the stash has expired (410)', async () => {
    const user = visit()
    restoreAnswer = { status: 410, body: { error: 'This person was deleted too long ago to be restored.' } }
    await deleteBenAndUndo(user)
    await waitFor(() => expect(writes().length).toBe(4))
    expect(writes().slice(1, 3)).toEqual(['POST /api/staff/trees/1/restores/7/', 'POST /api/staff/trees/1/members/'])
  })

  it('does NOT fall back on any other failure: a second copy of the person must not be created', async () => {
    const user = visit()
    restoreAnswer = { status: 500, body: { error: 'Something broke' } }
    await deleteBenAndUndo(user)
    await screen.findByText(/something broke/i)
    expect(writes()).toEqual(['DELETE /api/staff/trees/1/members/2/', 'POST /api/staff/trees/1/restores/7/'])
  })

  it('does not fall back when the restore ran but some links no longer fit: it says which', async () => {
    const user = visit()
    restoreAnswer = {
      status: 200,
      body: {
        ...RESTORED_BEN,
        restored_relationships: 0,
        skipped_relationships: [{ link: 'Ann Test is the Brother of Ben Test', reason: 'the other person is no longer in this family' }],
      },
    }
    await deleteBenAndUndo(user)
    await screen.findByText(/1 of 1 relationships could not be/i)
    expect(screen.getByText(/no longer in this family/i)).toBeTruthy()
    expect(writes()).toEqual(['DELETE /api/staff/trees/1/members/2/', 'POST /api/staff/trees/1/restores/7/'])
  })
})

describe('the Recently deleted list', () => {
  const STASH: StaffStash = {
    id: 5, name: 'Ana Rao', deleted_at: '2026-11-01T10:00:00Z', expires_at: '2026-12-01T10:00:00Z',
    deleted_by: 'Rhea Root', relationship_count: 2,
  }

  it('is only offered in edit mode', async () => {
    const user = visit()
    await screen.findByRole('button', { name: /pick ben/i })
    expect(screen.queryByRole('button', { name: /recently deleted/i })).toBeNull()
    await user.click(screen.getByRole('button', { name: /edit this tree/i }))
    expect(screen.getByRole('button', { name: /recently deleted/i })).toBeTruthy()
    await user.click(screen.getByRole('button', { name: /stop editing/i }))
    expect(screen.queryByRole('button', { name: /recently deleted/i })).toBeNull()
  })

  it('lists names, dates and who deleted them, and says when there is nobody', async () => {
    const user = visit()
    await screen.findByRole('button', { name: /pick ben/i })
    await user.click(screen.getByRole('button', { name: /edit this tree/i }))
    await user.click(screen.getByRole('button', { name: /recently deleted/i }))
    expect(await screen.findByText(/nobody has been deleted recently/i)).toBeTruthy()
  })

  it('shows what is restorable and restores one person from the stash', async () => {
    const user = visit()
    stashes = [STASH]
    restoreAnswer = { status: 200, body: { ...RESTORED_BEN, restored_relationships: 2, account_link: 'dropped' } }
    await screen.findByRole('button', { name: /pick ben/i })
    await user.click(screen.getByRole('button', { name: /edit this tree/i }))
    await user.click(screen.getByRole('button', { name: /recently deleted/i }))
    const dialog = await screen.findByRole('dialog', { name: /recently deleted people/i })
    expect(within(dialog).getByText('Ana Rao')).toBeTruthy()
    expect(within(dialog).getByText(/by Rhea Root · 2 relationships/)).toBeTruthy()
    await user.click(within(dialog).getByRole('button', { name: /^restore$/i }))
    await within(dialog).findByText(/restored ana rao with 2 of 2 relationships/i)
    expect(within(dialog).getByText(/account link was not restored/i)).toBeTruthy()
    expect(writes()).toEqual(['POST /api/staff/trees/1/restores/5/'])
  })

  it('reports a restore the server refuses (for example, it expired meanwhile)', async () => {
    const user = visit()
    stashes = [STASH]
    restoreAnswer = { status: 410, body: { error: 'This person was deleted too long ago to be restored.' } }
    await screen.findByRole('button', { name: /pick ben/i })
    await user.click(screen.getByRole('button', { name: /edit this tree/i }))
    await user.click(screen.getByRole('button', { name: /recently deleted/i }))
    const dialog = await screen.findByRole('dialog', { name: /recently deleted people/i })
    await user.click(await within(dialog).findByRole('button', { name: /^restore$/i }))
    expect(await within(dialog).findByText(/too long ago/i)).toBeTruthy()
  })
})
