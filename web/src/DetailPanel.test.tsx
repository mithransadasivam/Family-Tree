import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import DetailPanel from './DetailPanel'
import { ANN, BEN, MEMBERS, PARENT_CHILD, SIBLINGS, TYPES } from './testData'
import type { Relationship } from './types'

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(TYPES), { status: 200 })),
  )
})

function show(opts: { canDelete: boolean; relationships?: Relationship[] }) {
  const onDeleted = vi.fn()
  const onRelationshipRemoved = vi.fn()
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
      <DetailPanel
        treeId={1}
        member={BEN}
        members={MEMBERS}
        relationships={opts.relationships ?? SIBLINGS}
        canDelete={opts.canDelete}
        onEdit={() => undefined}
        onDeleted={onDeleted}
        onRelationshipRemoved={onRelationshipRemoved}
        onSelect={() => undefined}
        onClose={() => undefined}
      />
    </QueryClientProvider>,
  )
  return { onDeleted, onRelationshipRemoved }
}

describe('DetailPanel delete actions', () => {
  it('does not render the Delete button or relationship remove buttons for a non-owner', () => {
    show({ canDelete: false })
    expect(screen.queryByRole('button', { name: /delete/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /remove relationship/i })).toBeNull()
  })

  it('still lets a non-owner edit the person, edit a link and add one', () => {
    show({ canDelete: false })
    expect(screen.getByRole('button', { name: /^edit$/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /edit relationship with/i })).toBeTruthy()
    expect(screen.getByRole('heading', { name: /connect someone/i })).toBeTruthy()
  })

  it('does not explain a deletion rule the non-owner could never use', () => {
    // Ann is the Father of Ben, so Ann can't be deleted - but a non-owner never sees Delete at all.
    render(
      <QueryClientProvider client={new QueryClient()}>
        <DetailPanel
          treeId={1}
          member={ANN}
          members={MEMBERS}
          relationships={PARENT_CHILD}
          canDelete={false}
          onEdit={() => undefined}
          onDeleted={() => undefined}
          onRelationshipRemoved={() => undefined}
          onSelect={() => undefined}
          onClose={() => undefined}
        />
      </QueryClientProvider>,
    )
    expect(screen.queryByText(/so they can.t be deleted/i)).toBeNull()
  })

  it('renders the Delete button and relationship remove buttons for the owner', () => {
    show({ canDelete: true })
    expect(screen.getByRole('button', { name: /delete/i })).toBeTruthy()
    expect(screen.getByRole('button', { name: /remove relationship with/i })).toBeTruthy()
  })
})
