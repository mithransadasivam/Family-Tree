import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import TreePage from './TreePage'
import { GUEST, MEMBERS, OWNER, SIBLINGS, TREE, TYPES } from './testData'
import type { User } from './types'

// The canvas is irrelevant here: a stand-in that just lets the test select Ben.
vi.mock('./TreeView', async () => {
  const { createElement } = await import('react')
  return {
    default: ({ onSelect }: { onSelect: (id: number) => void }) =>
      createElement('button', { onClick: () => onSelect(2) }, 'pick Ben'),
  }
})

let calls: { method: string; url: string }[] = []

function fakeBackend(me: User) {
  calls = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string, init?: RequestInit) => {
      const method = init?.method ?? 'GET'
      // VITE_API_URL may prefix the path with a host; only the path matters here.
      const path = new URL(url, 'http://localhost').pathname + new URL(url, 'http://localhost').search
      calls.push({ method, url: path })
      let body: unknown = {}
      if (method === 'GET') {
        if (path.startsWith('/api/users/me/')) body = me
        else if (path.startsWith('/api/family-trees/')) body = [TREE]
        else if (path.startsWith('/api/family-members/')) body = MEMBERS
        else if (path.startsWith('/api/relationships/')) body = SIBLINGS
        else if (path.startsWith('/api/relationship-types/')) body = TYPES
      }
      return new Response(JSON.stringify(body), { status: 200 })
    }),
  )
}

async function openBensPanel(me: User) {
  fakeBackend(me)
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/trees/1']}>
        <Routes>
          <Route path="/trees/:treeId" element={<TreePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: /pick ben/i }))
  await screen.findByRole('complementary', { name: /details for ben/i })
  // Wait for "who am I" and "who owns this tree" to finish loading, so a missing button means
  // "hidden", not "still loading".
  await waitFor(() => expect(qc.isFetching()).toBe(0))
  return user
}

beforeEach(() => undefined)

describe('TreePage permissions', () => {
  it('shows a non-owner no delete actions, but they can still edit', async () => {
    await openBensPanel(GUEST)
    expect(screen.queryByRole('button', { name: /delete/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /remove relationship/i })).toBeNull()
    expect(screen.getByRole('button', { name: /^edit$/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /edit relationship with/i })).toBeTruthy()
    expect(calls.some((c) => c.method === 'DELETE')).toBe(false)
  })

  it('offers the owner Delete, and then Undo for it', async () => {
    const user = await openBensPanel(OWNER)
    await user.click(screen.getByRole('button', { name: /delete/i }))
    expect(await screen.findByText(/deleted ben test/i)).toBeTruthy()
    expect(screen.getByRole('button', { name: /^undo$/i })).toBeTruthy()
    expect(calls).toContainEqual({ method: 'DELETE', url: '/api/family-members/2/' })
  })

  it('offers the owner Undo after removing a relationship', async () => {
    const user = await openBensPanel(OWNER)
    await user.click(screen.getByRole('button', { name: /remove relationship with/i }))
    expect(await screen.findByRole('button', { name: /^undo$/i })).toBeTruthy()
    expect(calls).toContainEqual({ method: 'DELETE', url: '/api/relationships/10/' })
  })

  it('never shows a non-owner an Undo bar', async () => {
    await openBensPanel(GUEST)
    expect(screen.queryByRole('button', { name: /^undo$/i })).toBeNull()
    expect(screen.queryByRole('status', { name: '' })).toBeNull()
  })
})
