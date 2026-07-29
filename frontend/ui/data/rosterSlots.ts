import type { BoardRow } from './board';
import type { DraftPickRecord } from './draft';
import type { Dataset } from './load';
import type { LeagueConfig } from './league';

/**
 * Roster-need arithmetic for one team's picks, extracted (not duplicated) from
 * `DraftRoom.tsx`'s original `buildRosterSlots` -- originally written to build
 * *only* the user's own MY ROSTER panel (`userPicks` was always
 * `draft.picks.filter(p => p.teamSlot === userSlot)`). The function itself was
 * always slot-agnostic -- it takes whatever picks it's handed -- so filtering by
 * a *different* team slot before calling it needs no change here at all. Moved
 * to its own module so `LiveOpponents.tsx` (thread FR-032, "make Opponents
 * functional during a live draft") can call the exact same arithmetic per
 * opponent instead of re-deriving it.
 */

export interface RosterSlot {
  slot: string;
  kind: 'starter' | 'flex' | 'bench' | 'ir';
  position: string | null; // null for FLEX/BN/IR, which accept multiple positions
  row: BoardRow | null;
}

/** Greedy slot assignment: each of the given team's picks, in draft order,
 *  fills the first open slot that matches its position, then the first open
 *  FLEX it's eligible for, then the first open bench slot. Good enough for a
 *  dry run -- not a claim about how the real platform will assign slots.
 *  `picks` may be any team's picks (filtered by `teamSlot` by the caller), not
 *  only the user's -- this function has never looked at `teamSlot` itself. */
export function buildRosterSlots(
  picks: DraftPickRecord[],
  league: LeagueConfig,
  data: Dataset,
  rowsById: Map<number, BoardRow>,
): RosterSlot[] {
  const slots: RosterSlot[] = [];
  for (const t of league.thresholds) {
    if (t.position === 'FLEX') continue; // placed after named positions, below
    const count = t.starters.kind === 'present' ? t.starters.value : 0;
    for (let i = 0; i < count; i++) slots.push({ slot: t.position, kind: 'starter', position: t.position, row: null });
  }
  const flex = league.thresholds.find((t) => t.position === 'FLEX');
  const flexCount = flex && flex.starters.kind === 'present' ? flex.starters.value : 0;
  for (let i = 0; i < flexCount; i++) slots.push({ slot: 'FLEX', kind: 'flex', position: null, row: null });
  const bench = data.league.roster.bench ?? 0;
  for (let i = 0; i < bench; i++) slots.push({ slot: 'BN', kind: 'bench', position: null, row: null });
  // Thread 058 section D2: an IR slot, one per league.json:roster.ir (a real
  // field, already typed -- not the design mockup's hardcoded single IR row).
  // Deliberately excluded from the fill-target search below, same as the
  // design reference (docs/design-reference/prototype.dc.html line 2563,
  // `slots.push({slot:"IR",p:null})` -- never filled from the generic pick
  // pool): this build has no injury-designation data to decide which pick
  // belongs on IR, and guessing would be exactly the kind of fabricated
  // assignment Principle #1 forbids. It renders as a permanently-open slot
  // until a real injury signal exists to drive it.
  const ir = data.league.roster.ir ?? 0;
  for (let i = 0; i < ir; i++) slots.push({ slot: 'IR', kind: 'ir', position: null, row: null });
  const flexEligible = new Set(data.league.roster.flex_eligible ?? []);

  for (const pick of picks) {
    if (pick.playerId === null) continue;
    const row = rowsById.get(pick.playerId);
    const pos = row?.raw.position ?? null;
    let target =
      slots.find((s) => s.kind === 'starter' && s.position === pos && s.row === null) ??
      (pos && flexEligible.has(pos) ? slots.find((s) => s.kind === 'flex' && s.row === null) : undefined) ??
      slots.find((s) => s.kind === 'bench' && s.row === null);
    if (!target) continue;
    target.row = row ?? null;
    if (!row) target.slot = `${target.slot} (${pick.playerName})`;
  }
  return slots;
}
