import { absent, fromNullable, present, type Cell } from './cell';
import type { Dataset } from './load';
import { runIdOf } from './load';
import type { Position, RawBoardPlayer } from './types';

/**
 * Turns raw board records into rows of Cells.
 *
 * The important decision is in `projectedPoints`. For 233 of 378 players
 * `projection_within_fitted_range` is false and `projection_note` reads, verbatim:
 *
 *   "Beyond the fitted range of the projection curve. Extrapolated, no interval
 *    available -- do not display a point projection for this player."
 *
 * The field is populated, but the contract instructs us not to show it. So the Cell
 * is `absent`, carrying that note as its reason. The number exists and is deliberately
 * not rendered; the user sees why rather than seeing a blank.
 */

export interface BoardRow {
  id: number;
  /** Identity fields. Every player has these -- they are what makes a sparse row still useful. */
  name: Cell<string>;
  position: Cell<Position>;
  team: Cell<string>;
  overallRank: Cell<number>;
  positionalLabel: Cell<string>;
  positionalRank: number;
  byeWeek: Cell<number>;
  tierLabel: Cell<string>;

  /** Absent for the 233 out-of-range players. */
  projectedPoints: Cell<number>;
  /**
   * `appliesTo` carries `ci_applies_to` verbatim ("vbd" on every one of the
   * 145 rows that have an interval today) -- do not assume it, resolve it via
   * `ciTargetFor` below before rendering. Absent for the same 233 out-of-range
   * players `projectedPoints` is absent for.
   */
  interval: Cell<{ low: number; high: number; appliesTo: string }>;

  vbd: Cell<number>;
  consensusRank: Cell<number>;
  deltaVsConsensus: Cell<number>;

  /**
   * MFL-proxy ADP (contract 1.14.0, thread 082) -- market draft position, a
   * different claim from `consensusRank` (expert opinion). Absent for most
   * of the board (MFL only covers roughly the top ~230 players); that is a
   * real null, never a fabricated 0 or rank. `adpSource` is not a Cell since
   * it is always the same string travelling alongside the other four ADP
   * fields on this row, but it is threaded through raw for display so a
   * bare ADP number is never shown unlabelled.
   */
  adp: Cell<number>;
  adpMinPick: Cell<number>;
  adpMaxPick: Cell<number>;
  adpSelectedPct: Cell<number>;
  adpSource: string | null;

  /** Structural only. See `attribution` below. */
  structuralAdjustment: Cell<number>;
  replacementLevelsComponent: Cell<number>;
  scoringAndVbdComponent: Cell<number>;
  /**
   * Deliberately not a number. The board holds no player-level opinion, so there is
   * nothing to attribute -- the export says so and this carries that sentence through.
   */
  evaluativeNote: string;

  /** True when the projection is an out-of-range extrapolation. Drives the sparse styling. */
  isSparse: boolean;
  raw: RawBoardPlayer;
}

/**
 * What a row's interval actually brackets, read from `board.json:ci_applies_to`
 * rather than assumed. Founder, 2026-07-30: "what is in the parenthesis here --
 * it's a range, but the projection isn't in it?" He was right -- every consumer
 * (Board's PROJ column, DraftRoom's RECOMMENDED card, PlayerDetail's range bar)
 * paired the interval with `projected_points` while the export said, on every
 * one of the 145 rows that carry an interval, `ci_applies_to: "vbd"`.
 *
 * This is the one place that decision gets made. A consumer that wants to
 * render the interval calls `ciTargetFor(row)` and attaches it to whichever
 * Cell comes back -- never to `row.projectedPoints` directly, and never by
 * assuming the string is always `"vbd"`. `known` covers the two quantities
 * this app has a Cell for; anything else is `unrecognized` and must render as
 * an honest absence (the value is real, but this UI has no field to attach it
 * to), never silently dropped and never silently paired with points anyway.
 */
export type CiQuantity = 'vbd' | 'projected_points';

const CI_QUANTITY_LABEL: Record<CiQuantity, string> = {
  vbd: 'VBD',
  projected_points: 'PROJ',
};

export type CiTarget =
  | { kind: 'none' }
  | { kind: 'known'; quantity: CiQuantity; label: string; cell: Cell<number> }
  | { kind: 'unrecognized'; raw: string };

export function ciTargetFor(row: BoardRow): CiTarget {
  if (row.interval.kind !== 'present') return { kind: 'none' };
  const raw = row.interval.value.appliesTo;
  if (raw === 'vbd' || raw === 'projected_points') {
    const cell = raw === 'vbd' ? row.vbd : row.projectedPoints;
    return { kind: 'known', quantity: raw, label: CI_QUANTITY_LABEL[raw], cell };
  }
  return { kind: 'unrecognized', raw };
}

