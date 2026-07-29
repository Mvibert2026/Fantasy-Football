/**
 * FR-036: manually-typed opponent team names, local and per-league.
 *
 * Same storage shape/lifecycle as `prep.draft.<leagueId>` (ui/data/draft.ts) and
 * `prep.draftSlot.<leagueId>` (ui/data/draftSlot.ts) -- a sibling key per league, so
 * switching leagues never carries one league's typed names into another's, and a name
 * survives a reload.
 *
 * Names only, by construction: this module has no dependency on the availability
 * model, the recommendation, or opponent-strategy inference, and nothing here is wired
 * into any of them. A typed name is display text for a slot, nothing else -- see
 * ui/views/Opponents.tsx's own module doc for the fuller rule this follows (the
 * Opponents screen is observable arithmetic derived from the pick log, never a model
 * input).
 */

export type OpponentNameMap = Record<number, string>;

function storageKey(leagueId: string): string {
  return `prep.opponentNames.${leagueId}`;
}

export function loadOpponentNames(leagueId: string): OpponentNameMap {
  try {
    const raw = localStorage.getItem(storageKey(leagueId));
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (typeof parsed !== 'object' || parsed === null) return {};
    const out: OpponentNameMap = {};
    for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
      const slot = Number(k);
      if (Number.isInteger(slot) && slot > 0 && typeof v === 'string' && v.trim() !== '') {
        out[slot] = v;
      }
    }
    return out;
  } catch {
    return {};
  }
}

function persist(leagueId: string, names: OpponentNameMap): void {
  try {
    localStorage.setItem(storageKey(leagueId), JSON.stringify(names));
  } catch {
    // Persistence is a nicety; a failed write just means the names reset next load.
  }
}

/** Trims and rejects empty/whitespace-only input -- an empty typed name isn't a real
 *  override, it's a way to accidentally re-hide a sourced name behind nothing, so it's
 *  treated the same as `clearOpponentName`. */
export function saveOpponentName(leagueId: string, slot: number, name: string): OpponentNameMap {
  const current = loadOpponentNames(leagueId);
  const trimmed = name.trim();
  const next = trimmed === '' ? removeSlot(current, slot) : { ...current, [slot]: trimmed };
  persist(leagueId, next);
  return next;
}

/** Falls back to the sourced name (opponents.json's own team_name) if one exists --
 *  never to blank. There is nothing to fall back to *here*; the caller re-reads
 *  opponents.json's value once the typed override is removed, per FR-036's explicit
 *  "clearing falls back to sourced, not blank" rule. */
export function clearOpponentName(leagueId: string, slot: number): OpponentNameMap {
  const next = removeSlot(loadOpponentNames(leagueId), slot);
  persist(leagueId, next);
  return next;
}

function removeSlot(names: OpponentNameMap, slot: number): OpponentNameMap {
  if (!(slot in names)) return names;
  const next = { ...names };
  delete next[slot];
  return next;
}
