import { matchTemplate } from './templates';

/**
 * Intent classification. One entry point, three destinations.
 *
 * This is deliberately keyword-and-pattern based rather than model-based. Routing is
 * the one decision that must not be probabilistic: sending a board-arithmetic question
 * to the language model would turn a checkable number into prose, which is the failure
 * this whole design exists to prevent. A rule that occasionally routes to the wrong
 * lane is recoverable; a router that silently launders MODEL claims into INFERENCE ones
 * is not.
 */

export type Lane = 'export' | 'news' | 'reasoning';

/**
 * News intent is checked first and matched on explicit vocabulary. If someone asks
 * about an injury, they must not get board arithmetic dressed up as a status report.
 */
const NEWS_PATTERN =
  /\b(?:news|injur\w*|hurt|questionable|doubtful|probable|inactive|ruled out|practice|snap count|report(?:ed|ing)?|signing|signed|traded?|trade|waiver|suspension|suspended|holdout|latest|update|beat writer|depth chart)\b/i;

export interface Classification {
  lane: Lane;
  /** Why it routed this way, shown in the UI so the routing is never a black box. */
  rationale: string;
}

export function classify(question: string): Classification {
  const q = question.trim();

  if (NEWS_PATTERN.test(q)) {
    return {
      lane: 'news',
      rationale: 'Asks about player news or status, which is answered from ingested feed items.',
    };
  }

  const matched = matchTemplate(q);
  if (matched) {
    return {
      lane: 'export',
      rationale: `Matched the "${matched.template.id}" template, answered by computation over the exports.`,
    };
  }

  return {
    lane: 'reasoning',
    rationale: 'Matched no export template, so it goes to the reasoning lane over retrieved context.',
  };
}
