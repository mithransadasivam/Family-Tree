import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AppRoutes } from './App'
import DetailPanel from './DetailPanel'
import { ANN, BEN, GUEST, MEMBERS, SIBLINGS, STAFF_DETAIL, STAFF_TREES, SUPERUSER, TYPES } from './testData'
import type { User } from './types'

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
const writes = () => calls.filter((c) => c.method !== 'GET')

const DELETED_DETAIL = { ...STAFF_DETAIL, tree: STAFF_TREES[1] }
// Tree 1 as the fake server currently returns it; a test can swap in a bigger family.
let detail1 = STAFF_DETAIL

function fakeBackend(me: User) {
  calls = []
  detail1 = STAFF_DETAIL
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      const u = new URL(url, 'http://localhost')
      const method = init?.method ?? 'GET'
      const body = init?.body ? (JSON.parse(String(init.body)) as Record<string, unknown>) : null
      calls.push({ method, path: u.pathname + u.search, body })
      let out: unknown = {}
      if (method === 'GET') {
        if (u.pathname === '/api/users/me/') out = me
        else if (u.pathname === '/api/family-trees/') out = []
        else if (u.pathname === '/api/join-requests/mine/') out = []
        else if (u.pathname === '/api/relationship-types/') out = TYPES
        else if (u.pathname === '/api/staff/trees/1/') out = detail1
        else if (u.pathname === '/api/staff/trees/2/') out = DELETED_DETAIL
        else if (u.pathname === '/api/staff/trees/') out = { count: STAFF_TREES.length, results: STAFF_TREES }
      } else if (method === 'POST' && u.pathname.endsWith('/members/')) {
        out = { ...ANN, id: 99, first_name: String(body?.first_name ?? '') }
      }
      return new Response(JSON.stringify(out), { status: 200 })
    }),
  )
}

function visit(path: string, me: User = SUPERUSER) {
  fakeBackend(me)
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return userEvent.setup()
}

async function openBen(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole('button', { name: /pick ben/i }))
  return screen.findByRole('complementary', { name: /details for ben/i })
}

const editButton = () => screen.getByRole('button', { name: /edit this tree/i })

describe('staff edit mode: switching it on and off', () => {
  it('opens read-only and offers "Edit this tree"', async () => {
    const user = visit('/staff/trees/1')
    await openBen(user)
    expect(screen.getByRole('note').textContent).toMatch(/viewing as staff · read-only/i)
    expect(editButton().getAttribute('aria-pressed')).toBe('false')
    expect(screen.queryByRole('button', { name: /^edit$|delete|add person/i })).toBeNull()
    expect(writes()).toEqual([])
  })

  it('unlocks Add person, Edit, Delete, Connect and relationship editing, and says changes are live and visible to the owner', async () => {
    const user = visit('/staff/trees/1')
    await openBen(user)
    await user.click(editButton())

    const note = screen.getByRole('note').textContent ?? ''
    expect(note).toMatch(/editing as staff/i)
    expect(note).toMatch(/visible to its owner/i)
    expect(screen.getByRole('button', { name: /add person/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /^edit$/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /^delete$/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /remove relationship with/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /edit relationship with/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /connect someone/i })).toBeTruthy()
  })

  it('"Stop editing" locks everything again', async () => {
    const user = visit('/staff/trees/1')
    await openBen(user)
    await user.click(editButton())
    await user.click(screen.getByRole('button', { name: /stop editing/i }))
    expect(screen.getByRole('note').textContent).toMatch(/read-only/i)
    expect(screen.queryByRole('button', { name: /^edit$|delete|add person|remove relationship/i })).toBeNull()
    expect(screen.queryByRole('heading', { name: /connect someone/i })).toBeNull()
  })

  it('never remembers edit mode: coming back to the tree opens read-only again', async () => {
    const user = visit('/staff/trees/1')
    await openBen(user)
    await user.click(editButton())
    expect(screen.getByRole('button', { name: /stop editing/i })).toBeTruthy()
    // Navigate away and back through the page's own link.
    const back = screen.getAllByRole('link', { name: /all trees/i }).find((a) => a.classList.contains('back'))!
    await user.click(back)
    await user.click(await screen.findByRole('link', { name: 'Smith Family' }))
    await screen.findByRole('button', { name: /pick ben/i })
    expect(screen.getByRole('note').textContent).toMatch(/read-only/i)
  })

  it('a family its owner deleted cannot be edited at all', async () => {
    visit('/staff/trees/2')
    await screen.findByRole('button', { name: /pick ben/i })
    expect(screen.getByRole('note').textContent).toMatch(/deleted by its owner/i)
    const btn = editButton() as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    expect(btn.title).toMatch(/deleted by its owner/i)
  })

  it('a regular user cannot reach the page, so never sees an edit button or sends anything', async () => {
    visit('/staff/trees/1', GUEST)
    expect(await screen.findByRole('heading', { level: 1, name: /your families/i })).toBeTruthy()
    expect(screen.queryByRole('button', { name: /edit this tree/i })).toBeNull()
    expect(calls.filter((c) => c.path.startsWith('/api/staff/'))).toEqual([])
    expect(writes()).toEqual([])
  })
})

