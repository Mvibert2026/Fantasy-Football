/**
 * Every claim the assistant returns carries exactly one tag saying what kind of thing
 * it is. An untagged claim is a bug, and `assertTagged` is what makes that true at
 * runtime rather than by convention.
 *
 *   MODEL     -- computed from the exports. Deterministic, reproducible, cites a field
 *                path and the export run it came from.
 *   SOURCE    -- attributed to an outside publisher. Cites name, URL and timestamp,
 *                and shows its age once past the staleness window.
 *   INFERENCE -- produced by the language model over retrieved context. Never a number
 *                the model chose; only prose over facts the other lanes supplied.
 *
 * The distinction is the whole point. A user at a draft table needs to know whether a
 * sentence is arithmetic over their own board, something a reporter said, or a machine
 * rephrasing either -- those warrant very different amounts of trust.
 */

export type ClaimTag = 'MODEL' | 'SOURCE' | 'INFERENCE';

export const CLAIM_TAGS: readonly ClaimTag[] = ['MODEL', 'SOURCE', 'INFERENCE'] as const;

export interface Claim {
  readonly tag: ClaimTag;
  readonly text: string;
  /**
   * Where the claim came from, in a form the reader can check:
   *   MODEL     -- "board.json:players[12].vbd @ board@1.0.0+2026-07-25T23:03:55Z"
   *   SOURCE    -- publisher, URL and published_at
   *   INFERENCE -- the ids of the context items the model was given
   */
  readonly provenance: string;
  /** Mirrors the narration layer's confidence levels. Absent when not applicable. */
  readonly confidence?: 'high' | 'medium' | 'low';
  /** Set on SOURCE claims past the staleness window. */
  readonly age?: string;
}

export class UntaggedClaimError extends Error {}

/**
 * Validates a batch of claims before they can be rendered. Called on every answer the
 * assistant produces, from every lane -- this is the choke point the tagging guarantee
 * rests on.
 */
export function assertTagged(claims: readonly Claim[]): readonly Claim[] {
  claims.forEach((claim, i) => {
    if (!claim || typeof claim !== 'object') {
      throw new UntaggedClaimError(`Claim ${i} is not a claim object.`);
    }
    if (!CLAIM_TAGS.includes(claim.tag)) {
      throw new UntaggedClaimError(
        `Claim ${i} has tag ${JSON.stringify(claim.tag)}; expected one of ${CLAIM_TAGS.join(', ')}.`,
      );
    }
    if (!claim.text?.trim()) {
      throw new UntaggedClaimError(`Claim ${i} has no text.`);
    }
    if (!claim.provenance?.trim()) {
      throw new UntaggedClaimError(
        `Claim ${i} (${claim.tag}) has no provenance. Every claim must say where it came from.`,
      );
    }
  });
  return claims;
}

export function modelClaim(
  text: string,
  path: string,
  runId: string,
  confidence: Claim['confidence'] = 'medium',
): Claim {
  return { tag: 'MODEL', text, provenance: `${path} @ ${runId}`, confidence };
}

export function sourceClaim(
  text: string,
  publisher: string,
  url: string,
  publishedAt: string,
  age?: string,
): Claim {
  return {
    tag: 'SOURCE',
    text,
    provenance: `${publisher} — ${url} — published ${publishedAt}`,
    ...(age ? { age } : {}),
  };
}

export function inferenceClaim(text: string, contextIds: readonly string[]): Claim {
  return {
    tag: 'INFERENCE',
    text,
    provenance: `model prose over context: ${contextIds.join(', ') || 'none'}`,
  };
}
