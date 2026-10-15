import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { hueFor, initials, lifespan, photoSrc } from './Avatar'
import type { Unit } from './graph'
import { Fit } from './Icons'
import { AV, clip, G, H, layoutForest, linkPath, PAD, personX, W } from './layout'
import { fullName, type Member } from './types'

function Face({ m, cx, cy, r, id }: { m: Member; cx: number; cy: number; r: number; id: string }) {
  const src = photoSrc(m.photo_url)
  return (
    <g style={{ '--h': hueFor(m.id) } as CSSProperties}>
      <circle cx={cx} cy={cy} r={r} className="node-avatar-bg" />
      {src ? (
        <>
          <clipPath id={id}>
            <circle cx={cx} cy={cy} r={r} />
          </clipPath>
          <image
            href={src}
            x={cx - r}
            y={cy - r}
            width={r * 2}
            height={r * 2}
            clipPath={`url(#${id})`}
            preserveAspectRatio="xMidYMid slice"
          />
        </>
      ) : (
        <text x={cx} y={cy} className="node-init" style={{ fontSize: r * 0.58 }}>
          {initials(m)}
        </text>
      )}
    </g>
  )
}

function Card({
  m,
  x,
  y,
  depth,
  selected,
  onPick,
}: {
  m: Member
  x: number
  y: number
  depth: number
  selected: boolean
  onPick: (id: number) => void
}) {
  const ax = x - W / 2 + 42
  return (
    <g
      className={selected ? 'node selected' : 'node'}
      style={{ '--d': depth } as CSSProperties}
      role="button"
      tabIndex={0}
      aria-label={fullName(m)}
      aria-pressed={selected}
      onClick={() => onPick(m.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onPick(m.id)
        }
      }}
      data-testid={`node-${m.id}`}
    >
      <title>{fullName(m)}</title>
      {selected && <rect className="node-glow" x={x - W / 2 - 3} y={y - H / 2 - 3} width={W + 6} height={H + 6} rx={25} />}
      <rect className="node-card" x={x - W / 2} y={y - H / 2} width={W} height={H} rx={22} />
      <circle className="node-ring" cx={ax} cy={y} r={AV + 4} />
      <Face m={m} cx={ax} cy={y} r={AV} id={`clip-${m.id}`} />
      <text x={x - W / 2 + 80} y={y - 5} className="node-name">
        {clip(fullName(m), 17)}
      </text>
      <text x={x - W / 2 + 80} y={y + 16} className="node-sub">
        {lifespan(m) || ' '}
      </text>
    </g>
  )
}

/** Two interlocking rings: the marriage link drawn between spouses. */
function RingsLink({ x, y }: { x: number; y: number }) {
  return (
    <g className="spouse-link">
      <line x1={x - G / 2} x2={x + G / 2} y1={y} y2={y} />
      <circle cx={x - 5} cy={y} r={8} />
      <circle cx={x + 5} cy={y} r={8} />
    </g>
  )
}

interface Props {
  forest: Unit[]
  selectedId: number | null
  onSelect: (id: number) => void
  /** Bump `n` to pan the view so `id` is centred. */
  focus: { id: number; n: number } | null
}

interface View {
  x: number
  y: number
  k: number
}

