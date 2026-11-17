import { Eye, EyeOff } from './Icons'

/** The eye button next to a private detail: open eye = others can see it, slashed eye = hidden. */
export default function EyeToggle({
  on,
  onChange,
  label,
  disabled,
}: {
  on: boolean
  onChange: (on: boolean) => void
  /** What the detail is, e.g. "phone number". */
  label: string
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      className={`eye-btn${on ? ' on' : ''}`}
      aria-pressed={on}
      disabled={disabled}
      title={on ? `Your ${label} is visible to others. Click to hide it.` : `Your ${label} is hidden. Click to show it.`}
      aria-label={on ? `Hide ${label} from others` : `Show ${label} to others`}
      onClick={() => onChange(!on)}
    >
      {on ? <Eye size={18} /> : <EyeOff size={18} />}
    </button>
  )
}
