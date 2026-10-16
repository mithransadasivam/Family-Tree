import { useEffect, useState } from 'react'
import { Close } from './Icons'

export interface Undoable {
  /** Changes when a new action replaces the previous one, restarting the timer. */
  key: number
  message: string
  /** Puts things back. Throw to show an error instead of closing the bar. */
  run: () => Promise<void>
}

const SECONDS = 10

/** "Deleted X · Undo" bar. The countdown pauses while the pointer or focus is on it. */
export default function UndoBar({ undo, onDone }: { undo: Undoable; onDone: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    setBusy(true)
    setError(null)
    try {
      await undo.run()
      onDone()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not undo')
      setBusy(false)
    }
  }

  // Ctrl/Cmd+Z while the bar is up, unless the user is typing somewhere.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null
      const typing = !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !typing && !busy) {
        e.preventDefault()
        void run()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [undo, busy])

  return (
    <div className="undo-bar" role="status" aria-live="polite">
      <div className="undo-row">
        <span className="undo-msg">{error ?? undo.message}</span>
        {!error && (
          <button className="undo-btn" onClick={() => void run()} disabled={busy}>
            {busy ? 'Restoring…' : 'Undo'}
          </button>
        )}
        <button className="ghost icon-btn mini" onClick={onDone} aria-label="Dismiss">
          <Close size={14} />
        </button>
      </div>
      {!error && !busy && (
        // key restarts the countdown for each new action; finishing the animation dismisses the bar.
        <div key={undo.key} className="undo-timer" style={{ animationDuration: `${SECONDS}s` }} onAnimationEnd={onDone} />
      )}
    </div>
  )
}
