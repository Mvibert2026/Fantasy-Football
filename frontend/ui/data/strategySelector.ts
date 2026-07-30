import type { ScoredRow } from './recommendation';
import type { RawStrategies, RawStrategySigma } from './types';

/**
 * FR-061 / `docs/design/STRATEGY-SELECTOR.md`.
 *
 * "Rankings do not move; recommendations do, and they explain why." This module is
 * the "recommendations do" half: given the currently-selected strategy, how (if at
 * all) does the Recommend tab's shortlist reorder, and what plain-language rule
 * explains it.
 *
 * A hard constraint from the design spec and the founder's own framing: the
 * simulated strategies in `strategies.json` are OUTCOME measurements (how a whole
 * draft following that strategy scored, 600 sims/cell), not a per-pick scoring
 * formula. `src/draft_sim.py`'s `strategy_hero_rb` / `strategy_zero_rb` /
 * `strategy_elite_te` (`_positional_bias`) / `strategy_qb_early` ARE the real,
 * versioned per-pick rules that produced those measurements -- but they bias
 * `effective_rank` (consensus rank ± noise, in RANK-SLOT units) by round-gated
 * deltas like -45 or +100. This app's Recommend tab scores in VBD POINTS, a
 * different unit with no established conversion between the two. Porting the raw
 * numeric deltas into the VBD-point score would fabricate an equivalence that does
 * not exist -- exactly the "unearned confidence" CLAUDE.md forbids.
 *
 * So `applyStrategyPreference` ports the DIRECTION and ROUND WINDOW of each rule
 * faithfully (same conditions as the source function) but expresses it as a hard
 * reorder of the recommendation shortlist within the pool VBD already ranked --
 * never as a blended score with an invented magnitude. `strategy_balanced`'s rule
 * is continuous and need-weighted rather than round-gated, and this app's existing
 * default recommendation already carries its own need-based term
 * (`recommendation.ts`'s `unfilled_need`) -- rather than invent a claim that the two
 * are equivalent, Balanced applies no additional reorder here and says so.
 */

export type StrategyKey = 'bpa_consensus' | 'balanced' | 'zero_rb' | 'hero_rb' | 'elite_te_early' | 'qb_early';

export interface StrategyCatalogEntry {
  key: StrategyKey;
  label: string;
}

/** Every strategy this app knows a name for -- a stable identifier/label mapping,
 *  not a measured fact, so this is the one place in this module allowed to be a
 *  plain constant rather than derived from an export. Used both to label
 *  `strategies.json` rows (primary league) and to list the selectable-but-unpriced
 *  options on a league with no strategies.json at all (generic track). */
export const STRATEGY_CATALOG: readonly StrategyCatalogEntry[] = [
  { key: 'bpa_consensus', label: 'Best player available' },
  { key: 'balanced', label: 'Balanced' },
  { key: 'zero_rb', label: 'Zero RB' },
  { key: 'hero_rb', label: 'Hero RB' },
  { key: 'elite_te_early', label: 'Elite TE early' },
  { key: 'qb_early', label: 'QB early' },
];

export function strategyLabel(key: string): string {
  return STRATEGY_CATALOG.find((s) => s.key === key)?.label ?? key;
}

/** Plain-word rule text for each strategy's Recommend-tab effect, shown next to
 *  the selector and in the strategy-adjustment panel when it fires. Every
 *  round-gated rule here names the exact round window it applies -- that part is
 *  the honest reason and always shows. The `src/draft_sim.py::strategy_*` source
 *  citation is developer-facing sourcing text (FR-121); it is appended only when
 *  `showSources` is on (`ui/data/traceMode.ts`, default off), never welded into
 *  the reason itself. */
export function strategyRuleText(key: StrategyKey, showSources: boolean = false): string {
  const src = (fn: string) => (showSources ? ` (src/draft_sim.py::${fn})` : '');
  switch (key) {
    case 'bpa_consensus':
      return 'No adjustment -- this is the recommendation you already see by default.';
    case 'balanced':
      return (
        `Balanced's simulated rule is a continuous, need-weighted adjustment across the whole draft${src('strategy_balanced')}, ` +
        "not a round-gated one -- close in spirit to this app's own default unfilled-need term already " +
        "in the recommendation score. Selecting it does not additionally reorder today's shortlist."
      );
    case 'zero_rb':
      return (
        `Avoid running backs through round 4${src('strategy_zero_rb')}. Direction and round window only ` +
        '-- see the module note on magnitude.'
      );
    case 'hero_rb':
      return (
        `Strongly prefer a running back with round 1's pick${src('strategy_hero_rb')}. (The source rule ` +
        "also softly leans RB through round 5 with a WR penalty; that softer lean isn't reproduced here " +
        '-- it has no unit-compatible magnitude to port faithfully.)'
      );
    case 'elite_te_early':
      return `Prefer a tight end through round 3${src('strategy_elite_te (_positional_bias)')}. Direction and round window only.`;
    case 'qb_early':
      return (
        `Prefer a quarterback through round 3${src('strategy_qb_early (_positional_bias)')} -- overriding ` +
        "this app's own default penalty against an early QB while it's active."
      );
  }
}

/** Positive at `round`, per the ported rule -- null means "no reorder from this
 *  strategy at this round." Kept separate from `applyStrategyPreference` so a
 *  caller can tell whether the strategy has anything to say about this pick at
 *  all, without diffing two arrays. */
