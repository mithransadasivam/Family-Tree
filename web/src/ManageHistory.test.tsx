import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AppRoutes } from './App'
import { OWNER, SUPERUSER, TREE } from './testData'
import type { EditHistory } from './types'

const HISTORY: EditHistory[] = [
  {
    id: 3, entity_type: 'family_member', entity_id: 2, field_name: 'first_name', old_value: 'Ben', new_value: 'Benji',
    change_description: 'Staff edit: Changed first name of Ben Test', edited_by: SUPERUSER,
    edited_at: '2026-11-05T10:00:00Z', by_staff: true,
  },
  {
    id: 2, entity_type: 'family_member', entity_id: 2, change_description: 'Updated member: Ben Test',
    edited_by: OWNER, edited_at: '2026-11-05T09:00:00Z', by_staff: false,
  },
  {
    id: 1, entity_type: 'family_member', entity_id: 1, change_description: 'Added member: Ann Test',
    edited_by: OWNER, edited_at: '2026-11-05T08:00:00Z',
  },
]

describe('the family history shows what staff changed', () => {
  it('badges staff changes, shows old and new values, and leaves the members’ own changes plain', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        const path = new URL(url, 'http://localhost').pathname
        const body =
          path === '/api/users/me/' ? OWNER
          : path === '/api/family-trees/' ? [TREE]
          : path === '/api/edit-history/' ? HISTORY
          : path === '/api/join-requests/' ? []
          : {}
        return new Response(JSON.stringify(body), { status: 200 })
      }),
    )
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter initialEntries={['/trees/1/manage']}>
          <AppRoutes />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    const staffRow = (await screen.findByText('Changed first name of Ben Test')).closest('li')!
    expect(within(staffRow).getByText('Staff')).toBeTruthy()
    expect(within(staffRow).getByText(/Ben → Benji/)).toBeTruthy()
    expect(within(staffRow).getByText(/Rhea/)).toBeTruthy() // who it was
    expect(staffRow.textContent).not.toMatch(/Staff edit:/) // the badge replaces the prefix, not both

    const plain = screen.getByText('Updated member: Ben Test').closest('li')!
    expect(within(plain).queryByText('Staff')).toBeNull()
    const added = screen.getByText('Added member: Ann Test').closest('li')!
    expect(within(added).queryByText('Staff')).toBeNull()
  })
})