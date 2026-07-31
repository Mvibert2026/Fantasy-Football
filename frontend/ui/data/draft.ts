/**
 * Draft mode: client-side draft state and the snake-order math it runs on.
 *
 * No backend call per pick -- this project is static-JSON, offline-first by
 * design (see CLAUDE.md and every other view in this app), and a live draft is
 * exactly when the network is least reliable. Picks and the queue persist to
 * localStorage, keyed per league (matching the multi-league work: draft state for
 * one league has no business leaking into another's).
 *
 * Queue vs. watchlist, per FRONTEND-SPEC.md §6.10 -- two distinct objects, not
 * one renamed:
 *   - Queue (`DraftState.queue`, here) is draft-scoped and self-pruning: a
 *     queued player drops out the instant anyone drafts him (see `recordPick`'s
 *     caller in DraftRoom.tsx), and the whole list resets with the draft.
 *   - Watchlist (`ui/data/watchlist.ts`) is account-wide, persists across
 *     seasons and leagues, and never disappears on its own.
 *
 * Team-at-pick is derived, never stored, from the same snake formula
 * ui/views/RoundGrid.tsx already uses in the forward direction (round, slot) ->
 * pick; this is its inverse, pick -> (round, slot).
 */

/**
 * RETROFIT-5 (design_handoff_draft_assistant/screens/01-draft-board.md): how the
 * pick was committed, so shortcut-entered picks can be examined for
 * systematically different behaviour rather than argued about.
 *
 * This is a deliberately smaller, three-value set scoped to this screen only --
 * NOT the same field as `mock_picks.entry_mode` in ADR-D
 * (docs/adr-drafts/ADR-D-mock-logging-instrumentation.md), which is a closed
 * eight-value enum with its own contamination-control machinery
 * (`shortlist_source`, `predictions_visible`, write-once hazard-model fields,
 * a blind-arm design) for Mock Lab's calibration-logging pipeline specifically.
 * That ADR is Status: Proposed and scoped to `mock_picks`/`mock_drafts`; it does
 * not name this screen. If this screen's exported log is ever wired into
 * calibration (`toDraftLog` below already documents itself as matching the
 * backend's mock-logging schema "field-for-field"), the two entry_mode
 * vocabularies will need to be reconciled deliberately, not silently -- flagged
 * in the thread reply for this retrofit rather than resolved here.
 *
 *   - 'shortcut' -- committed a displayed candidate without typing: a digit
 *     key, Enter on the un-typed default shortlist, or a click on a candidate
 *     row, a board-list row's mark-taken control, the recommended-pick button,
 *     or the player-detail sheet's mark-taken button.
 *   - 'typed'    -- the query field held text the user typed, then committed
 *     (a filtered match or the no-match free-text fallback).
 *   - 'pasted'   -- same as 'typed', but the query's content arrived via a
 *     paste event rather than keystrokes.
 */
export type EntryMode = 'shortcut' | 'typed' | 'pasted';

export interface DraftPickRecord {
  overallPick: number;
  round: number;
  /** 1-indexed, matching league.json:user_draft_slot's own convention. */
  teamSlot: number;
  /** board.json player id, when the entry matched a real board row. */
  playerId: number | null;
  /** The name as typed or selected -- always present, even for an off-board
   *  player (kicker, DST, a rookie not on this board) entered by free text. */
  playerName: string;
  timestamp: string;
  /** Optional (not `entryMode: EntryMode | null`) so a pick literal written
   *  before RETROFIT-5 -- an old test, an old localStorage record -- still
   *  type-checks; every read path normalises the missing case to an explicit
   *  `null` via `?? null`, never a fabricated 'shortcut' (Principle #2: an
   *  explicit null is a real state, distinct from any of the three real
   *  modes). Every pick `recordPick` writes going forward sets a real value. */
  entryMode?: EntryMode | null;
}

export interface DraftState {
  leagueId: string;
  /** Identifies one draft session for the exported log -- stable across picks,
   *  regenerated on reset. Not a claim about any backend record; the backend
   *  assigns its own identity to an imported log. */
  mockId: string;
  picks: DraftPickRecord[];
  /** Draft-scoped, self-pruning -- board.json player ids. See the module doc. */
  queue: number[];
}

function storageKey(leagueId: string): string {
  return `prep.draft.${leagueId}`;
}

