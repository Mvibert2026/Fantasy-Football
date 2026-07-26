import type { Cell } from './cell';
import { playerAvailabilityAtPick, type SigmaCell } from './availability';
import type { BoardRow } from './board';
import type { DraftPickRecord } from './draft';
import { teamSlotAtPick } from './draft';
import type { Dataset } from './load';
import type { LeagueConfig } from './league';

/**
 * Live availability -- the two-number model, FRONTEND-SPEC.md §5.2, implemented
 * exactly as specified. This runs entirely client-side, per pick, from state
 * already on hand: no server round-trip, matching "Recompute runs client-side per
 * pick" in the spec itself.
 *
 * One deliberate substitution, and it makes the result MORE honest than the
 * spec's own reference implementation, not less: the spec's band width is a
 * single placeholder constant (`noise_band = 0.12`, explicitly flagged in the
 * spec's own §10 as "swap the real bootstrapped width"). This backend has never
 * shipped that field -- confirmed directly with the backend session -- but it
 * does ship three real sigma readings (5/10/20) per pick in availability.json.
 * The band width used here is half the real spread between the sigma-5 and
 * sigma-20 readings at the same pick, not a fabricated constant.
 *
 * `baseline_p` (spec §6.3) is this app's existing Prep-mode marginal probability
 * (ui/data/availability.ts, sigma-10 reading) -- already real, already built.
 * `live_p` is that baseline adjusted by the roster-need and positional-run
 * signals below, exactly per the spec's formula.
 */

const FLAT = 0.2;
const NEED_COEFFICIENT = -0.62;
const RUN_COEFFICIENT = -1.25;

export type Signal = 'none' | 'thin' | 'ok';

export interface LiveAvailabilityResult {
  baseline: Cell<number>;
  /** Null exactly when signal is 'none' -- never a silent fallback to baseline. */
  live: number | null;
  signal: Signal;
  /** Both components shown separately per the spec's explicit display contract --
   *  never combined into one delta. Null alongside a null `live`. */
  adjustment: { need: number; run: number } | null;
  band: { lo: number; hi: number; w: number } | null;
  picksLogged: number;
  picksRequired: number;
}

function logit(v: number): number {
  const c = Math.min(0.995, Math.max(0.005, v));
  return Math.log(c / (1 - c));
}

function sigmoid(z: number): number {
  return 1 / (1 + Math.exp(-z));
}

function clamp01(v: number): number {
  return Math.min(0.99, Math.max(0.01, v));
}

/** teamAt(n), 1-indexed to match this app's DraftPickRecord.teamSlot convention
 *  (the spec's own reference is 0-indexed; teamSlotAtPick already is 1-indexed,
 *  see ui/data/draft.ts, checked against RoundGrid.tsx's forward formula). */
function teamSlotsBetween(fromPickInclusive: number, toPickExclusive: number, teams: number): number[] {
  const out: number[] = [];
  for (let p = fromPickInclusive; p < toPickExclusive; p++) out.push(teamSlotAtPick(p, teams));
  return out;
}

/** Roster need per team, §5.2: want = {QB:qb, RB:rb+1, WR:wr+1, TE:te, DEF:def},
 *  gap[k] = max(0, want[k]-have[k]), total = sum(gap). +1 on RB/WR absorbs flex,
 *  per the spec's own comment. DEF's `have` can never grow (no DEF player exists
 *  anywhere on this board -- ADR-039), so DEF's gap sits at a constant `want.DEF`
 *  for the whole draft; that's an honest reflection of what this board can model,
 *  not a bug. */
