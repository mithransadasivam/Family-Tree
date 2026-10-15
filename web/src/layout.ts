import type { Unit } from './graph'

// Card and spacing metrics (SVG units).
export const W = 216 // card width
export const H = 80 // card height
export const AV = 24 // avatar radius
export const G = 44 // gap between spouses (holds the rings link)
export const SG = 44 // gap between sibling subtrees
export const TG = 110 // gap between separate family lines
export const VG = 84 // vertical gap between generations
export const PAD = 60

export const clip = (s: string, n: number) => (s.length > n ? `${s.slice(0, n - 1)}…` : s)
export const unitWidth = (u: Unit) => u.people.length * W + (u.people.length - 1) * G

export interface Placed {
  unit: Unit
  cx: number // centre of the whole unit
  y: number // vertical centre of its cards
  depth: number // absolute generation row
  kids: Placed[]
}

export const personX = (p: Placed, i: number) => p.cx - unitWidth(p.unit) / 2 + i * (W + G) + W / 2

/**
 * Lay out a forest. Within a tree, children sit side by side with each parent unit centred
 * over them. A secondary tree (e.g. a spouse's parents) is dropped to the row just above the
 * person it connects to and slid sideways so it sits directly above that person, as close as
 * the space already used by earlier trees allows. Unconnected trees go to the right.
 */
export function layoutForest(forest: Unit[]) {
  const widths = new Map<Unit, number>()
  const measure = (u: Unit): number => {
    const span = u.children.reduce((sum, c) => sum + measure(c), 0) + SG * Math.max(0, u.children.length - 1)
    const w = Math.max(unitWidth(u), span)
    widths.set(u, w)
    return w
  }

  const place = (u: Unit, left: number, depth: number): Placed => {
    const sw = widths.get(u)!
    const span = u.children.reduce((s, c) => s + widths.get(c)!, 0) + SG * Math.max(0, u.children.length - 1)
    let x = left + (sw - span) / 2
    const kids = u.children.map((c) => {
      const p = place(c, x, depth + (c.skip ? 2 : 1))
      x += widths.get(c)! + SG
      return p
    })
    const half = unitWidth(u) / 2
    const mid = kids.length ? (kids[0].cx + kids[kids.length - 1].cx) / 2 : left + sw / 2
    const cx = Math.min(Math.max(mid, left + half), left + sw - half)
    return { unit: u, cx, y: depth * (H + VG) + H / 2, depth, kids }
  }
  const flatten = (p: Placed, out: Placed[] = []): Placed[] => {
    out.push(p)
    p.kids.forEach((k) => flatten(k, out))
    return out
  }

  const rowOf = new Map<number, number>() // person id -> absolute row
  const pos = new Map<number, { x: number; y: number }>() // person id -> card centre
  const rowRight = new Map<number, number>() // row -> right edge of everything placed so far
  const all: Placed[] = []
  let maxRow = 0
  let right = 0

  for (const root of forest) {
    measure(root)

    // The row this tree starts on: just above the person it links to (if any).
    let anchor: { row: number; unit: Unit; person: number } | null = null
    const find = (u: Unit, d: number) => {
      if (anchor) return
      for (const r of u.refs) {
        const row = rowOf.get(r)
        if (row !== undefined) {
          anchor = { row: Math.max(0, row - 1 - d), unit: u, person: r }
          return
        }
      }
      u.children.forEach((c) => find(c, d + (c.skip ? 2 : 1)))
    }
    find(root, 0)
    const base = (anchor as { row: number } | null)?.row ?? 0

    // Lay out at x = 0, measure how far left it reaches in each row, then pick the offset.
    const draft = flatten(place(root, 0, base))
    let offset = 0
    for (const p of draft) {
      const taken = rowRight.get(p.depth)
      if (taken !== undefined) offset = Math.max(offset, taken + TG - (p.cx - unitWidth(p.unit) / 2))
    }
    const link = anchor as { unit: Unit; person: number } | null
    if (link) {
      const parent = draft.find((p) => p.unit === link.unit)
      const target = pos.get(link.person)
      // Sit directly above the person this family connects to, when there is room.
      if (parent && target) offset = Math.max(offset, target.x - parent.cx)
    }

    const placedTree = place(root, offset, base)
    for (const p of flatten(placedTree)) {
      all.push(p)
      maxRow = Math.max(maxRow, p.depth)
      rowRight.set(p.depth, Math.max(rowRight.get(p.depth) ?? -Infinity, p.cx + unitWidth(p.unit) / 2))
      right = Math.max(right, p.cx + unitWidth(p.unit) / 2)
      p.unit.people.forEach((m, i) => {
        rowOf.set(m.id, p.depth)
        pos.set(m.id, { x: personX(p, i), y: p.y })
      })
    }
  }

  const left = Math.min(0, ...all.map((p) => p.cx - unitWidth(p.unit) / 2))
  return {
    placed: all,
    pos,
    left,
    width: Math.max(W, right - left),
    height: (maxRow + 1) * H + maxRow * VG,
  }
}

/** Path from a parent unit down to a card centred at (x2, y2 - H/2 .. top edge y2). */
export function linkPath(p: Placed, x2: number, y2: number) {
  const couple = p.unit.people.length > 1
  const x1 = couple ? p.cx : personX(p, 0)
  const sy = couple ? p.y + 8 : p.y + H / 2 // leave the rings link / card bottom
  const yb = couple ? p.y + H / 2 + 6 : sy // clear of the cards
  const ye = Math.min(y2, p.y + H / 2 + VG) // bend inside the gap below the parent row
  return `M${x1} ${sy} L${x1} ${yb} C${x1} ${yb + (ye - yb) / 2}, ${x2} ${ye - (ye - yb) / 2}, ${x2} ${ye} L${x2} ${y2}`
}