function newMockId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return `mock-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function emptyState(leagueId: string): DraftState {
  return { leagueId, mockId: newMockId(), picks: [], queue: [] };
}

export function loadDraftState(leagueId: string): DraftState {
  try {
    const raw = localStorage.getItem(storageKey(leagueId));
    if (!raw) return emptyState(leagueId);
    const parsed = JSON.parse(raw) as Partial<DraftState>;
    if (parsed.leagueId !== leagueId) return emptyState(leagueId);
    // `queue` and (the now-retired) `watchlist` field: tolerate an older
    // record written before this field existed, rather than discarding real
    // picks just because the shape grew a field.
    return {
      leagueId,
      mockId: parsed.mockId ?? newMockId(),
      // entryMode didn't exist before RETROFIT-5 -- an old stored pick has no
      // honest value to backfill, so it stays `null` rather than being guessed
      // as 'shortcut'.
      picks: (parsed.picks ?? []).map((p) => ({ ...p, entryMode: p.entryMode ?? null })),
      queue: parsed.queue ?? [],
    };
  } catch {
    return emptyState(leagueId);
  }
}

/** A queued player drops out the instant anyone drafts him -- self-pruning, no
 *  dead-pick state to clear. Call after appending a new pick. */
export function pruneQueue(queue: number[], justDraftedId: number | null): number[] {
  if (justDraftedId === null) return queue;
  return queue.filter((id) => id !== justDraftedId);
}

export function saveDraftState(state: DraftState): void {
  try {
    localStorage.setItem(storageKey(state.leagueId), JSON.stringify(state));
  } catch {
    // Persistence is a nicety; a failed write just means state resets next load.
  }
}

/** ceil(pick / teams) -- round 1 is picks 1..teams, round 2 is teams+1..2*teams, etc. */
export function roundOfPick(overallPick: number, teams: number): number {
  return Math.ceil(overallPick / teams);
}

/** 1-indexed position within that round (NOT snake-adjusted team slot --
 *  `teamSlotAtPick` below is the one that reverses on even rounds). Pick 23 in
 *  a 10-team league is round 3, pick-within-round 3, regardless of which team
 *  slot actually holds it. */
export function pickWithinRound(overallPick: number, teams: number): number {
  return overallPick - (roundOfPick(overallPick, teams) - 1) * teams;
}

/**
 * FR-087 ("It's also helpful to think in rounds"): a compact "round.pick"
 * label for any overall pick number this app displays, e.g. pick 23 in a
 * 10-team league renders "R3.03". Display only -- every caller still keys its
 * own logic off the real overall pick number (`roundOfPick`/
 * `pickWithinRound` above, already used for snake arithmetic elsewhere in
 * this file); this just formats the same two numbers next to the raw pick,
 * never replaces it, so nothing computation-facing changes.
 */
export function roundPickLabel(overallPick: number, teams: number): string {
  const round = roundOfPick(overallPick, teams);
  const posInRound = pickWithinRound(overallPick, teams);
  return `R${round}.${String(posInRound).padStart(2, '0')}`;
}

/** 1-indexed team slot on the clock at a given overall pick. Odd rounds run
 *  slot 1..teams; even rounds reverse, teams..1 -- the same snake RoundGrid.tsx
 *  computes forward, inverted here from pick back to (round, slot). */
export function teamSlotAtPick(overallPick: number, teams: number): number {
  const round = roundOfPick(overallPick, teams);
  const positionInRound = overallPick - (round - 1) * teams; // 1..teams
  return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
}

/**
 * FR-135 (traditional draft board): the exact inverse of `teamSlotAtPick` in
 * the other direction -- given a (round, team slot) address, the overall pick
 * number that address occupies under this league's snake order. The board
 * needs this to number every cell (made or not) from `round.pick` addresses
 * alone, before any pick exists to look up. Kept as the single source of the
 * round/slot<->overallPick formula; `pickNumbersForSlot` below is defined in
 * terms of it rather than re-deriving the same arithmetic a second time.
 */
export function overallPickForRoundSlot(round: number, slot: number, teams: number): number {
  const positionInRound = round % 2 === 1 ? slot : teams - slot + 1;
  return (round - 1) * teams + positionInRound;
}

/** The overall pick number every one of this league's rounds lands on for one
 *  team slot -- used both for "your next pick" and to build the full user-picks
 *  list independent of league.json:pick_sequence (which only covers the real
 *  league's own slot; this needs to work for any slot when logging a mock). */
export function pickNumbersForSlot(teams: number, slot: number, rounds: number): number[] {
  const out: number[] = [];
  for (let round = 1; round <= rounds; round++) {
    out.push(overallPickForRoundSlot(round, slot, teams));
  }
  return out;
}

export function currentOverallPick(picks: DraftPickRecord[]): number {
  return picks.length + 1;
}

export function nextPickForSlot(
  picks: DraftPickRecord[],
  teams: number,
  slot: number,
  rounds: number,
): number | null {
  const cur = currentOverallPick(picks);
  return pickNumbersForSlot(teams, slot, rounds).find((p) => p >= cur) ?? null;
}

export function isSlotOnClock(picks: DraftPickRecord[], teams: number, slot: number): boolean {
  return teamSlotAtPick(currentOverallPick(picks), teams) === slot;
}

export function takenPlayerIds(picks: DraftPickRecord[]): Set<number> {
  return new Set(picks.filter((p) => p.playerId !== null).map((p) => p.playerId as number));
}

/** The backend's mock-logging schema, field-for-field -- see the Draft mode spec.
 *  No mfl_id: board.json carries player_id_gsis, never an mfl_id, so the honest
 *  field to send is the name as entered, not a fabricated cross-walked id. */
export interface DraftLogEntry {
  mock_id: string;
  overall_pick: number;
  round: number;
  team_slot: number;
  player_name_raw: string;
  timestamp: string;
  /** See `EntryMode` -- `null` for picks logged before RETROFIT-5, never a
   *  fabricated 'shortcut'. */
  entry_mode: EntryMode | null;
}

export function toDraftLog(state: DraftState): DraftLogEntry[] {
  return state.picks.map((p) => ({
    mock_id: state.mockId,
    overall_pick: p.overallPick,
    round: p.round,
    team_slot: p.teamSlot,
    player_name_raw: p.playerName,
    timestamp: p.timestamp,
    entry_mode: p.entryMode ?? null,
  }));
}
