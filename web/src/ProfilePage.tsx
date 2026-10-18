import { useRef, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { BASE, ENDPOINTS } from './api'
import { photoSrc } from './Avatar'
import { toAvatarJpeg } from './avatarImage'
import { Arrow, Edit, Mail, Phone, Pin } from './Icons'
import { useAvatar, useMe, useTrees, useUpdateMe, type ProfileInput } from './queries'
import type { User } from './types'

const initialsOf = (u: Pick<User, 'first_name' | 'last_name' | 'email'>) =>
  `${u.first_name[0] ?? ''}${u.last_name[0] ?? ''}`.toUpperCase() || (u.email[0] ?? '?').toUpperCase()

/** Round account avatar: the uploaded picture, else the Google photo, else initials. */
export function AccountAvatar({ user, size = 28 }: { user: User; size?: number }) {
  const src = user.has_avatar
    ? `${BASE}${ENDPOINTS.avatar}?v=${encodeURIComponent(user.avatar_version ?? '')}`
    : photoSrc(user.photo_url ?? '')
  return src ? (
    <img className="avatar" src={src} width={size} height={size} alt="" referrerPolicy="no-referrer" style={{ width: size, height: size }} />
  ) : (
    <span
      className="avatar avatar-fallback"
      style={{ width: size, height: size, fontSize: size * 0.38, '--h': 152 } as CSSProperties}
    >
      {initialsOf(user)}
    </span>
  )
}

const Req = () => (
  <span className="req" aria-hidden>
    {' '}
    *
  </span>
)

function Row({ icon, label, value, note }: { icon: React.ReactNode; label: string; value?: string; note?: string }) {
  return (
    <div className="detail-row">
      <span className="detail-icon">{icon}</span>
      <div>
        <div className="detail-label">{label}</div>
        <div className={value ? '' : 'muted'}>{value || 'Not added yet'}</div>
        {note && <div className="muted small">{note}</div>}
      </div>
    </div>
  )
}

export default function ProfilePage() {
  const me = useMe()
  const trees = useTrees()
  const update = useUpdateMe()
  const [editing, setEditing] = useState(false)
  const [saved, setSaved] = useState(false)
  const avatar = useAvatar()
  const fileInput = useRef<HTMLInputElement>(null)
  const [photoError, setPhotoError] = useState<string | null>(null)
  const [f, setF] = useState<ProfileInput>({ first_name: '', last_name: '', phone: '', address: '' })

  if (me.isLoading) return <p className="status">Loading…</p>
  if (me.error || !me.data) {
    return (
      <p role="alert" className="status error">
        Could not load your profile: {me.error?.message ?? 'unknown error'}{' '}
        <button onClick={() => void me.refetch()}>Retry</button>
      </p>
    )
  }

  const u = me.data
  const owned = trees.data?.filter((t) => t.owner.id === u.id) ?? []
  const isOwner = owned.length > 0
  const since = u.created_at
    ? new Date(u.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })
    : null
  const fullName = `${u.first_name} ${u.last_name}`.trim() || u.email

  const startEdit = () => {
    setF({ first_name: u.first_name, last_name: u.last_name, phone: u.phone ?? '', address: u.address ?? '' })
    setSaved(false)
    setEditing(true)
  }
  const pickPhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // allow choosing the same file again
    if (!file) return
    setPhotoError(null)
    try {
      avatar.upload.mutate(await toAvatarJpeg(file), {
        onError: (err) => setPhotoError(err.message),
      })
    } catch (err) {
      setPhotoError(err instanceof Error ? err.message : 'Could not use that picture.')
    }
  }
  const busyPhoto = avatar.upload.isPending || avatar.remove.isPending
  const set = (k: keyof ProfileInput) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setF((p) => ({ ...p, [k]: e.target.value }))

  return (
    <main className="page narrow">
      <header className="page-head rise">
        <span className="eyebrow">Your account</span>
        <h1>
          My <em>profile</em>
        </h1>
      </header>

      <section className="card profile-hero rise" style={{ '--i': 1 } as CSSProperties}>
        <div className="avatar-halo">
          <AccountAvatar user={u} size={88} />
        </div>
        <div>
          <h2>{fullName}</h2>
          <div className="row wrap" style={{ marginTop: 8 }}>
            <span className={`badge ${isOwner ? '' : 'pending'}`}>{isOwner ? 'Owner' : 'Member'}</span>
            {since && <span className="muted small">Member since {since}</span>}
          </div>
          <div className="row wrap" style={{ marginTop: 12 }}>
            <input ref={fileInput} type="file" accept="image/*" hidden onChange={(e) => void pickPhoto(e)} />
            <button className="ghost" disabled={busyPhoto} onClick={() => fileInput.current?.click()}>
              <Edit size={15} /> {avatar.upload.isPending ? 'Uploading…' : u.has_avatar ? 'Change photo' : 'Add your own photo'}
            </button>
            {u.has_avatar && (
              <button
                className="ghost"
                disabled={busyPhoto}
                onClick={() => {
                  setPhotoError(null)
                  avatar.remove.mutate(undefined, { onError: (err) => setPhotoError(err.message) })
                }}
              >
                {u.photo_url ? 'Use my Google photo' : 'Remove photo'}
              </button>
            )}
          </div>
          {photoError && (
            <p role="alert" className="error" style={{ marginTop: 8 }}>
              {photoError}
            </p>
          )}
        </div>
      </section>

      <section className="card rise" style={{ '--i': 2 } as CSSProperties}>
        <div className="row between" style={{ marginBottom: 6 }}>
          <h3>Your details</h3>
          {!editing && (
            <button className="ghost" onClick={startEdit}>
              <Edit size={15} /> Edit
            </button>
          )}
        </div>

        {editing ? (
          <form
            className="stack"
            onSubmit={(e) => {
              e.preventDefault()
              update.mutate(
                { ...f, first_name: f.first_name.trim(), last_name: f.last_name.trim(), phone: f.phone.trim(), address: f.address.trim() },
                {
                  onSuccess: () => {
                    setEditing(false)
                    setSaved(true)
                  },
                },
              )
            }}
          >
            <div className="row">
              <label className="field grow">
                <span>
                  First name
                  <Req />
                </span>
                <input required autoFocus value={f.first_name} onChange={set('first_name')} />
              </label>
              <label className="field grow">
                <span>
                  Last name
                  <Req />
                </span>
                <input required value={f.last_name} onChange={set('last_name')} />
              </label>
            </div>
            <label className="field">
              Phone
              <input type="tel" maxLength={20} value={f.phone} onChange={set('phone')} />
            </label>
            <label className="field">
              Address
              <input value={f.address} onChange={set('address')} />
            </label>
            <p className="muted small">
              <Req />
              Required. Your email comes from your Google account.
            </p>
            {update.error && (
              <p role="alert" className="error">
                {update.error.message}
              </p>
            )}
            <div className="row end">
              <button type="button" className="ghost" onClick={() => setEditing(false)}>
                Cancel
              </button>
              <button disabled={update.isPending || !f.first_name.trim() || !f.last_name.trim()}>
                {update.isPending ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          </form>
        ) : (
          <>
            <Row icon={<Mail size={18} />} label="Email" value={u.email} note="From your Google account" />
            <Row icon={<Phone size={18} />} label="Phone" value={u.phone} />
            <Row icon={<Pin size={18} />} label="Address" value={u.address} />
            {saved && (
              <p role="status" style={{ marginTop: 12, color: 'var(--sage)' }}>
                Saved.
              </p>
            )}
          </>
        )}
      </section>

      <section className="card rise" style={{ '--i': 3 } as CSSProperties}>
        <h3>Your families</h3>
        {trees.data?.length === 0 && <p className="muted">You are not in any family yet.</p>}
        <ul className="plain">
          {trees.data?.map((t) => (
            <li key={t.id} className="request">
              <Link to={`/trees/${t.id}`} className="link-row">
                {t.tree_name} <Arrow size={14} />
              </Link>
              <span className={`badge ${t.owner.id === u.id ? '' : 'pending'}`}>{t.owner.id === u.id ? 'Owner' : 'Member'}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}
