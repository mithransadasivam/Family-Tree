import type { CSSProperties } from 'react'
import type { Member } from './types'

/** Only absolute http(s) URLs are rendered - photo_url is user-supplied free text. */
export const photoSrc = (url: string) => (/^https?:\/\//i.test(url) ? url : null)

export const initials = (m: Pick<Member, 'first_name' | 'last_name'>) =>
  `${m.first_name[0] ?? ''}${m.last_name[0] ?? ''}`.toUpperCase() || '?'

// A stable hue per person, drawn from the brand's sage / gold / teal / clay / plum family.
const HUES = [152, 42, 188, 18, 285, 98, 215, 340]
export const hueFor = (id: number) => HUES[Math.abs(id) % HUES.length]

export const lifespan = (m: Pick<Member, 'birth_date' | 'death_date'>) => {
  const b = m.birth_date?.slice(0, 4)
  const d = m.death_date?.slice(0, 4)
  if (b && d) return `${b} – ${d}`
  if (b) return `b. ${b}`
  if (d) return `d. ${d}`
  return ''
}

export default function Avatar({ member, size = 40 }: { member: Member; size?: number }) {
  const src = photoSrc(member.photo_url)
  return src ? (
    <img
      className="avatar"
      src={src}
      width={size}
      height={size}
      alt=""
      referrerPolicy="no-referrer"
      style={{ width: size, height: size }}
    />
  ) : (
    <span
      className="avatar avatar-fallback"
      style={{ width: size, height: size, fontSize: size * 0.38, '--h': hueFor(member.id) } as CSSProperties}
    >
      {initials(member)}
    </span>
  )
}
