/**
 * Draft-slot override: FR-034. The user's draft position (`league.json:user_draft_slot`)
 * is a config value written once when a league export was built. For a second/third
 * league it is often an acknowledged placeholder (see docs/CURRENT-STATE.md's league-2
 * paragraph: "user_draft_slot=1 is an unresolved placeholder"), and even for the primary
 * league the founder wants to rehearse prep from a slot he doesn't actually hold.
 *
 * This is local, per-league, cosmetic-to-the-export state -- same shape and lifecycle as
 * `prep.draft.<leagueId>` in ui/data/draft.ts (a sibling key, not a field inside that
 * object, so clearing draft picks never touches the slot choice and vice versa). It is
 * NOT written back to league.json and never will be; the override lives only in the
 * browser that set it.
 *
 * Per Principle #1/#2: an override does not trace to a backend field, so it must never be
 * presented as if it were `league.json:user_draft_slot` itself. `ui/data/league.ts`'s
 * `applyUserSlotOverride` keeps the original (`userSlotSourced`) and the effective value
 * (`userSlot`, what every downstream computation reads) as two separate Cells precisely so
 * a screen can show both and mark which is which -- the same supplied-vs-derived rule
 * FR-036's typed opponent names follow.
 */

function storageKey(leagueId: string): string {
  return `prep.draftSlot.${leagueId}`;
}

/** `null` means "no override stored" -- fall back to league.json:user_draft_slot. Never 0
 *  (slots are 1-indexed; 0 would be an invented invalid slot, not an honest absence). */
export function loadSlotOverride(leagueId: string): number | null {
  try {
    const raw = localStorage.getItem(storageKey(leagueId));
    if (raw === null) return null;
    const n = Number(raw);
    return Number.isInteger(n) && n > 0 ? n : null;
  } catch {
    return null;
  }
}

export function saveSlotOverride(leagueId: string, slot: number): void {
  try {
    localStorage.setItem(storageKey(leagueId), String(slot));
  } catch {
    // Persistence is a nicety; a failed write just means the override resets next load.
  }
}

/** Falls back to the sourced slot, per FR-034's explicit requirement -- clearing an
 *  override is a return to the real config value, not a blank/unset state. There is
 *  nothing to write here beyond removing the key; `loadSlotOverride` already treats a
 *  missing key as "no override". */
export function clearSlotOverride(leagueId: string): void {
  try {
    localStorage.removeItem(storageKey(leagueId));
  } catch {
    // Same as above.
  }
}

/** A uniformly-random valid slot in [1, teams]. Only ever called from a UI action (the
 *  "randomise" button) -- never used to silently invent a value when one is missing. */
export function randomSlot(teams: number): number {
  return 1 + Math.floor(Math.random() * teams);
}