export function buildRows(data: Dataset): BoardRow[] {
  const runId = runIdOf(data.manifest, 'board');

  return data.board.players.map((p, i) => {
    const at = (field: string) => `board.json:players[${i}].${field}`;

    const suppressionReason =
      p.projection_note ??
      'No projection note was supplied for this player, so the projection is not displayed.';

    const projectedPoints: Cell<number> = p.projection_within_fitted_range
      ? present(p.projected_points, at('projected_points'), runId)
      : absent(at('projected_points'), runId, suppressionReason);

    const interval: Cell<{ low: number; high: number; appliesTo: string }> =
      p.ci_low === null || p.ci_high === null
        ? absent(at('ci_low'), runId, suppressionReason)
        : present(
            { low: p.ci_low, high: p.ci_high, appliesTo: p.ci_applies_to },
            at('ci_low'),
            runId,
          );

    const noAdpReason =
      'No MFL ADP data for this player -- MyFantasyLeague’s public sample only covers ' +
      'roughly the top ~230 players in a 10-team pull, so most of the board genuinely has no ' +
      'market opinion on file. Not a zero, not a rank -- not computed.';

    return {
      id: p.id,
      name: present(p.player, at('player'), runId),
      position: present(p.position, at('position'), runId),
      team: present(p.team, at('team'), runId),
      overallRank: present(p.overall_rank, at('overall_rank'), runId),
      positionalLabel: present(p.positional_label, at('positional_label'), runId),
      positionalRank: p.positional_rank,
      byeWeek: fromNullable(
        p.bye_week,
        at('bye_week'),
        runId,
        'No bye week in the 2026 schedule for this player -- typically a free agent or unrostered.',
      ),
      tierLabel: present(p.tier_label, at('tier_label'), runId),
      projectedPoints,
      interval,
      vbd: present(p.vbd, at('vbd'), runId),
      consensusRank: present(p.consensus_rank, at('consensus_rank'), runId),
      deltaVsConsensus: present(p.delta_vs_consensus, at('delta_vs_consensus'), runId),
      adp: fromNullable(p.adp ?? null, at('adp'), runId, noAdpReason),
      adpMinPick: fromNullable(p.adp_min_pick ?? null, at('adp_min_pick'), runId, noAdpReason),
      adpMaxPick: fromNullable(p.adp_max_pick ?? null, at('adp_max_pick'), runId, noAdpReason),
      adpSelectedPct: fromNullable(p.adp_selected_pct ?? null, at('adp_selected_pct'), runId, noAdpReason),
      adpSource: p.adp_source ?? null,
      structuralAdjustment: present(p.structural_adjustment, at('structural_adjustment'), runId),
      replacementLevelsComponent: present(
        p.structural_breakdown.replacement_levels,
        at('structural_breakdown.replacement_levels'),
        runId,
      ),
      scoringAndVbdComponent: present(
        p.structural_breakdown.scoring_and_vbd_method,
        at('structural_breakdown.scoring_and_vbd_method'),
        runId,
      ),
      evaluativeNote: p.evaluative_adjustment_note,
      isSparse: !p.projection_within_fitted_range,
      raw: p,
    };
  });
}

export const POSITIONS: Position[] = ['QB', 'RB', 'WR', 'TE'];

export interface BoardFilters {
  positions: Position[];
  tiers: string[];
  /** Inclusive bounds on delta_vs_consensus. Null means unbounded. */
  minDelta: number | null;
  maxDelta: number | null;
  /** When true, keep only rows whose projection is suppressed. */
  sparseOnly: boolean;
  search: string;
}

export const NO_FILTERS: BoardFilters = {
  positions: [],
  tiers: [],
  minDelta: null,
  maxDelta: null,
  sparseOnly: false,
  search: '',
};

export function applyFilters(rows: BoardRow[], f: BoardFilters): BoardRow[] {
  const needle = f.search.trim().toLowerCase();
  return rows.filter((row) => {
    if (
      f.positions.length &&
      !(row.position.kind === 'present' && f.positions.includes(row.position.value))
    ) {
      return false;
    }
    if (f.tiers.length && row.tierLabel.kind === 'present' && !f.tiers.includes(row.tierLabel.value))
      return false;
    if (f.sparseOnly && !row.isSparse) return false;
    if (row.deltaVsConsensus.kind === 'present') {
      const d = row.deltaVsConsensus.value;
      if (f.minDelta !== null && d < f.minDelta) return false;
      if (f.maxDelta !== null && d > f.maxDelta) return false;
    }
    if (needle) {
      const name = row.name.kind === 'present' ? row.name.value.toLowerCase() : '';
      const team = row.team.kind === 'present' ? row.team.value.toLowerCase() : '';
      if (!name.includes(needle) && !team.includes(needle)) return false;
    }
    return true;
  });
}

/** Distinct tier labels in board order, for the filter control. */
export function tierLabels(rows: BoardRow[]): string[] {
  const seen: string[] = [];
  for (const row of rows) {
    if (row.tierLabel.kind === 'present' && !seen.includes(row.tierLabel.value)) {
      seen.push(row.tierLabel.value);
    }
  }
  return seen;
}
