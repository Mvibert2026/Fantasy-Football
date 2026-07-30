import type { Plugin, ViteDevServer } from 'vite';
import type { IncomingMessage, ServerResponse } from 'node:http';

/**
 * Reasoning-lane proxy, mounted inside the Vite dev server.
 *
 * The API key lives only in this process. The client posts retrieved context here
 * and receives prose back; it never sees, and cannot ask for, the credential.
 *
 * The absence of a key is a permanent, first-class state, not a placeholder. So are
 * proxy-down and offline. In all three cases this endpoint (or its absence) resolves
 * to a clear "reasoning unavailable" answer, and every other lane keeps working --
 * the export-query lane is local computation over static JSON and never touches the
 * network at all.
 */

export const REASONING_ENDPOINT = '/__reasoning';

/** The single model. No tier routing: not worth the failure mode at this volume. */
// Founder's call, 2026-07-29: start the assistant on Sonnet. Kept in step with
// worker/index.js, which serves the same lane on the hosted site.
const MODEL = 'claude-sonnet-5';
const MAX_TOKENS = 2048;

/**
 * The renderer contract, restated as a system prompt.
 *
 * SOURCE OF TRUTH IS `docs/assistant-persona.md`. This is a copy, and so is the
 * one in `worker/index.js`. Change all three together or local and hosted answer differently.
 *
 * Rules 1-4 are the safety floor: the model is handed only retrieved context,
 * never the exports or the repo, so it cannot cite a number it was not given.
 * Rules 5-8 are the founder's own voice, added 2026-07-29 -- rule 5's second
 * sentence is the one doing the real work, because an uncertainty stated as a
 * trailing caveat is an uncertainty the reader skips.
 */
const SYSTEM = `You answer questions about one fantasy football draft board using ONLY the retrieved context supplied in the user message.

Binding rules:
1. Every claim you make must be traceable to exactly one item in the retrieved context.
2. You may reword a context item. You may not introduce any claim, comparison, cause, prediction, or recommendation that is not already present in one.
3. If the retrieved context does not answer the question, say so plainly and stop. Do not fall back on your own football knowledge. You have none that applies here: this board is proprietary and its numbers are not public.
4. Never state a number that does not appear verbatim in the retrieved context.
5. Respect the confidence level attached to each context item. An item marked "low" must not be phrased as assertively as one marked "high". Where an item carries an interval, a sample size or a status of "exploratory", say so in the same sentence as the claim -- never as a trailing caveat.
6. Answer the question that was asked. Lead with the answer, then what it is made of.
7. Prefer plain words to the project's internal vocabulary. The reader is not a developer.
8. Be concise. Two or three sentences unless the question genuinely needs more.
9. Earlier turns in this conversation, if any, are for continuity only -- so "he", "that pick", "the other one" can resolve to something said earlier. They are never a source of facts. Every claim in THIS answer must still be traceable to an item in THIS turn's retrieved context, exactly as rules 1-4 require, even when a prior turn discussed the same player or number.`;

type ReasoningRequest = {
  question: string;
  context: Array<{ id: string; text: string; confidence: string; source_path: string }>;
  /** FR-077: prior turns in this dock session, oldest first, so a follow-up
   *  question can carry a referent from the conversation. Bounded client-side
   *  (ui/assistant/reasoning.ts's boundHistory) before it ever reaches here. */
  history?: Array<{ question: string; answerText: string }>;
};

function json(res: ServerResponse, status: number, body: unknown) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json');
  res.end(JSON.stringify(body));
}

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk as Buffer);
  return Buffer.concat(chunks).toString('utf8');
}

/**
 * Turns an upstream failure into something a person can act on.
 *
 * Every branch says the same two things: the reasoning lane is off, and nothing else
 * is affected. What changes is the remedy, which is the only part the user needs.
 */
function explainUpstreamError(err: unknown): { reason: string; detail: string } {
  const raw = err instanceof Error ? err.message : String(err);
  const status = (err as { status?: number })?.status;
  const suffix =
    ' Everything else on the page is unaffected — the board, the guide, the glossary and ' +
    'every template query are computed locally from static files.';

  if (/credit balance is too low/i.test(raw)) {
    return {
      reason: 'no_credit',
      detail:
        'The Anthropic account has no credit, so the reasoning lane cannot run. The API key ' +
        'itself is valid — this request authenticated and was rejected at billing. Add credit ' +
        'and the lane works with no code change.' + suffix,
    };
  }
  if (status === 401 || /authentication_error|invalid x-api-key/i.test(raw)) {
    return {
      reason: 'bad_key',
      detail:
        'The Anthropic API rejected the key. Check ANTHROPIC_API_KEY in the worktree .env, ' +
        'then restart the dev server so it is re-read.' + suffix,
    };
  }
  if (status === 429 || /rate_limit/i.test(raw)) {
    return {
      reason: 'rate_limited',
      detail: 'The Anthropic API is rate-limiting this key. Wait and retry.' + suffix,
    };
  }
  if (status !== undefined && status >= 500) {
    return {
      reason: 'upstream_down',
      detail: 'The Anthropic API returned a server error. Retry shortly.' + suffix,
    };
  }
  if (/ENOTFOUND|ECONNREFUSED|fetch failed|network/i.test(raw)) {
    return {
      reason: 'offline',
      detail: 'The Anthropic API could not be reached — this machine appears to be offline.' + suffix,
    };
  }
  return {
    reason: 'upstream_error',
    detail: 'The reasoning lane could not complete the request.' + suffix,
  };
}

