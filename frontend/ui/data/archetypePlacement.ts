/**
 * TEMPORARY SCAFFOLDING -- design round-1 item 2, the player profile
 * (`docs/design/PLAYER-PROFILE.md` §4, `docs/founder-requests/FR-075-*.md`,
 * `docs/handoffs/117-prepared-answers-to-the-2026-08-01-handoff-held.md`
 * "Prepared answer 1", `docs/handoffs/121-archetype-placement-built-both-ways-behind-a-fla.md`).
 *
 * The founder asked, in his own words, for the archetype chip "towards the top
 * of the card ... next to the name[s] ... before position." Design's round-1
 * handoff proposes moving it out of the identity strip into the disclosed
 * section instead, on a real argument (a status can invalidate a pick; an
 * archetype only comments on one you remain free to make). The PM agrees with
 * design on the merits but correctly held that reversing a direct founder
 * instruction is not a call to make silently -- see thread 117. **The founder
 * has not ruled yet and has asked to see both before he does.** So this file
 * exists to let both render from the same build, for screenshots, without
 * picking a winner in code.
 *
 * - `'identity-strip'` (Arrangement A): the chip renders beside the name in
 *   every state -- a real label or one of the three honest absences -- exactly
 *   as FR-075 was originally built. This is the DEFAULT: if this flag is never
 *   touched, the shipped behaviour is the one the founder actually asked for.
 * - `'disclosed'` (Arrangement B): the chip renders beside the name only for a
 *   real label. Every absence state is one item shorter in the strip and
 *   instead gets its full, visually distinct treatment in the disclosed
 *   ARCHETYPE section (see `PlayerDetail.tsx`).
 *
 * Flip it for a screenshot without a rebuild: `?archetypePlacement=disclosed`
 * on the URL, or `localStorage.setItem('prep.archetypePlacement', 'disclosed')`
 * in devtools / a Playwright `page.addInitScript`. Both fall back to the
 * default below when unset or unrecognised. The URL param wins so a single
 * screenshot script can drive both arrangements by URL alone.
 *
 * **This whole file is scaffolding, not a permanent setting.** Once the
 * founder rules (thread 121), delete the losing arrangement's branch in
 * `PlayerDetail.tsx` and this file along with it -- do not let it calcify
 * into a real user-facing preference nobody asked for.
 */

export type ArchetypePlacement = 'identity-strip' | 'disclosed';

/** The founder's standing instruction (FR-075). Do not change this default
 *  without an explicit founder ruling recorded in thread 121. */
export const DEFAULT_ARCHETYPE_PLACEMENT: ArchetypePlacement = 'identity-strip';

const STORAGE_KEY = 'prep.archetypePlacement';

function isValidPlacement(v: string | null): v is ArchetypePlacement {
  return v === 'identity-strip' || v === 'disclosed';
}

/** Resolved once per render call rather than cached in a context -- this is
 *  screenshot scaffolding, not a live user preference with its own toggle UI,
 *  so there is no persisted-state React tree to keep in sync. */
export function currentArchetypePlacement(): ArchetypePlacement {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('archetypePlacement');
    if (isValidPlacement(fromUrl)) return fromUrl;
  } catch {
    // No window (SSR / some test environments) -- fall through to storage/default.
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isValidPlacement(stored)) return stored;
  } catch {
    // Storage unavailable -- fall through to default.
  }
  return DEFAULT_ARCHETYPE_PLACEMENT;
}
