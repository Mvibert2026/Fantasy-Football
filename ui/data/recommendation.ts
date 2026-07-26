import type { BoardRow } from './board';

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
  let score = row.vbd.value;
  const pos = row.raw.position;
  if (unfilledPositions.has(pos)) score += 8;
  if (pos === 'TE' && row.raw.tier === 1) score += 18;
  if (pos === 'QB' && round < 6) score -= 25;
  return score;
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
