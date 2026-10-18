import frauncesUrl from '@fontsource-variable/fraunces/files/fraunces-latin-wght-normal.woff2?url'
import frauncesItalicUrl from '@fontsource-variable/fraunces/files/fraunces-latin-wght-italic.woff2?url'
import interUrl from '@fontsource-variable/inter/files/inter-latin-wght-normal.woff2?url'
import { hueFor, initials } from './Avatar'
import type { Unit } from './graph'
import { AV, cardLines, clip, G, H, layoutForest, linkPath, personX, W } from './layout'
import { ringData } from './Rings'
import type { Member } from './types'

export type PosterTheme = 'light' | 'dark'

export interface PosterOptions {
  theme: PosterTheme
  title: string
  showDates: boolean
  /** member id -> image as a data: URI (photos that could be fetched). Omit to draw initials only. */
  photos?: Map<number, string>
  people: number
  generations: number
}

interface Palette {
  bg: string
  bg2: string
  ink: string
  ink2: string
  ink3: string
  sage: string
  gold: string
  card: string
  cardLine: string
  ring: string
  initL: number
}

const PALETTES: Record<PosterTheme, Palette> = {
  light: {
    bg: '#f4eee0', bg2: '#ece3cf', ink: '#1b2a23', ink2: '#4a5b51', ink3: '#7b887f',
    sage: '#1d6a51', gold: '#a96a12', card: '#fffcf4', cardLine: 'rgba(70,55,25,0.28)',
    ring: '#1d6a51', initL: 28,
  },
  dark: {
    bg: '#07100d', bg2: '#0e1d17', ink: '#eef4ee', ink2: '#a9bdb2', ink3: '#70877b',
    sage: '#7fd6b0', gold: '#ecc277', card: '#10201a', cardLine: 'rgba(190,235,214,0.24)',
    ring: '#7fd6b0', initL: 70,
  },
}

const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

// ---------------------------------------------------------------------------------------
// Fonts and photos: an SVG drawn as an image cannot load anything from the network, so the
// fonts (and any photos) are inlined as data: URIs.
// ---------------------------------------------------------------------------------------

async function toDataUri(res: Response, fallbackType: string): Promise<string> {
  const blob = await res.blob()
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(String(r.result).replace(/^data:[^;,]*/, `data:${blob.type || fallbackType}`))
    r.onerror = () => reject(r.error)
    r.readAsDataURL(blob)
  })
}

let fontCss: Promise<string> | null = null
export function loadPosterFonts(): Promise<string> {
  fontCss ??= (async () => {
    const face = async (family: string, url: string, style: string) => {
      const uri = await toDataUri(await fetch(url), 'font/woff2')
      return `@font-face{font-family:'${family}';font-style:${style};font-weight:100 900;src:url(${uri}) format('woff2');}`
    }
    return (
      await Promise.all([
        face('Fraunces Poster', frauncesUrl, 'normal'),
        face('Fraunces Poster', frauncesItalicUrl, 'italic'),
        face('Inter Poster', interUrl, 'normal'),
      ])
    ).join('')
  })().catch((e) => {
    fontCss = null
    throw e
  })
  return fontCss
}

/** Fetch member photos as data URIs. Photos whose host blocks cross-origin reads are skipped
 *  (they fall back to initials). */
