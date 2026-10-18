import { useState } from 'react'
import { CATEGORIES, TERMS } from './relationshipTerms'
import type { RelationshipType } from './types'

// English only for now. relationshipTerms.ts also holds Hindi, Tamil, Telugu, Malayalam and
// Punjabi terms (ported from the Android app) if a language switcher is wanted later.
const TERM_LIST = TERMS.english

/**
 * Relationship picker state: one term (Father, Grandson, ...) resolved to the backend's
 * relationship type id. Pass `initialType` (a type name) to pre-select it when editing.
 */
export function useTermPicker(
  types: RelationshipType[] | undefined,
  initialType?: string,
  /** Hide terms that cannot apply (e.g. "Mother" for a man). */
  allow?: (englishType: string) => boolean,
) {
  const [termKey, setTermKey] = useState(() => {
    if (!initialType) return ''
    const i = TERM_LIST.findIndex((t) => t.englishType === initialType)
    return i >= 0 ? String(i) : ''
  })

  const typeByName = new Map((types ?? []).map((t) => [t.type_name, t.id]))
  const groups = CATEGORIES.map((c) => ({
    ...c,
    terms: TERM_LIST.map((t, i) => ({ ...t, key: String(i) })).filter(
      (t) => t.category === c.id && typeByName.has(t.englishType) && (allow?.(t.englishType) ?? true),
    ),
  })).filter((c) => c.terms.length > 0)
  const picked = termKey === '' ? undefined : TERM_LIST[Number(termKey)]
  // A choice that is no longer allowed (the gender changed) counts as not chosen.
  const chosen = picked && (allow?.(picked.englishType) ?? true) ? picked : undefined
  const typeId = chosen ? typeByName.get(chosen.englishType) : undefined

  const picker = (
    <select value={chosen ? termKey : ''} onChange={(e) => setTermKey(e.target.value)} aria-label="Relationship type">
      <option value="">Choose a relationship…</option>
      {groups.map((c) => (
        <optgroup key={c.id} label={c.label}>
          {c.terms.map((t) => (
            <option key={t.key} value={t.key}>
              {t.label}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  )

  return { typeId, picker, reset: () => setTermKey('') }
}
