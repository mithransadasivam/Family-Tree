/**
 * Permission model: every tree member can add and edit people and relationships, but only the
 * tree owner can delete them (the backend enforces it; this only keeps the UI honest).
 *
 * Anything still loading counts as "not the owner", so delete actions never flash up for a member.
 */
export function isTreeOwner(
  tree: { owner: { id: number } } | undefined,
  me: { id: number } | undefined,
): boolean {
  return !!tree && !!me && tree.owner.id === me.id
}