export function strategyPromotedPosition(key: StrategyKey, round: number): string | null {
  if (key === 'hero_rb' && round === 1) return 'RB';
  if (key === 'elite_te_early' && round <= 3) return 'TE';
  if (key === 'qb_early' && round <= 3) return 'QB';
  return null;
}

export function strategyDemotedPosition(key: StrategyKey, round: number): string | null {
  if (key === 'zero_rb' && round <= 4) return 'RB';
  return null;
}

/** Reorders an already VBD-recommendation-ranked list by the active strategy's
 *  round-gated preference, stable within each group (VBD order is preserved
 *  inside "promoted" and inside "the rest"/"demoted"). A no-op for
 *  `bpa_consensus`, `balanced`, and any round outside a strategy's stated window
 *  -- see `strategyRuleText`. */
export function applyStrategyPreference(scored: ScoredRow[], round: number, key: StrategyKey): ScoredRow[] {
  const promote = strategyPromotedPosition(key, round);
  if (promote) {
    const first = scored.filter((s) => s.row.raw.position === promote);
    const rest = scored.filter((s) => s.row.raw.position !== promote);
    return [...first, ...rest];
  }
  const demote = strategyDemotedPosition(key, round);
  if (demote) {
    const rest = scored.filter((s) => s.row.raw.position !== demote);
    const last = scored.filter((s) => s.row.raw.position === demote);
    return [...rest, ...last];
  }
  return scored;
}

export interface StrategyDisplayRow {
  key: string;
  label: string;
  isBaseline: boolean;
  /** null for the baseline row -- it has nothing to be measured against. */
  marginRange: { low: number; high: number } | null;
  /** One fill/direction per season, read from the sigma=10 cell's own
   *  `per_season_margin` (the middle of the three simulated sigma settings --
   *  the margin range beside it already shows the across-sigma spread, so the
   *  dots don't need to). null for the baseline. */
  seasonSigns: Array<'up' | 'down' | null> | null;
  seasonsPositive: number | null;
  nSeasons: number;
  verdict: string;
}

const DISPLAY_SIGMA = 10.0;

function marginRangeOf(bySigma: RawStrategySigma[]): { low: number; high: number } | null {
  const margins = bySigma.map((c) => c.margin_vs_baseline).filter((m): m is number => m !== null);
  if (margins.length === 0) return null;
  return { low: Math.min(...margins), high: Math.max(...margins) };
}

/**
 * Display order, computed LIVE from the export every time rather than a hardcoded
 * ranking -- `docs/design/STRATEGY-SELECTOR.md`'s own table happens to read
 * best-to-worst by season-consistency, but writing that order as a fixed list here
 * would silently go stale the day this export re-runs with different numbers.
 * Baseline always first (it is not "worse" or "better," it's the reference); the
 * rest sorted by seasons-positive descending, ties broken by the sigma=10 margin.
 */
export function orderedStrategiesFor(strategies: RawStrategies): StrategyDisplayRow[] {
  const rows: StrategyDisplayRow[] = strategies.strategies.map((s) => {
    const displayCell = s.by_sigma.find((c) => c.sigma === DISPLAY_SIGMA) ?? null;
    return {
      key: s.name,
      label: strategyLabel(s.name),
      isBaseline: s.is_baseline,
      marginRange: marginRangeOf(s.by_sigma),
      seasonSigns:
        displayCell?.per_season_margin != null
          ? strategies.seasons.map((yr) => {
              const m = displayCell.per_season_margin![String(yr)];
              if (m === undefined) return null;
              return m > 0 ? 'up' : m < 0 ? 'down' : null;
            })
          : null,
      seasonsPositive: displayCell?.seasons_positive ?? null,
      nSeasons: strategies.power_floor.n_seasons,
      verdict: s.verdict,
    };
  });
  const baseline = rows.filter((r) => r.isBaseline);
  const rest = rows
    .filter((r) => !r.isBaseline)
    .sort((a, b) => {
      const ap = a.seasonsPositive ?? -1;
      const bp = b.seasonsPositive ?? -1;
      if (bp !== ap) return bp - ap;
      const am = a.marginRange ? (a.marginRange.low + a.marginRange.high) / 2 : -Infinity;
      const bm = b.marginRange ? (b.marginRange.low + b.marginRange.high) / 2 : -Infinity;
      return bm - am;
    });
  return [...baseline, ...rest];
}

/** `league.json:roster` summarised into the same shape of sentence the design
 *  spec's generic-track example uses ("nine starters, one flex and a kicker") --
 *  computed live from THIS league's own roster, never the spec's illustrative
 *  numbers, which were about a different league (yahoo-02). */
export function rosterShapeSummary(roster: { starters: Record<string, number>; kicker: boolean }): string {
  const flex = roster.starters['FLEX'] ?? 0;
  const nonFlexTotal = Object.entries(roster.starters)
    .filter(([k]) => k !== 'FLEX')
    .reduce((sum, [, n]) => sum + n, 0);
  const totalStarters = nonFlexTotal + flex;
  const parts = [
    `${totalStarters} starter${totalStarters === 1 ? '' : 's'}`,
    `${flex} flex`,
    roster.kicker ? '1 kicker' : 'no kicker',
  ];
  return parts.join(', ');
}