/**
 * FR-077: turns prior Q/A pairs into alternating user/assistant messages ahead
 * of the current turn, so the model can resolve a follow-up's referents ("what
 * about him") without those prior turns ever being treated as retrieved
 * context -- rule 9 above states that constraint to the model directly; this
 * function is what makes the shape of the request match it (history messages
 * carry no context block, only the current turn does).
 */
function buildMessages(
  parsed: ReasoningRequest,
  contextBlock: string,
): Array<{ role: 'user' | 'assistant'; content: string }> {
  const messages: Array<{ role: 'user' | 'assistant'; content: string }> = [];
  for (const turn of parsed.history ?? []) {
    if (!turn.question?.trim() || !turn.answerText?.trim()) continue;
    messages.push({ role: 'user', content: turn.question });
    messages.push({ role: 'assistant', content: turn.answerText });
  }
  messages.push({
    role: 'user',
    content: `Retrieved context:\n${contextBlock}\n\nQuestion: ${parsed.question}`,
  });
  return messages;
}

export function reasoningProxy(apiKey: string | undefined): Plugin {
  return {
    name: 'prep-reasoning-proxy',
    configureServer(server: ViteDevServer) {
      server.middlewares.use(REASONING_ENDPOINT, async (req, res) => {
        if (req.method !== 'POST') {
          json(res, 405, { status: 'error', reason: 'method_not_allowed' });
          return;
        }

        // Permanent state, not a placeholder: no key configured.
        if (!apiKey) {
          json(res, 200, {
            status: 'unavailable',
            reason: 'no_key',
            detail:
              'No ANTHROPIC_API_KEY is configured. The reasoning lane is off. Board queries, ' +
              'the guide, the glossary and the methodology notes are unaffected -- they are ' +
              'computed locally from the exports and never call the network.',
          });
          return;
        }

        let parsed: ReasoningRequest;
        try {
          parsed = JSON.parse(await readBody(req));
        } catch {
          json(res, 400, { status: 'error', reason: 'bad_request' });
          return;
        }

        if (!parsed.question || !Array.isArray(parsed.context)) {
          json(res, 400, { status: 'error', reason: 'bad_request' });
          return;
        }

        // No context retrieved means nothing to reason over. Answering anyway would be
        // answering from the model's own knowledge, which rule 3 forbids -- so short-circuit
        // here rather than spending a request to be told the same thing.
        if (parsed.context.length === 0) {
          json(res, 200, {
            status: 'no_context',
            detail: 'Nothing in the exports matched that question, so there was nothing to reason over.',
          });
          return;
        }

        const contextBlock = parsed.context
          .map(
            (item) =>
              `- [${item.id}] (confidence: ${item.confidence}; source: ${item.source_path})\n  ${item.text}`,
          )
          .join('\n');

        try {
          const { default: Anthropic } = await import('@anthropic-ai/sdk');
          const client = new Anthropic({ apiKey });

          const message = await client.messages.create({
            model: MODEL,
            max_tokens: MAX_TOKENS,
            system: SYSTEM,
            messages: buildMessages(parsed, contextBlock),
          });

          // A refusal returns HTTP 200 with an empty or partial content array, so
          // stop_reason has to be checked before content is read.
          if (message.stop_reason === 'refusal') {
            json(res, 200, {
              status: 'unavailable',
              reason: 'refused',
              detail: 'The model declined to answer that question.',
            });
            return;
          }

          const text = message.content
            .filter((block): block is { type: 'text'; text: string; citations: null } =>
              block.type === 'text',
            )
            .map((block) => block.text)
            .join('\n')
            .trim();

          json(res, 200, {
            status: 'ok',
            text,
            model: message.model,
            context_ids: parsed.context.map((item) => item.id),
          });
        } catch (err) {
          // Offline, rate-limited, bad key, no credit, API down -- the lane is
          // unavailable and everything else still works. What differs is what the user
          // can do about it, so say that in plain language rather than forwarding a raw
          // API error body to the screen.
          const { reason, detail } = explainUpstreamError(err);
          json(res, 200, {
            status: 'unavailable',
            reason,
            detail,
            // Kept separate so the UI can show the plain message and still make the
            // underlying error available for debugging.
            technical: err instanceof Error ? err.message : String(err),
          });
        }
      });
    },
  };
}