export async function loadPhotos(members: Member[]): Promise<Map<number, string>> {
  const out = new Map<number, string>()
  await Promise.all(
    members
      .filter((m) => /^https?:\/\//i.test(m.photo_url))
      .map(async (m) => {
        try {
          const res = await fetch(m.photo_url, { mode: 'cors', referrerPolicy: 'no-referrer' })
          if (res.ok) out.set(m.id, await toDataUri(res, 'image/jpeg'))
        } catch {
          // No CORS permission or offline: draw initials instead.
        }
      }),
  )
  return out
}

// ---------------------------------------------------------------------------------------
// The poster
// ---------------------------------------------------------------------------------------

export interface Poster {
  svg: string
  width: number
  height: number
}

const MARGIN_X = 150
const HEADER = 300
const FOOTER = 170

export function buildPoster(forest: Unit[], opts: PosterOptions, fonts: string, seed = 7): Poster {
  const c = PALETTES[opts.theme]
  const { placed, pos, left, width, height } = layoutForest(forest)

  const width_ = Math.max(1500, width + MARGIN_X * 2)
  // Small trees are scaled up to fill the sheet; big ones stay at natural size.
  const k = Math.min(1.9, (width_ - MARGIN_X * 2) / width)
  const height_ = HEADER + height * k + FOOTER
  const serif = `'Fraunces Poster','Iowan Old Style',Georgia,serif`
  const sans = `'Inter Poster',system-ui,'Segoe UI',sans-serif`

  const defs: string[] = []
  const body: string[] = []

  // Background: parchment / night, big growth rings in two corners, a double frame.
  body.push(`<rect width="${width_}" height="${height_}" fill="${c.bg}"/>`)
  const rings = (cx: number, cy: number, size: number, s: number, count: number, opacity: number) => {
    const { paths } = ringData(s, count)
    const k = size / 400
    return `<g transform="translate(${cx - size / 2} ${cy - size / 2}) scale(${k})" fill="none" stroke="${c.ring}" opacity="${opacity}">${paths
      .map((p) => `<path d="${p.d}" stroke-width="${(p.w / k) * 1.1}" opacity="${p.o}"/>`)
      .join('')}</g>`
  }
  defs.push(`<clipPath id="page"><rect width="${width_}" height="${height_}"/></clipPath>`)
  body.push(
    `<g clip-path="url(#page)">${rings(width_ - 80, 60, 1100, seed, 28, 0.2)}${rings(60, height_ - 40, 900, seed + 9, 22, 0.16)}</g>`,
  )
  body.push(
    `<rect x="46" y="46" width="${width_ - 92}" height="${height_ - 92}" rx="8" fill="none" stroke="${c.gold}" stroke-width="2" opacity="0.7"/>` +
      `<rect x="62" y="62" width="${width_ - 124}" height="${height_ - 124}" rx="4" fill="none" stroke="${c.gold}" stroke-width="1" opacity="0.4"/>`,
  )

  // Header
  const cx = width_ / 2
  body.push(
    `<text x="${cx}" y="150" text-anchor="middle" font-family="${sans}" font-size="22" font-weight="600" letter-spacing="7" fill="${c.gold}">A FAMILY TREE</text>`,
    `<text x="${cx}" y="236" text-anchor="middle" font-family="${serif}" font-size="88" font-weight="400" fill="${c.ink}">${esc(clip(opts.title, 48))}</text>`,
    `<text x="${cx}" y="284" text-anchor="middle" font-family="${sans}" font-size="24" fill="${c.ink2}">${opts.people} ${opts.people === 1 ? 'person' : 'people'}  ·  ${opts.generations} ${opts.generations === 1 ? 'generation' : 'generations'}</text>`,
  )

  // Links first, then spouse rings, then cards, so cards paint over link ends.
  const links: string[] = []
  for (const p of placed) {
    for (const kid of p.kids) links.push(linkPath(p, personX(kid, 0), kid.y - H / 2))
    for (const id of p.unit.refs) {
      const at = pos.get(id)
      if (at && at.y - H / 2 > p.y + H / 2) links.push(linkPath(p, at.x, at.y - H / 2))
    }
  }
  body.push(`<g transform="translate(${(width_ - width * k) / 2 - left * k} ${HEADER}) scale(${k})">`)
  body.push(
    `<g fill="none" stroke="${c.sage}" stroke-width="2.4" stroke-linecap="round" opacity="0.6">${links
      .map((d) => `<path d="${d}"/>`)
      .join('')}</g>`,
  )

  const hsl = (id: number, a?: number) =>
    a === undefined ? `hsl(${hueFor(id)} 65% ${c.initL}%)` : `hsl(${hueFor(id)} 55% 50% / ${a})`

  const card = (m: Member, x: number, y: number) => {
    const ax = x - W / 2 + 42
    const photo = opts.photos?.get(m.id)
    const face = photo
      ? (defs.push(`<clipPath id="f${m.id}"><circle cx="${ax}" cy="${y}" r="${AV}"/></clipPath>`),
        `<image href="${photo}" x="${ax - AV}" y="${y - AV}" width="${AV * 2}" height="${AV * 2}" clip-path="url(#f${m.id})" preserveAspectRatio="xMidYMid slice"/>`)
      : `<circle cx="${ax}" cy="${y}" r="${AV}" fill="${hsl(m.id, 0.2)}"/><text x="${ax}" y="${y}" text-anchor="middle" dominant-baseline="central" font-family="${sans}" font-size="${(AV * 0.58).toFixed(1)}" font-weight="600" fill="${hsl(m.id)}">${esc(initials(m))}</text>`
    const text = cardLines(m, opts.showDates)
      .map((l) => {
        const y2 = y + l.dy
        const x2 = x - W / 2 + 80
        if (l.kind === 'life')
          return `<text x="${x2}" y="${y2}" dominant-baseline="central" font-family="${sans}" font-size="${l.size}" letter-spacing="0.4" fill="${c.ink3}">${esc(l.text)}</text>`
        const first = l.kind === 'first'
        return `<text x="${x2}" y="${y2}" dominant-baseline="central" font-family="${serif}" font-size="${l.size}" font-weight="${first ? 500 : 400}" fill="${first ? c.ink : c.ink2}">${esc(l.text)}</text>`
      })
      .join('')
    return (
      `<rect x="${x - W / 2}" y="${y - H / 2}" width="${W}" height="${H}" rx="22" fill="${c.card}" stroke="${c.cardLine}" stroke-width="1.4"/>` +
      `<circle cx="${ax}" cy="${y}" r="${AV + 4}" fill="none" stroke="${c.cardLine}" stroke-width="1.6"/>` +
      face +
      text
    )
  }

  for (const p of placed) {
    const y = p.y
    p.unit.people.forEach((_, i) => {
      if (i === 0) return
      const mx = personX(p, i - 1) + W / 2 + G / 2
      body.push(
        `<g fill="none" stroke="${c.gold}"><line x1="${mx - G / 2}" x2="${mx + G / 2}" y1="${y}" y2="${y}" stroke-width="1.4" opacity="0.6"/><circle cx="${mx - 5}" cy="${y}" r="8" stroke-width="2"/><circle cx="${mx + 5}" cy="${y}" r="8" stroke-width="2"/></g>`,
      )
    })
    p.unit.people.forEach((m, i) => body.push(card(m, personX(p, i), y)))
  }
  body.push('</g>')

  // Footer
  const fy = HEADER + height * k + 90
  const date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
  body.push(
    `<g transform="translate(${cx - 150} ${fy - 20})" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="16" cy="16" r="12.5" stroke="${c.gold}" stroke-width="1.4"/><circle cx="16" cy="16" r="8" stroke="${c.sage}" stroke-width="1" opacity="0.6"/><path d="M16 23V15.5M16 15.5 11.5 10M16 15.5 20.5 10" stroke="${c.gold}" stroke-width="1.8"/><circle cx="11.5" cy="9.5" r="1.7" fill="${c.sage}" stroke="none"/><circle cx="20.5" cy="9.5" r="1.7" fill="${c.sage}" stroke="none"/></g>`,
    `<text x="${cx - 104}" y="${fy + 2}" font-family="${serif}" font-size="26" fill="${c.ink}">Kinship</text>`,
    `<text x="${cx + 22}" y="${fy + 2}" font-family="${sans}" font-size="16" fill="${c.ink3}">Created ${esc(date)}</text>`,
  )

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width_}" height="${height_}" viewBox="0 0 ${width_} ${height_}">` +
    `<defs><style>${fonts}</style>${defs.join('')}</defs>${body.join('')}</svg>`
  return { svg, width: width_, height: height_ }
}

