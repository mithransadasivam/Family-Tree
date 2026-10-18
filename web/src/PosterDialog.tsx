import { useEffect, useRef, useState } from 'react'
import type { KnownGender, Unit } from './graph'
import { Close, Download, Printer, Share } from './Icons'
import {
  buildPoster,
  fileSafe,
  loadPhotos,
  loadPosterFonts,
  posterToPng,
  printPoster,
  svgBlob,
  type Poster,
  type PosterTheme,
} from './poster'
import type { Member } from './types'

interface Props {
  genders: Map<number, KnownGender>
  forest: Unit[]
  members: Member[]
  treeName: string
  people: number
  generations: number
  onClose: () => void
}

function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}

export default function PosterDialog({ genders, forest, members, treeName, people, generations, onClose }: Props) {
  const [theme, setTheme] = useState<PosterTheme>('light')
  const [title, setTitle] = useState(treeName)
  const [showDates, setShowDates] = useState(true)
  const [showPhotos, setShowPhotos] = useState(true)
  const [poster, setPoster] = useState<Poster | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [busy, setBusy] = useState<'png' | 'share' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const photos = useRef<Map<number, string> | null>(null)

  const canShare =
    typeof navigator !== 'undefined' &&
    typeof navigator.canShare === 'function' &&
    navigator.canShare({ files: [new File([''], 'x.png', { type: 'image/png' })] })

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  // Rebuild the poster when an option changes (title edits are debounced).
  useEffect(() => {
    let cancelled = false
    const t = setTimeout(async () => {
      try {
        const fonts = await loadPosterFonts()
        if (showPhotos && photos.current === null) photos.current = await loadPhotos(members)
        if (cancelled) return
        setPoster(
          buildPoster(forest, {
            theme,
            title: title.trim() || treeName,
            showDates,
            photos: showPhotos ? (photos.current ?? undefined) : undefined,
            genders,
            people,
            generations,
          }, fonts),
        )
        setError(null)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Could not build the poster')
      }
    }, 200)
    return () => {
      cancelled = true
      clearTimeout(t)
    }
  }, [forest, members, genders, theme, title, treeName, showDates, showPhotos, people, generations])

  useEffect(() => {
    if (!poster) return
    const url = URL.createObjectURL(svgBlob(poster.svg))
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [poster])

  const name = fileSafe(title || treeName)
  const run = async (kind: 'png' | 'share', fn: (png: Blob) => Promise<void> | void) => {
    if (!poster) return
    setBusy(kind)
    setError(null)
    try {
      await fn(await posterToPng(poster))
    } catch (e) {
      if (!(e instanceof DOMException && e.name === 'AbortError')) {
        setError(e instanceof Error ? e.message : 'Something went wrong')
      }
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal poster-modal" role="dialog" aria-label="Family tree poster" onClick={(e) => e.stopPropagation()}>
        <div className="row between" style={{ alignItems: 'flex-start' }}>
          <div>
            <span className="eyebrow">Keep it, print it, share it</span>
            <h3 style={{ marginTop: 8 }}>Make a poster</h3>
          </div>
          <button className="ghost icon-btn" onClick={onClose} aria-label="Close">
            <Close size={16} />
          </button>
        </div>

        <div className="poster-controls">
          <label className="field grow">
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={60} />
          </label>
          <div className="field">
            Style
            <div className="seg" role="group" aria-label="Poster style">
              {(['light', 'dark'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  className={theme === t ? 'on' : ''}
                  aria-pressed={theme === t}
                  onClick={() => setTheme(t)}
                >
                  {t === 'light' ? 'Light' : 'Dark'}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="row wrap" style={{ gap: 22, marginTop: 0 }}>
          <label className="check">
            <input type="checkbox" checked={showDates} onChange={(e) => setShowDates(e.target.checked)} />
            <span>Birth and death years</span>
          </label>
          <label className="check">
            <input type="checkbox" checked={showPhotos} onChange={(e) => setShowPhotos(e.target.checked)} />
            <span>Photos</span>
          </label>
        </div>

        <div className="poster-preview" data-theme-preview={theme}>
          {previewUrl ? (
            <img src={previewUrl} alt={`Poster preview for ${title || treeName}`} />
          ) : (
            <div className="skeleton" style={{ width: '100%', height: 260 }} role="status" aria-label="Building poster" />
          )}
        </div>

        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}

        <div className="row wrap end">
          {canShare && (
            <button
              className="ghost"
              disabled={!poster || busy !== null}
              onClick={() =>
                run('share', async (png) => {
                  await navigator.share({ files: [new File([png], `${name}.png`, { type: 'image/png' })], title: title || treeName })
                })
              }
            >
              <Share size={16} /> Share
            </button>
          )}
          <button className="ghost" disabled={!poster} onClick={() => poster && save(svgBlob(poster.svg), `${name}.svg`)}>
            <Download size={16} /> SVG
          </button>
          <button className="ghost" disabled={!poster} onClick={() => poster && printPoster(poster)}>
            <Printer size={16} /> Print / PDF
          </button>
          <button disabled={!poster || busy !== null} onClick={() => void run('png', (png) => save(png, `${name}.png`))}>
            <Download size={16} /> {busy === 'png' ? 'Preparing…' : 'Download PNG'}
          </button>
        </div>
      </div>
    </div>
  )
}
