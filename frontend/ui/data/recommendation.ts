import type { BoardRow } from './board';

/**
 * Plain-English noun for a position code, used only to compose the FR-058
 * override explanation ("you have no tight end yet") -- never a second source
 * of truth for the position itself, which stays `row.raw.position`.
 */
const POSITION_NOUN: Record<string, string> = {
  QB: 'quarterback',
  RB: 'running back',
  WR: 'wide receiver',
  TE: 'tight end',
  DEF: 'defense',
};

/** One named constant in the stopgap formula, with the plain-word reason it
 *  fired for a specific row -- FR-058's requirement that a departure from VBD
 *  "show which term moved the player, in plain words," not a bare `+18`. */
export interface RecommendationTerm {
  key: 'unfilled_need' | 'tier1_te' | 'early_qb_penalty';
  points: number;
  reason: string;
}

/**
 * Every stopgap term that applies to this row, this round, given which
 * starting positions are still unfilled. `recommendationScore` and
 * `findVbdOverride` both build on this single list rather than each
 * reimplementing the four (three reachable) constants -- so the score and its
 * own explanation can never drift apart.
 */
export function recommendationTerms(
  row: BoardRow,
  round: number,
  unfilledPositions: ReadonlySet<string>,
): RecommendationTerm[] {
  const terms: RecommendationTerm[] = [];
  const pos = row.raw.position;
  if (unfilledPositions.has(pos)) {
    terms.push({ key: 'unfilled_need', points: 8, reason: `you have no ${POSITION_NOUN[pos] ?? pos} yet` });
  }
  if (pos === 'TE' && row.raw.tier === 1) {
    terms.push({ key: 'tier1_te', points: 18, reason: 'this is the last tier-1 tight end left on the board' });
  }
  if (pos === 'QB' && round < 6) {
    terms.push({ key: 'early_qb_penalty', points: -25, reason: 'it is a quarterback being taken before round 6' });
  }
  return terms;
}

/**
 * Draft-room recommendation score, exactly the formula specified for this build:
 *
 *   score = vbd + 8 (unfilled need) + 18 (tier-1 TE) - 25 (QB, round < 6) - 40 (DEF, round < 13)
 *
 * No DEF term is reachable: board.json carries no DEF players at all (no DST data
 * is ingested -- ADR-039), so a DEF branch here would be dead code checking a case
 * that can never occur, not a faithful implementation of the formula's intent.
 *
 * A stopgap, not a validated model. It exists so the recommendation panel has
 * something better than raw rank to sort by this session; it has not been
 * backtested the way the rankings themselves have (see docs/statistical-guardrails.md).
 */
export function recommendationScore(
  row: BoardRow,
  round: number,
  unfilledPositions: ReadonlySet<string>,
): number | null {
  if (row.vbd.kind !== 'present') return null;
  const terms = recommendationTerms(row, round, unfilledPositions);
  return row.vbd.value + terms.reduce((sum, t) => sum + t.points, 0);
}

export interface ScoredRow {
  row: BoardRow;
  score: number;
}

/** Available rows (drafted players already excluded by the caller), ranked by
 *  recommendationScore, best first. Rows with no projection (and so no VBD) sort
 *  last rather than being silently dropped -- still pickable, just not endorsed. */
export function rankByRecommendation(
  rows: BoardRow[],
  round: number,
  unfilledPositions: ReadonlySet<string>,
): ScoredRow[] {
  const scored = rows.map((row) => ({ row, score: recommendationScore(row, round, unfilledPositions) }));
  return scored
    .slice()
    .sort((a, b) => {
      if (a.score === null && b.score === null) return 0;
      if (a.score === null) return 1;
      if (b.score === null) return -1;
      return b.score - a.score;
    })
    .map(({ row, score }) => ({ row, score: score ?? -Infinity }));
}

/**
 * FR-058: "if the recommendation strays from VBD ... the panel needs to
 * provide an explanation." `top` is the recommendation's #1 pick; `available`
 * is every undrafted player the recommendation was allowed to choose from --
 * the comparison is against the single highest-VBD player on the *whole*
 * board, not merely the top-6 shortlist the panel already shows, because the
 * founder's complaint was specifically that a higher-VBD player can sit
 * unmentioned below the fold.
 *
 * Returns null when there is nothing to explain: `top` already *is* the
 * highest-VBD available player (the ordering agrees with VBD), or no
 * available row has a VBD value to compare against. Per FR-058's "nothing at
 * all when nothing moved" -- callers must not render a panel for a null
 * result.
 */
export interface VbdOverride {
  /** The player VBD alone would have ranked first; the recommendation buried them. */
  displaced: BoardRow;
  /** Positive VBD points the recommendation overrode (displaced.vbd - top.vbd).
   *  Always > 0 when this object exists. */
  vbdGap: number;
  /** Every stopgap term that actually explains the departure: boosts that lifted
   *  `top` above `displaced`, and/or penalties that dropped `displaced` below
   *  `top`. Never empty -- score is vbd plus these terms, so if top's own vbd
   *  is lower than displaced's, some term here must account for the gap. */
  firing: Array<{ term: RecommendationTerm; appliesTo: 'top' | 'displaced' }>;
}

export function findVbdOverride(
  top: BoardRow,
  available: BoardRow[],
  round: number,
  unfilledPositions: ReadonlySet<string>,
): VbdOverride | null {
  if (top.vbd.kind !== 'present') return null;

  let leader: BoardRow | null = null;
  let leaderVbd = -Infinity;
  for (const row of available) {
    if (row.vbd.kind !== 'present') continue;
    if (row.vbd.value > leaderVbd) {
      leader = row;
      leaderVbd = row.vbd.value;
    }
  }
  if (leader === null || leader.id === top.id) return null;

  const vbdGap = leaderVbd - top.vbd.value;
  if (vbdGap <= 0) return null; // top already has >= VBD -- the order agrees with VBD

  const topTerms = recommendationTerms(top, round, unfilledPositions).filter((t) => t.points > 0);
  const leaderTerms = recommendationTerms(leader, round, unfilledPositions).filter((t) => t.points < 0);
  const firing: VbdOverride['firing'] = [
    ...topTerms.map((term) => ({ term, appliesTo: 'top' as const })),
    ...leaderTerms.map((term) => ({ term, appliesTo: 'displaced' as const })),
  ];
  // Guard, should not be reachable: score = vbd + terms, so a lower-vbd row
  // outscoring a higher-vbd one requires at least one nonzero term somewhere.
  if (firing.length === 0) return null;

  return { displaced: leader, vbdGap, firing };
}
