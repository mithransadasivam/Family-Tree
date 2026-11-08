import type { IgnoredLink } from './generations'

/**
 * Shown above the tree when some links contradict each other (usually one was saved the wrong way
 * round), so the picture is not silently wrong. The data is not changed: the link named here is
 * only left out of the drawing until someone edits or removes it.
 */
export default function TreeConflictNotice({ conflicts }: { conflicts: IgnoredLink[] }) {
  if (conflicts.length === 0) return null
  return (
    <div className="tree-notice" role="alert">
      <b>Some relationships in this family contradict each other.</b>{' '}
      To keep the tree readable, {conflicts.length === 1 ? 'this link is' : 'these links are'} not drawn:
      <ul>
        {conflicts.map((c) => (
          <li key={c.id}>
            <b>{c.reads}</b> — {c.why}.
            {c.alsoCheck.length > 0 && (
              <>
                {' '}
                It conflicts with: {c.alsoCheck.join('; ')}. If this link is right and one of those is wrong, fix
                that one instead.
              </>
            )}
          </li>
        ))}
      </ul>
      Open the people involved and edit or remove the link; the tree will redraw as soon as it is fixed.
    </div>
  )
}
