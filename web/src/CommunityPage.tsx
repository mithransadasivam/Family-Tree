import { useEffect, useState, type CSSProperties } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  useCommunity,
  useCommunityActions,
  useCommunityMembers,
  useCommunityPeople,
  useCommunityRequests,
  useHandleCommunityRequest,
  useShareTree,
} from './communityQueries'
import { Back, Mars, Phone, Search, Venus } from './Icons'

type GenderFilter = '' | 'male' | 'female'
type Living = '' | 'yes' | 'no'

const PAGE = 50

function useDebounced<T>(value: T, ms = 300): T {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

function People({ id, hasFamilies }: { id: number; hasFamilies: boolean }) {
  const [name, setName] = useState('')
  const [gender, setGender] = useState<GenderFilter>('')
  const [ageMin, setAgeMin] = useState('')
  const [ageMax, setAgeMax] = useState('')
  const [living, setLiving] = useState<Living>('')
  const [limit, setLimit] = useState(PAGE)

  const dName = useDebounced(name.trim())
  const dMin = useDebounced(ageMin.trim())
  const dMax = useDebounced(ageMax.trim())
  const params = new URLSearchParams()
  if (dName) params.set('q', dName)
  if (gender) params.set('gender', gender)
  if (dMin) params.set('age_min', dMin)
  if (dMax) params.set('age_max', dMax)
  if (living) params.set('living', living)
  params.set('limit', String(limit))
  const people = useCommunityPeople(id, params.toString())

  const filtered = Boolean(dName || gender || dMin || dMax || living)
  const clear = () => {
    setName('')
    setGender('')
    setAgeMin('')
    setAgeMax('')
    setLiving('')
    setLimit(PAGE)
  }
  // Any change to a filter starts the list from the top again.
  const change = <T,>(set: (v: T) => void) => (v: T) => {
    set(v)
    setLimit(PAGE)
  }

  return (
    <section className="card rise" style={{ '--i': 1 } as CSSProperties}>
      <h3>People in this community</h3>
      <div className="stack">
        <label className="field">
          <span className="sr-only">Name</span>
          <div className="row">
            <Search size={16} />
            <input
              className="grow"
              placeholder="Search by name"
              value={name}
              onChange={(e) => change(setName)(e.target.value)}
            />
          </div>
        </label>
        <div className="row wrap" style={{ alignItems: 'flex-end', gap: 16 }}>
          <div className="field">
            Gender
            <div className="seg" role="group" aria-label="Gender">
              {(
                [
                  ['', 'Anyone'],
                  ['male', 'Men'],
                  ['female', 'Women'],
                ] as const
              ).map(([v, label]) => (
                <button
                  key={v}
                  type="button"
                  className={gender === v ? 'on' : ''}
                  aria-pressed={gender === v}
                  onClick={() => change(setGender)(v)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="field">
            Age
            <div className="row">
              <input
                className="age-input"
                inputMode="numeric"
                placeholder="From"
                aria-label="Minimum age"
                value={ageMin}
                onChange={(e) => change(setAgeMin)(e.target.value.replace(/\D/g, '').slice(0, 3))}
              />
              <span className="muted">to</span>
              <input
                className="age-input"
                inputMode="numeric"
                placeholder="To"
                aria-label="Maximum age"
                value={ageMax}
                onChange={(e) => change(setAgeMax)(e.target.value.replace(/\D/g, '').slice(0, 3))}
              />
            </div>
          </div>
          <div className="field">
            Status
            <div className="seg" role="group" aria-label="Living or deceased">
              {(
                [
                  ['', 'All'],
                  ['yes', 'Living'],
                  ['no', 'Deceased'],
                ] as const
              ).map(([v, label]) => (
                <button
                  key={v}
                  type="button"
                  className={living === v ? 'on' : ''}
                  aria-pressed={living === v}
                  onClick={() => change(setLiving)(v)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          {filtered && (
            <button className="ghost" onClick={clear}>
              Clear filters
            </button>
          )}
        </div>
        <p className="muted small">
          To search by one age, put the same number in both boxes. Age filters only include living people with a birth
          date.
        </p>
      </div>

      {people.error && (
        <p role="alert" className="error">
          {people.error.message}
        </p>
      )}
      {people.data && (
        <p className="muted small" role="status" style={{ marginTop: 14 }}>
          {people.data.count} {people.data.count === 1 ? 'person' : 'people'}
          {filtered ? ' match' : ''}
        </p>
      )}
      <ul className="plain people-list">
        {people.data?.results.map((p) => (
          <li key={p.id} className="request person-row">
            <div>
              <strong>
                {p.first_name} {p.last_name}
              </strong>
              {p.gender === 'male' && <Mars size={14} className="gender-inline" aria-label="Male" />}
              {p.gender === 'female' && <Venus size={14} className="gender-inline" aria-label="Female" />}
              <div className="muted small">
                {p.deceased ? 'Deceased' : p.age !== null ? `${p.age} years old` : 'Age not recorded'}
              </div>
            </div>
            {p.phone && (
              <a className="phone-link" href={`tel:${p.phone.replace(/[^\d+]/g, '')}`}>
                <Phone size={14} /> {p.phone}
              </a>
            )}
          </li>
        ))}
      </ul>
      {people.data && people.data.count === 0 && (
        <p className="muted">
          {filtered
            ? 'Nobody matches those filters.'
            : hasFamilies
              ? 'No people yet.'
              : 'No families have been shared here yet. Share one of yours below to get started.'}
        </p>
      )}
      {people.data && people.data.count > limit && (
        <div className="row end">
          <button className="ghost" onClick={() => setLimit((l) => l + PAGE)}>
            Show more
          </button>
        </div>
      )}
    </section>
  )
}

export default function CommunityPage() {
  const id = Number(useParams().communityId)
  const nav = useNavigate()
  const c = useCommunity(id)
  const isOwner = c.data?.role === 'owner'
  const requests = useCommunityRequests(id, isOwner)
  const members = useCommunityMembers(id, isOwner)
  const handle = useHandleCommunityRequest(id)
  const { share, unshare } = useShareTree(id)
  const actions = useCommunityActions(id)

  if (c.isLoading) return <p className="status">Loading…</p>
  if (c.error || !c.data) {
    return (
      <p role="alert" className="status error">
        Could not open this community: {c.error?.message ?? 'unknown error'}{' '}
        <Link to="/communities">Back to communities</Link>
      </p>
    )
  }
  const d = c.data

  return (
    <main className="page narrow">
      <header className="page-head rise">
        <Link to="/communities" className="link-row muted">
          <Back size={14} /> All communities
        </Link>
        <h1 style={{ marginTop: 14 }}>{d.name}</h1>
        {d.description && <p className="muted">{d.description}</p>}
        <div className="row wrap" style={{ marginTop: 10 }}>
          <span className={`badge ${isOwner ? '' : 'pending'}`}>{isOwner ? 'Owner' : 'Member'}</span>
          <span className="muted small">
            {d.member_count} {d.member_count === 1 ? 'member' : 'members'} · {d.tree_count}{' '}
            {d.tree_count === 1 ? 'family' : 'families'} shared
          </span>
        </div>
      </header>

      <People id={id} hasFamilies={d.tree_count > 0} />

      <section className="card rise" style={{ '--i': 2 } as CSSProperties}>
        <h3>Your families here</h3>
        <p className="muted small">
          Sharing a family lets members of this community find the people in it: name, gender, age and any public phone
          number. Photos, addresses, emails, private numbers and the family tree itself are never shown. You can stop
          sharing at any time.
        </p>
        {d.my_trees.length === 0 && <p className="muted">You do not own a family yet. Create one from the families page.</p>}
        <ul className="plain">
          {d.my_trees.map((t) => (
            <li key={t.id} className="request">
              <span>{t.tree_name}</span>
              {t.shared ? (
                <button className="ghost" disabled={unshare.isPending} onClick={() => unshare.mutate(t.id)}>
                  Stop sharing
                </button>
              ) : (
                <button disabled={share.isPending} onClick={() => share.mutate(t.id)}>
                  Share
                </button>
              )}
            </li>
          ))}
        </ul>
        {(share.error || unshare.error) && (
          <p role="alert" className="error">
            {(share.error ?? unshare.error)?.message}
          </p>
        )}
      </section>

      {isOwner && (
        <>
          <section className="card rise" style={{ '--i': 3 } as CSSProperties}>
            <h3>Join requests</h3>
            {requests.data?.length === 0 && <p className="muted">No one is waiting.</p>}
            <ul className="plain">
              {requests.data?.map((r) => (
                <li key={r.id} className="request">
                  <div>
                    <strong>{r.name}</strong>
                    <div className="muted small">{r.email}</div>
                  </div>
                  <div className="row">
                    <button
                      className="ghost"
                      disabled={handle.isPending}
                      onClick={() => handle.mutate({ id: r.id, status: 'rejected' })}
                    >
                      Decline
                    </button>
                    <button disabled={handle.isPending} onClick={() => handle.mutate({ id: r.id, status: 'approved' })}>
                      Approve
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            {handle.error && (
              <p role="alert" className="error">
                {handle.error.message}
              </p>
            )}
          </section>

          <section className="card rise" style={{ '--i': 4 } as CSSProperties}>
            <h3>Members</h3>
            <ul className="plain">
              {members.data?.map((m) => (
                <li key={m.user_id} className="request">
                  <div>
                    <strong>{m.name}</strong>
                    <div className="muted small">{m.email}</div>
                  </div>
                  {m.role === 'owner' ? (
                    <span className="badge">Owner</span>
                  ) : (
                    <button
                      className="ghost"
                      disabled={actions.removeMember.isPending}
                      onClick={() => {
                        if (window.confirm(`Remove ${m.name}? Their shared families will stop being shared here.`))
                          actions.removeMember.mutate(m.user_id)
                      }}
                    >
                      Remove
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </section>
        </>
      )}

      <section className="card danger-zone rise" style={{ '--i': 5 } as CSSProperties}>
        {isOwner ? (
          <>
            <h3>Delete this community</h3>
            <p className="muted small">
              This removes the community for everyone. Family trees and the people in them are not deleted.
            </p>
            <div className="row end">
              <button
                className="danger"
                disabled={actions.remove.isPending}
                onClick={() => {
                  if (window.confirm(`Delete "${d.name}" for everyone?`))
                    actions.remove.mutate(undefined, { onSuccess: () => nav('/communities') })
                }}
              >
                Delete community
              </button>
            </div>
          </>
        ) : (
          <>
            <h3>Leave this community</h3>
            <p className="muted small">Your shared families will stop being shared here.</p>
            <div className="row end">
              <button
                className="danger"
                disabled={actions.leave.isPending}
                onClick={() => {
                  if (window.confirm(`Leave "${d.name}"?`)) actions.leave.mutate(undefined, { onSuccess: () => nav('/communities') })
                }}
              >
                Leave community
              </button>
            </div>
          </>
        )}
        {(actions.remove.error || actions.leave.error || actions.removeMember.error) && (
          <p role="alert" className="error">
            {(actions.remove.error ?? actions.leave.error ?? actions.removeMember.error)?.message}
          </p>
        )}
      </section>
    </main>
  )
}
