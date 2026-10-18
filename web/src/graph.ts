import type { Member, Relationship } from './types'

// Relationship classification, based on the Android app (TreeViewScreen.kt).
// `relationship_type_name` describes what member_1 IS to member_2.
const SPOUSE = new Set(['Spouse', 'Husband', 'Wife', 'Partner', 'Fiance', 'Fiancee'])
const PARENT = new Set(['Father', 'Mother', 'Stepfather', 'Stepmother', 'Step Father', 'Step Mother'])
const CHILD = new Set([
  'Son', 'Daughter', 'Stepson', 'Stepdaughter', 'Step Son', 'Step Daughter',
  'Adopted Son', 'Adopted Daughter',
])
// Two generations apart. Drawn as a direct link only when the generation in between is
// not recorded, otherwise the grandchild would be placed twice (under the grandparent
// and under their real parent).
const GRANDPARENT = new Set(['Grandfather', 'Grandmother'])
const GRANDCHILD = new Set(['Grandson', 'Granddaughter'])

export const isSpouseType = (name: string) => SPOUSE.has(name)

export type Group =
  | 'Grandparents'
  | 'Parents'
  | 'Spouse'
  | 'Siblings'
  | 'Children'
  | 'Grandchildren'
  | 'In-laws'
  | 'Extended family'

export const GROUP_ORDER: Group[] = [
  'Grandparents',
  'Parents',
  'Spouse',
  'Siblings',
  'Children',
  'Grandchildren',
  'In-laws',
  'Extended family',
]

type Dir = { group: Group; inverse: Group; inverseLabel: string }
const FAMILY: Record<string, Dir> = {}
const def = (names: string[], group: Group, inverse: Group, inverseLabel: string) =>
  names.forEach((n) => (FAMILY[n] = { group, inverse, inverseLabel }))

// For a type T on (member_1 -> member_2): `group` is where member_1 sits from member_2's
// point of view, `inverse`/`inverseLabel` is where member_2 sits from member_1's.
def(['Father', 'Mother'], 'Parents', 'Children', 'Child')
def(['Step Father', 'Step Mother', 'Stepfather', 'Stepmother'], 'Parents', 'Children', 'Stepchild')
def(['Son', 'Daughter'], 'Children', 'Parents', 'Parent')
def(['Step Son', 'Step Daughter', 'Stepson', 'Stepdaughter'], 'Children', 'Parents', 'Step-parent')
def(['Adopted Son', 'Adopted Daughter'], 'Children', 'Parents', 'Adoptive parent')
def(['Grandfather', 'Grandmother'], 'Grandparents', 'Grandchildren', 'Grandchild')
def(['Grandson', 'Granddaughter'], 'Grandchildren', 'Grandparents', 'Grandparent')
def(['Brother', 'Sister'], 'Siblings', 'Siblings', 'Sibling')
def(['Step Brother', 'Step Sister'], 'Siblings', 'Siblings', 'Step-sibling')
def(['Adopted Brother', 'Adopted Sister'], 'Siblings', 'Siblings', 'Adopted sibling')
def(['Spouse', 'Husband', 'Wife', 'Partner', 'Fiance', 'Fiancee'], 'Spouse', 'Spouse', 'Partner')
def(['Father-in-Law', 'Mother-in-Law'], 'In-laws', 'In-laws', 'Child-in-law')
def(['Son-in-Law', 'Daughter-in-Law'], 'In-laws', 'In-laws', 'Parent-in-law')
def(['Brother-in-Law', 'Sister-in-Law'], 'In-laws', 'In-laws', 'Sibling-in-law')
def(['Uncle', 'Aunt'], 'Extended family', 'Extended family', 'Nephew / niece')
def(['Cousin'], 'Extended family', 'Extended family', 'Cousin')
def(['Guardian'], 'Extended family', 'Extended family', 'Ward')

/** What the other person in `rel` is to `selfId`, in the groups the detail panel shows. */
export function classify(rel: Relationship, selfId: number) {
  const name = rel.relationship_type_name
  const selfIsFirst = rel.member_1 === selfId
  const other = selfIsFirst ? rel.member_2 : rel.member_1
  const d = FAMILY[name]
  if (!d) {
    return { group: 'Extended family' as Group, other, label: selfIsFirst ? `${name} of` : name }
  }
  return selfIsFirst
    ? { group: d.inverse, other, label: d.inverseLabel }
    : { group: d.group, other, label: name }
}

export interface Graph {
  parents: Map<number, Set<number>>
  children: Map<number, Set<number>>
  spouses: Map<number, Set<number>>
  /** `${ancestor}>${descendant}` for links that skip a generation (grandparent -> grandchild). */
  skips: Set<string>
}

const add = (m: Map<number, Set<number>>, k: number, v: number) => {
  if (!m.has(k)) m.set(k, new Set())
  m.get(k)!.add(v)
}

