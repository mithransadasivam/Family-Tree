export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden className="logo-mark">
      <circle cx="16" cy="16" r="12.5" stroke="var(--gold)" strokeWidth="1.4" opacity=".95" />
      <circle cx="16" cy="16" r="8" stroke="var(--sage)" strokeWidth="1" opacity=".55" />
      <path
        d="M16 23V15.5M16 15.5 11.5 10M16 15.5 20.5 10"
        stroke="var(--gold)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="11.5" cy="9.5" r="1.7" fill="var(--sage)" />
      <circle cx="20.5" cy="9.5" r="1.7" fill="var(--sage)" />
    </svg>
  )
}

export default function Logo() {
  return (
    <span className="logo">
      <LogoMark />
      <span className="logo-word">Kinship</span>
    </span>
  )
}
