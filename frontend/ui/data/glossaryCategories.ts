/**
 * Glossary organisation, FRONTEND-SPEC.md §6.8/§7.3: four categories, and a
 * "backing field" per term.
 *
 * Neither exists as a field in glossary.json -- the real export is a flat
 * `{ [term]: { short_definition, long_explanation } }` map with no `category` and
 * no per-term field pointer (spec's own example payload describes an aspirational
 * richer shape this backend hasn't built). Both tables below are this app's own
 * editorial organisation of real content, not sourced data masquerading as such:
 * every definition's *text* still comes from glossary.json verbatim, and every
 * `field` path below points at a real Cell this app already renders elsewhere
 * (cross-checked against ui/data/trace-fields.ts and this session's own
 * assistant/reasoning modules) -- categorising and cross-referencing real terms
 * is an IA decision, not an invented fact about what a term means.
 *
 * A term not listed here still renders -- just under "Other" with no backing
 * field shown, so an export that adds a term never disappears silently.
 */

export type GlossaryCategory = 'prob' | 'value' | 'draft' | 'state' | 'other';

export const CATEGORY_LABEL: Record<GlossaryCategory, string> = {
  prob: 'Probability & uncertainty',
  value: 'Value & ranking',
  draft: 'Draft mechanics',
  state: 'Data state',
  other: 'Other',
};

export const CATEGORY_ORDER: GlossaryCategory[] = ['value', 'prob', 'draft', 'state', 'other'];

interface TermMeta {
  category: GlossaryCategory;
  field?: string;
}

const TERM_META: Record<string, TermMeta> = {
  VBD: { category: 'value', field: 'board.json:players[].vbd' },
  'replacement level': { category: 'value', field: 'league.json:replacement_levels' },
  'consensus rank': { category: 'value', field: 'board.json:players[].consensus_rank' },
  'confidence interval': { category: 'prob', field: 'board.json:players[].ci_low / ci_high' },
  tier: { category: 'value', field: 'board.json:players[].tier_label' },
  'structural adjustment': { category: 'value', field: 'board.json:players[].structural_adjustment' },
  'evaluative adjustment': { category: 'value', field: 'board.json:players[].evaluative_adjustment' },
  'availability probability': { category: 'prob', field: 'availability.json:by_player' },
  sigma: { category: 'prob', field: 'availability.json:metadata.sigma_values' },
  'sign test': { category: 'prob', field: 'strategies.json:strategies[].by_sigma[].sign_test_p' },
  'power floor': { category: 'prob', field: 'strategies.json:power_floor' },
  holdout: { category: 'state' },
  'projected points': { category: 'value', field: 'board.json:players[].projected_points' },
};

export function categoryOf(term: string): GlossaryCategory {
  return TERM_META[term]?.category ?? 'other';
}

export function fieldOf(term: string): string | undefined {
  return TERM_META[term]?.field;
}