export function buildGraph(rels: Relationship[]): Graph {
  const g: Graph = { parents: new Map(), children: new Map(), spouses: new Map(), skips: new Set() }
  const link = (parent: number, child: number) => {
    add(g.children, parent, child)
    add(g.parents, child, parent)
  }
  const skips: [number, number][] = [] // [grandparent, grandchild]
  for (const r of rels) {
    const name = r.relationship_type_name
    if (SPOUSE.has(name)) {
      add(g.spouses, r.member_1, r.member_2)
      add(g.spouses, r.member_2, r.member_1)
    } else if (PARENT.has(name)) {
      link(r.member_1, r.member_2)
    } else if (CHILD.has(name)) {
      link(r.member_2, r.member_1)
    } else if (GRANDPARENT.has(name)) {
      skips.push([r.member_1, r.member_2])
    } else if (GRANDCHILD.has(name)) {
      skips.push([r.member_2, r.member_1])
    }
    // Siblings, cousins, in-laws, etc. are derived from the above, not drawn as edges.
  }
  for (const [grandparent, grandchild] of skips) {
    const bridged = [...(g.children.get(grandparent) ?? [])].some((p) => g.children.get(p)?.has(grandchild))
    // Someone's spouse counts as bridging too: Gran -> (her son's wife) -> grandchild.
    const viaSpouse = [...(g.children.get(grandparent) ?? [])].some((p) =>
      [...(g.spouses.get(p) ?? [])].some((s) => g.children.get(s)?.has(grandchild)),
    )
    if (!bridged && !viaSpouse) {
      link(grandparent, grandchild)
      g.skips.add(`${grandparent}>${grandchild}`)
    }
  }
  return g
}

/** Members with no recorded parents - candidate roots for the tree view. */
export function findRoots(members: Member[], g: Graph): Member[] {
  const roots = members.filter((m) => !g.parents.has(m.id))
  // Show one of each spouse pair only.
  const seen = new Set<number>()
  return roots.filter((m) => {
    if (seen.has(m.id)) return false
    seen.add(m.id)
    g.spouses.get(m.id)?.forEach((s) => seen.add(s))
    return true
  })
}

/**
 * A family unit: a person plus their spouse(s), drawn side by side, with the children they
 * share (or that either of them has) hanging below. `people[0]` is the person the unit was
 * reached through - the child of the unit above - so that is where the parent link lands.
 */
export interface Unit {
  id: number
  people: Member[]
  children: Unit[]
  /** Reached by a grandparent link: drawn two rows below its parent unit, not one. */
  skip: boolean
  /**
   * Children of this unit who are already drawn elsewhere (typically a married-in spouse,
   * shown beside their partner). They get a link from this unit rather than a second card.
   */
  refs: number[]
}

const byBirth = (a: Member, b: Member) =>
  (a.birth_date ?? '9999').localeCompare(b.birth_date ?? '9999') || a.id - b.id

/**
 * Turn the whole family graph into a forest of unit trees. `mainId` is drawn first (leftmost);
 * every other family line follows, so an in-law's parents are never dropped. Each person gets
 * exactly one card; a child who already has one is recorded in `refs` and linked instead.
 */
export function buildForest(mainId: number | null, members: Map<number, Member>, g: Graph): Unit[] {
  const visited = new Set<number>()
  const build = (id: number): Unit | null => {
    const m = members.get(id)
    if (!m || visited.has(id)) return null
    visited.add(id)
    const spouses = [...(g.spouses.get(id) ?? [])]
      .filter((s) => members.has(s) && !visited.has(s))
      .map((s) => members.get(s)!)
    spouses.forEach((s) => visited.add(s.id))
    const people = [m, ...spouses]
    const kidIds = new Set<number>()
    people.forEach((p) => g.children.get(p.id)?.forEach((c) => kidIds.add(c)))
    const marriedIntoFamily = (childId: number) =>
      [...(g.spouses.get(childId) ?? [])].some((sp) => members.has(sp) && !visited.has(sp) && g.parents.has(sp))
    const refs: number[] = []
    const children: Unit[] = []
    ;[...kidIds]
      .map((c) => members.get(c))
      .filter((c): c is Member => !!c)
      // Birth order, except a child who married into a family with known parents goes last:
      // that spouse's parents are drawn off to the right, so this keeps their link from
      // crossing the other siblings' lines.
      .sort((a, b) => Number(marriedIntoFamily(a.id)) - Number(marriedIntoFamily(b.id)) || byBirth(a, b))
      .forEach((c) => {
        if (visited.has(c.id)) {
          refs.push(c.id)
          return
        }
        const unit = build(c.id)
        if (unit) {
          // A direct (non-skip) parent link means the child belongs on the next row.
          unit.skip = !people.some(
            (p) => g.children.get(p.id)?.has(c.id) && !g.skips.has(`${p.id}>${c.id}`),
          )
          children.push(unit)
        }
      })
    return { id, people, children, skip: false, refs }
  }

  const forest: Unit[] = []
  const add = (id: number) => {
    const u = build(id)
    if (u) forest.push(u)
  }
  if (mainId !== null) add(mainId)
  // Remaining family lines: the oldest known generation first, then anyone not yet reached.
  const rest = [...members.values()].sort(byBirth)
  rest.filter((m) => !g.parents.has(m.id)).forEach((m) => add(m.id))
  rest.forEach((m) => add(m.id))
  return forest
}

/** Number of generations (rows) in a unit tree. */
export function depthOf(u: Unit | null): number {
  return u ? Math.max(1, ...u.children.map((c) => (c.skip ? 2 : 1) + depthOf(c))) : 0
}

/** Number of people drawn in a unit tree. */
export function countPeople(u: Unit): number {
  return u.people.length + u.children.reduce((n, c) => n + countPeople(c), 0)
}

/**
 * True if anyone is recorded as this person's child or grandchild. Such a person is a "root"
 * of the family and cannot be deleted (the server enforces the same rule).
 */
export function hasDescendants(personId: number, rels: Relationship[]): boolean {
  return rels.some((r) => {
    const t = r.relationship_type_name
    if (r.member_1 === personId && (PARENT.has(t) || GRANDPARENT.has(t))) return true
    if (r.member_2 === personId && (CHILD.has(t) || GRANDCHILD.has(t))) return true
    return false
  })
}