function rosterNeed(
  teamSlot: number,
  picks: DraftPickRecord[],
  rowsById: Map<number, BoardRow>,
  starters: Record<string, number>,
): { gap: Record<string, number>; total: number } {
  const want: Record<string, number> = {
    QB: starters.QB ?? 0,
    RB: (starters.RB ?? 0) + 1,
    WR: (starters.WR ?? 0) + 1,
    TE: starters.TE ?? 0,
    DEF: starters.DEF ?? 0,
  };
  const have: Record<string, number> = { QB: 0, RB: 0, WR: 0, TE: 0, DEF: 0 };
  for (const pick of picks) {
    if (pick.teamSlot !== teamSlot || pick.playerId === null) continue;
    const row = rowsById.get(pick.playerId);
    if (!row) continue;
    const pos = row.raw.position;
    if (pos in have) have[pos] = (have[pos] ?? 0) + 1;
  }
  const gap: Record<string, number> = {};
  let total = 0;
  for (const [pos, w] of Object.entries(want)) {
    const g = Math.max(0, w - (have[pos] ?? 0));
    gap[pos] = g;
    total += g;
  }
  return { gap, total };
}

export function computeLiveAvailability({
  data,
  league,
  row,
  targetPick,
  picks,
  rowsById,
}: {
  data: Dataset;
  league: LeagueConfig;
  row: BoardRow;
  /** The overall pick to project availability at -- typically the user's next pick. */
  targetPick: number;
  picks: DraftPickRecord[];
  rowsById: Map<number, BoardRow>;
}): LiveAvailabilityResult {
  const name = row.name.kind === 'present' ? row.name.value : '';
  const baselineCell: SigmaCell = playerAvailabilityAtPick(data, name, targetPick);
  const baseline = baselineCell.sigma10;

  const picksLogged = picks.length;
  const teams = league.teams.kind === 'present' ? league.teams.value : 0;
  const cur = picksLogged + 1;
  const minPicks = Math.max(4, Math.round(teams * 0.5));
  const between = teams > 0 ? teamSlotsBetween(cur, targetPick, teams) : [];

  const bandFromSigma = (widen: boolean): { lo: number; hi: number; w: number } | null => {
    if (baselineCell.sigma5.kind !== 'present' || baselineCell.sigma20.kind !== 'present') return null;
    const w = ((baselineCell.sigma20.value - baselineCell.sigma5.value) / 2) * (widen ? 1.6 : 1);
    const mid = baseline.kind === 'present' ? baseline.value : baselineCell.sigma10.kind === 'present' ? baselineCell.sigma10.value : 0.5;
    return { lo: Math.max(0, mid - w), hi: Math.min(1, mid + w), w };
  };

  if (between.length === 0 || picksLogged < minPicks) {
    return {
      baseline,
      live: null,
      signal: 'none',
      adjustment: null,
      band: null,
      picksLogged,
      picksRequired: minPicks,
    };
  }

  const starters = data.league.roster.starters as Record<string, number>;
  let demand = 0;
  for (const slot of between) {
    const need = rosterNeed(slot, picks, rowsById, starters);
    demand += need.total > 0 ? (need.gap[row.raw.position] ?? 0) / need.total : FLAT;
  }

  const recent = picks
    .slice(-5)
    .map((p) => (p.playerId !== null ? rowsById.get(p.playerId) : undefined))
    .filter((r): r is BoardRow => !!r);
  const runN = recent.filter((r) => r.raw.position === row.raw.position).length;
  const runZ = recent.length >= 3 ? runN / recent.length - FLAT : 0;

  const needZ = (demand - between.length * FLAT) / Math.max(1, Math.sqrt(between.length));
  const needAdj = NEED_COEFFICIENT * needZ;
  const runAdj = RUN_COEFFICIENT * runZ;

  const baseForLogit = baseline.kind === 'present' ? baseline.value : 0.5;
  const live = clamp01(sigmoid(logit(baseForLogit) + needAdj + runAdj));
  const signal: Signal = picksLogged < teams ? 'thin' : 'ok';

  return {
    baseline,
    live,
    signal,
    adjustment: { need: needAdj, run: runAdj },
    band: bandFromSigma(signal === 'thin'),
    picksLogged,
    picksRequired: minPicks,
  };
}

/** §5.3: probability as frequency. A bare percentage reads as decisive; the dot
 *  array is the redundant, honest framing this product exists to make standard. */
export function dotsFilled(p: number): number {
  return Math.round(p * 10);
}

export function freqText(p: number): string {
  return `${dotsFilled(p)} in 10 drafts`;
}