describe('staff edit mode: every write goes to the staff endpoints, and only those', () => {
  it('deletes a person (Ben has no children) and offers Undo', async () => {
    const user = visit('/staff/trees/1')
    await openBen(user)
    await user.click(editButton())
    await user.click(screen.getByRole('button', { name: /^delete$/i }))
    await screen.findByText(/deleted ben test/i)
    expect(screen.getByRole('button', { name: /undo/i })).toBeTruthy()
    expect(writes().map((c) => `${c.method} ${c.path}`)).toEqual(['DELETE /api/staff/trees/1/members/2/'])
  })

  it('undoing that delete re-creates the person and their links through the staff endpoints', async () => {
    const user = visit('/staff/trees/1')
    await openBen(user)
    await user.click(editButton())
    await user.click(screen.getByRole('button', { name: /^delete$/i }))
    await user.click(await screen.findByRole('button', { name: /undo/i }))
    await waitFor(() => expect(writes().length).toBe(3))
    expect(writes().map((c) => `${c.method} ${c.path}`)).toEqual([
      'DELETE /api/staff/trees/1/members/2/',
      'POST /api/staff/trees/1/members/',
      'POST /api/staff/trees/1/relationships/',
    ])
  })

  it('removes a relationship', async () => {
    const user = visit('/staff/trees/1')
    const panel = await openBen(user)
    await user.click(editButton())
    await user.click(within(panel).getByRole('button', { name: /remove relationship with/i }))
    await waitFor(() => expect(writes().length).toBe(1))
    expect(writes()[0]).toMatchObject({ method: 'DELETE', path: '/api/staff/trees/1/relationships/10/' })
  })

  it('edits a relationship in place (one PATCH, the stored direction kept)', async () => {
    const user = visit('/staff/trees/1')
    const panel = await openBen(user)
    await user.click(editButton())
    await user.click(within(panel).getByRole('button', { name: /edit relationship with/i }))
    await user.selectOptions(within(panel).getByRole('combobox', { name: /relationship type/i }), 'Sister')
    await user.click(within(panel).getByRole('button', { name: /^save$/i }))
    await waitFor(() => expect(writes().length).toBe(1))
    expect(writes()[0].method).toBe('PATCH')
    expect(writes()[0].path).toBe('/api/staff/trees/1/relationships/10/')
    // Ann is member_1 ("Ann is the Brother of Ben"), Ben was viewed: Ann stays first.
    expect(writes()[0].body).toMatchObject({ member_1: 1, member_2: 2, relationship_type: 2 })
  })

  it('edits a person without ever showing or sending a phone number', async () => {
    const user = visit('/staff/trees/1')
    await openBen(user)
    await user.click(editButton())
    await user.click(screen.getByRole('button', { name: /^edit$/i }))
    expect(screen.queryByLabelText(/phone number/i)).toBeNull()
    const first = screen.getByDisplayValue('Ben')
    await user.clear(first)
    await user.type(first, 'Benji')
    await user.click(screen.getByRole('button', { name: /save changes/i }))
    await waitFor(() => expect(writes().length).toBe(1))
    expect(writes()[0].method).toBe('PATCH')
    expect(writes()[0].path).toBe('/api/staff/trees/1/members/2/')
    expect(writes()[0].body).toMatchObject({ first_name: 'Benji' })
    expect(writes()[0].body).not.toHaveProperty('phone')
    expect(writes()[0].body).not.toHaveProperty('phone_public')
  })

  it('adds a person and links them, as one create plus one link', async () => {
    const user = visit('/staff/trees/1')
    await screen.findByRole('button', { name: /pick ben/i })
    await user.click(editButton())
    await user.click(screen.getByRole('button', { name: /add person/i }))
    const dialog = (await screen.findByRole('heading', { name: /add to the family/i })).closest('form')!
    const form = within(dialog)
    const [first, last] = form.getAllByRole('textbox')
    await user.type(first, 'Cy')
    await user.type(last, 'Test')
    await user.selectOptions(form.getByRole('combobox', { name: /relationship type/i }), 'Brother')
    await user.selectOptions(form.getByRole('combobox', { name: /related person/i }), 'Ann Test')
    await user.click(form.getByRole('button', { name: /^add person$/i }))
    await waitFor(() => expect(writes().length).toBe(2))
    expect(writes().map((c) => `${c.method} ${c.path}`)).toEqual([
      'POST /api/staff/trees/1/members/',
      'POST /api/staff/trees/1/relationships/',
    ])
    expect(writes()[1].body).toMatchObject({ member_1: 99, member_2: 1, relationship_type: 1 })
  })

  it('connects two people from the panel, as "[other] is the [type] of [this person]"', async () => {
    const user = visit('/staff/trees/1')
    // Same family plus Cy, who is not connected to anyone yet.
    detail1 = { ...STAFF_DETAIL, members: [...MEMBERS, { ...ANN, id: 3, first_name: 'Cy' }] }
    await screen.findByRole('button', { name: /pick ben/i })
    await user.click(await screen.findByRole('button', { name: /edit this tree/i }))
    await user.click(screen.getByRole('button', { name: /pick ben/i }))
    const panel = await screen.findByRole('complementary', { name: /details for ben/i })
    await user.selectOptions(within(panel).getByRole('combobox', { name: /related member/i }), 'Cy Test')
    await user.selectOptions(within(panel).getByRole('combobox', { name: /relationship type/i }), 'Father')
    await user.click(within(panel).getByRole('button', { name: /^connect$/i }))
    await waitFor(() => expect(writes().length).toBe(1))
    expect(writes()[0]).toMatchObject({
      method: 'POST',
      path: '/api/staff/trees/1/relationships/',
      body: { tree: 1, member_1: 3, member_2: 2, relationship_type: 3 },
    })
  })

  it('no request outside /api/staff/ ever changes data, across a whole edit session', async () => {
    const user = visit('/staff/trees/1')
    const panel = await openBen(user)
    await user.click(editButton())
    await user.click(within(panel).getByRole('button', { name: /remove relationship with/i }))
    await user.click(await screen.findByRole('button', { name: /undo/i }))
    await waitFor(() => expect(writes().length).toBe(2))
    expect(writes().every((c) => c.path.startsWith('/api/staff/trees/1/'))).toBe(true)
  })
})

describe('the normal family page is untouched', () => {
  it('still writes to the normal endpoints, never the staff ones', async () => {
    fakeBackend(SUPERUSER)
    const user = userEvent.setup()
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <DetailPanel
          treeId={1}
          member={BEN}
          members={MEMBERS}
          relationships={SIBLINGS}
          canDelete
          onEdit={() => undefined}
          onDeleted={() => undefined}
          onRelationshipRemoved={() => undefined}
          onSelect={() => undefined}
          onClose={() => undefined}
        />
      </QueryClientProvider>,
    )
    await user.click(screen.getByRole('button', { name: /remove relationship with/i }))
    await waitFor(() => expect(writes().length).toBe(1))
    expect(writes()[0]).toMatchObject({ method: 'DELETE', path: '/api/relationships/10/' })
    await user.click(screen.getByRole('button', { name: /^delete$/i }))
    await waitFor(() => expect(writes().length).toBe(2))
    expect(writes()[1]).toMatchObject({ method: 'DELETE', path: '/api/family-members/2/' })
    expect(calls.some((c) => c.path.startsWith('/api/staff/'))).toBe(false)
  })
})
