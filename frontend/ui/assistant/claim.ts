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

/** `inferenceClaim`'s provenance prefix, matched back out by `answerSources` below --
 *  the one place both directions of that string format are defined, so they cannot
 *  drift apart. */
const INFERENCE_PREFIX = 'model prose over context: ';

/** One row in the assistant panel's "N sources" disclosure list. `id` is a class-1
 *  field path or context key (PROVENANCE-DISCLOSURE.md) -- callers must gate whether
 *  it is ever shown to the reader behind the trace-mode switch (`ui/data/traceMode.tsx`);
 *  this type only carries the data, not a visibility decision. */
export interface SourceRow {
  readonly tag: ClaimTag;
  readonly id: string;
}

/**
 * The individual sources behind a whole answer, for the per-answer "N sources"
 * disclosure (docs/design/ASSISTANT-WINDOW.md item 4). A MODEL or SOURCE claim cites
 * exactly one thing -- a field path, or a publisher -- so it contributes one row. An
 * INFERENCE claim's provenance already lists every context item the model was shown
 * for that paragraph (`model prose over context: page.a, page.b, ...`); each id
 * becomes its own row, because "3 sources" on a reasoning answer means three context
 * items informed it, not that one paragraph was produced. Deduplicated across claims
 * (the reasoning lane emits one claim per paragraph, each citing the same context
 * set) so a repeated id is counted, and listed, once.
 */
export function answerSources(claims: readonly Claim[]): readonly SourceRow[] {
  const seen = new Set<string>();
  const rows: SourceRow[] = [];
  function add(tag: ClaimTag, id: string) {
    const key = `${tag}:${id}`;
    if (seen.has(key)) return;
    seen.add(key);
    rows.push({ tag, id });
  }
  for (const claim of claims) {
    if (claim.tag === 'INFERENCE') {
      if (!claim.provenance.startsWith(INFERENCE_PREFIX)) continue;
      const list = claim.provenance.slice(INFERENCE_PREFIX.length).trim();
      if (!list || list === 'none') continue;
      for (const id of list.split(',').map((s) => s.trim()).filter(Boolean)) add('INFERENCE', id);
    } else {
      add(claim.tag, claim.provenance);
    }
  }
  return rows;
}