// ---------------------------------------------------------------------------------------
// Export helpers
// ---------------------------------------------------------------------------------------

export const svgBlob = (svg: string) => new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })

/** Rasterise the poster. The scale is capped so very large trees stay under canvas limits. */
export async function posterToPng(p: Poster): Promise<Blob> {
  const url = URL.createObjectURL(svgBlob(p.svg))
  try {
    const img = new Image()
    img.decoding = 'sync'
    await new Promise<void>((resolve, reject) => {
      img.onload = () => resolve()
      img.onerror = () => reject(new Error('Could not render the poster image'))
      img.src = url
    })
    // Give embedded fonts a moment to be applied before drawing.
    await new Promise((r) => setTimeout(r, 150))
    const scale = Math.max(0.5, Math.min(2.5, 9000 / Math.max(p.width, p.height), Math.sqrt(24e6 / (p.width * p.height))))
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(p.width * scale)
    canvas.height = Math.round(p.height * scale)
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Canvas is not available')
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    return await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('Could not create the PNG'))), 'image/png'),
    )
  } finally {
    URL.revokeObjectURL(url)
  }
}

/** Open the browser's print dialog for the poster (choose "Save as PDF" to get a PDF). */
export function printPoster(p: Poster) {
  const frame = document.createElement('iframe')
  frame.setAttribute('aria-hidden', 'true')
  Object.assign(frame.style, { position: 'fixed', right: '0', bottom: '0', width: '0', height: '0', border: '0' })
  const orientation = p.width >= p.height ? 'landscape' : 'portrait'
  frame.srcdoc =
    `<!doctype html><html><head><meta charset="utf-8"><title>Kinship poster</title><style>` +
    `@page{size:${orientation};margin:0}html,body{margin:0;background:#fff}` +
    `svg{display:block;width:100%;height:auto;max-height:100vh}` +
    `</style></head><body>${p.svg}</body></html>`
  frame.onload = () => {
    const w = frame.contentWindow
    if (!w) return
    w.focus()
    w.print()
    setTimeout(() => frame.remove(), 60_000)
  }
  document.body.appendChild(frame)
}

export const fileSafe = (s: string) =>
  (s.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'family-tree').slice(0, 60)

