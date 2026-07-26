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
      picks: parsed.picks ?? [],
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

/** 1-indexed team slot on the clock at a given overall pick. Odd rounds run
 *  slot 1..teams; even rounds reverse, teams..1 -- the same snake RoundGrid.tsx
 *  computes forward, inverted here from pick back to (round, slot). */
export function teamSlotAtPick(overallPick: number, teams: number): number {
  const round = roundOfPick(overallPick, teams);
  const positionInRound = overallPick - (round - 1) * teams; // 1..teams
  return round % 2 === 1 ? positionInRound : teams - positionInRound + 1;
}

/** The overall pick number every one of this league's rounds lands on for one
 *  team slot -- used both for "your next pick" and to build the full user-picks
 *  list independent of league.json:pick_sequence (which only covers the real
 *  league's own slot; this needs to work for any slot when logging a mock). */
export function pickNumbersForSlot(teams: number, slot: number, rounds: number): number[] {
  const out: number[] = [];
  for (let round = 1; round <= rounds; round++) {
    const positionInRound = round % 2 === 1 ? slot : teams - slot + 1;
    out.push((round - 1) * teams + positionInRound);
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
}

export function toDraftLog(state: DraftState): DraftLogEntry[] {
  return state.picks.map((p) => ({
    mock_id: state.mockId,
    overall_pick: p.overallPick,
    round: p.round,
    team_slot: p.teamSlot,
    player_name_raw: p.playerName,
    timestamp: p.timestamp,
  }));
}