export default function TreeView({ forest, selectedId, onSelect, focus }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const content = useRef<SVGGElement>(null)
  const view = useRef<View>({ x: 0, y: 0, k: 1 })
  const dragged = useRef(false)
  const [size, setSize] = useState({ w: 0, h: 0 })
  const [reset, setReset] = useState(0)

  const { placed, pos, left, width, height } = useMemo(() => layoutForest(forest), [forest])

  const apply = useCallback(() => {
    const { x, y, k } = view.current
    content.current?.setAttribute('transform', `translate(${x} ${y}) scale(${k})`)
  }, [])

  // Fit everything in view: when first measured, when the main tree changes, on "Recenter".
  const fitKey = `${forest[0]?.id}-${reset}-${size.w > 0}`
  const lastFit = useRef('')
  useLayoutEffect(() => {
    if (size.w === 0 || lastFit.current === fitKey) return
    lastFit.current = fitKey
    const k = Math.min(1, (size.w - PAD) / width, (size.h - PAD * 1.6) / height)
    view.current = { k, x: (size.w - width * k) / 2 - left * k, y: Math.max(PAD / 2, 44) }
    apply()
  }, [fitKey, size, left, width, height, apply])

  // Pan to a person (from search or a relationship link).
  const lastFocus = useRef(0)
  useEffect(() => {
    if (!focus || focus.n === lastFocus.current || size.w === 0) return
    lastFocus.current = focus.n
    const at = pos.get(focus.id)
    if (!at) return
    const k = Math.max(view.current.k, 0.75)
    view.current = { k, x: size.w / 2 - at.x * k, y: size.h / 2 - at.y * k }
    apply()
  }, [focus, pos, size, apply])

  useEffect(() => {
    const el = box.current
    if (!el) return
    const measure = () => setSize({ w: el.clientWidth, h: el.clientHeight })
    measure()
    const ro = new ResizeObserver(measure)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // Wheel zoom (needs a non-passive listener to prevent page scroll) and pointer pan / pinch.
  useEffect(() => {
    const el = box.current
    if (!el) return
    const zoomAt = (px: number, py: number, factor: number) => {
      const v = view.current
      const k = Math.min(2, Math.max(0.2, v.k * factor))
      const r = k / v.k
      view.current = { k, x: px - (px - v.x) * r, y: py - (py - v.y) * r }
      apply()
    }
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      const rect = el.getBoundingClientRect()
      zoomAt(e.clientX - rect.left, e.clientY - rect.top, Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0016)))
    }

    const pointers = new Map<number, { x: number; y: number }>()
    let pinch = 0
    let travelled = 0
    const onDown = (e: PointerEvent) => {
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY })
      if (pointers.size === 1) {
        dragged.current = false
        travelled = 0
      }
      pinch = 0
    }
    const onMove = (e: PointerEvent) => {
      const prev = pointers.get(e.pointerId)
      if (!prev) return
      const cur = { x: e.clientX, y: e.clientY }
      if (pointers.size === 1) {
        const dx = cur.x - prev.x
        const dy = cur.y - prev.y
        travelled += Math.abs(dx) + Math.abs(dy)
        if (travelled > 6) dragged.current = true
        if (dragged.current) {
          view.current = { ...view.current, x: view.current.x + dx, y: view.current.y + dy }
          apply()
        }
      } else if (pointers.size === 2) {
        pointers.set(e.pointerId, cur)
        const [a, b] = [...pointers.values()]
        const dist = Math.hypot(a.x - b.x, a.y - b.y)
        if (pinch) {
          const rect = el.getBoundingClientRect()
          zoomAt((a.x + b.x) / 2 - rect.left, (a.y + b.y) / 2 - rect.top, dist / pinch)
        }
        pinch = dist
        dragged.current = true
      }
      pointers.set(e.pointerId, cur)
    }
    const onUp = (e: PointerEvent) => {
      pointers.delete(e.pointerId)
      pinch = 0
    }

    el.addEventListener('wheel', onWheel, { passive: false })
    el.addEventListener('pointerdown', onDown)
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    window.addEventListener('pointercancel', onUp)
    return () => {
      el.removeEventListener('wheel', onWheel)
      el.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
      window.removeEventListener('pointercancel', onUp)
    }
  }, [apply])

  const pick = (id: number) => {
    if (!dragged.current) onSelect(id)
  }

  return (
    <>
      <div className="tree-canvas" ref={box}>
        <svg className="tree-svg" role="group" aria-label="Family tree">
          <g ref={content}>
            {/* Links first so cards paint over their ends. */}
            {placed.flatMap((p) => [
              ...p.kids.map((c, i) => (
                <path
                  key={`${p.unit.id}-${c.unit.id}`}
                  className="link"
                  pathLength={1}
                  style={{ '--d': c.depth, '--n': i } as CSSProperties}
                  d={linkPath(p, personX(c, 0), c.y - H / 2)}
                />
              )),
              // Children drawn elsewhere (e.g. a spouse beside their partner): link to that card.
              ...p.unit.refs.flatMap((id) => {
                const at = pos.get(id)
                if (!at || at.y - H / 2 <= p.y + H / 2) return []
                return [
                  <path
                    key={`${p.unit.id}~${id}`}
                    className="link"
                    pathLength={1}
                    style={{ '--d': p.depth + 1 } as CSSProperties}
                    d={linkPath(p, at.x, at.y - H / 2)}
                  />,
                ]
              }),
            ])}
            {placed.map((p) => (
              <g key={p.unit.id}>
                {p.unit.people.slice(1).map((_, i) => (
                  <RingsLink key={i} x={personX(p, i) + W / 2 + G / 2} y={p.y} />
                ))}
                {p.unit.people.map((m, i) => (
                  <Card
                    key={m.id}
                    m={m}
                    x={personX(p, i)}
                    y={p.y}
                    depth={p.depth}
                    selected={m.id === selectedId}
                    onPick={pick}
                  />
                ))}
              </g>
            ))}
          </g>
        </svg>
      </div>
      <div className="canvas-controls">
        <button className="ghost mini" onClick={() => setReset((n) => n + 1)} title="Show the whole family">
          <Fit size={15} /> Show all
        </button>
      </div>
      <div className="canvas-hint hide-sm">Drag to pan · Scroll to zoom · Click a person</div>
    </>
  )
}
