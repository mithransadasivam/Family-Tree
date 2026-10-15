import { useMemo } from 'react'

function rng(seed: number) {
  let a = seed >>> 0 || 1
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

interface Props {
  /** Same seed = same rings, so each tree gets a stable "fingerprint". */
  seed?: number
  count?: number
  className?: string
  /** Draw a growth crack and pith dot, like a cut trunk. */
  detail?: boolean
}

/** The geometry of a set of growth rings in a 400x400 box. Pure, so posters can reuse it. */
export function ringData(seed: number, count: number) {
  const r = rng(seed * 9301 + 49297)
  const size = 400
  const c = size / 2
  const harmonics = [
    { k: 2, a: 0.03 + r() * 0.03, p: r() * 6.28 },
    { k: 3, a: 0.02 + r() * 0.025, p: r() * 6.28 },
    { k: 5, a: 0.008 + r() * 0.014, p: r() * 6.28 },
    { k: 8, a: 0.004 + r() * 0.006, p: r() * 6.28 },
  ]
  const drift = r() * 6.28
  const paths: { d: string; o: number; w: number }[] = []
  for (let i = 1; i <= count; i++) {
    const base = (i / count) * (size * 0.47)
    const pts: string[] = []
    const n = 64
    for (let s = 0; s <= n; s++) {
      const ang = (s / n) * Math.PI * 2
      let wob = 1
      for (const h of harmonics) wob += h.a * Math.sin(h.k * ang + h.p + i * 0.11 + drift)
      // Rings get a little rounder toward the edge, like a real trunk.
      const rr = base * (1 + (wob - 1) * (1 - (i / count) * 0.35))
      pts.push(`${s === 0 ? 'M' : 'L'}${(c + rr * Math.cos(ang)).toFixed(1)} ${(c + rr * Math.sin(ang)).toFixed(1)}`)
    }
    paths.push({
      d: pts.join('') + 'Z',
      o: Math.min(1, 0.35 + 0.65 * (1 - i / count) + (i % 4 === 0 ? 0.25 : 0)),
      w: i % 5 === 0 ? 1.4 : 0.8,
    })
  }
  const ca = r() * 6.28
  const crack = `M${c} ${c} L${(c + Math.cos(ca) * size * 0.46).toFixed(1)} ${(c + Math.sin(ca) * size * 0.46).toFixed(1)}`
  return { paths, crack }
}

/** Concentric, slightly irregular growth rings, drawn in `currentColor`. */
export default function Rings({ seed = 1, count = 16, className, detail = true }: Props) {
  const { paths, crack } = useMemo(() => ringData(seed, count), [seed, count])

  return (
    <svg className={className} viewBox="0 0 400 400" fill="none" stroke="currentColor" aria-hidden>
      {paths.map((p, i) => (
        <path key={i} d={p.d} strokeWidth={p.w} opacity={p.o} />
      ))}
      {detail && (
        <>
          <path d={crack} strokeWidth="0.8" opacity=".35" strokeDasharray="3 5" />
          <circle cx="200" cy="200" r="2.2" fill="currentColor" stroke="none" />
        </>
      )}
    </svg>
  )
}
