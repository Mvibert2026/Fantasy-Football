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
 * The renderer contract from docs/data-contract.md, restated as a system prompt.
 *
 * This is a second line of defence, not the first. The first is that the request
 * body carries only retrieved context -- the model is never handed the exports, the
 * repo, or the docs. It cannot cite a number it was not given.
 */
const SYSTEM = `You answer questions about one fantasy football draft board using ONLY the retrieved context supplied in the user message.

Binding rules:
1. Every claim you make must be traceable to exactly one item in the retrieved context.
2. You may reword a context item. You may not introduce any claim, comparison, cause, prediction, or recommendation that is not already present in one.
3. If the retrieved context does not answer the question, say so plainly and stop. Do not fall back on your own football knowledge. You have none that applies here: this board is proprietary and its numbers are not public.
4. Never state a number that does not appear verbatim in the retrieved context.
5. Respect the confidence level attached to each context item. An item marked "low" must not be phrased as assertively as one marked "high".
6. Be concise. Two or three sentences unless the question genuinely needs more.`;

type ReasoningRequest = {
  question: string;
  context: Array<{ id: string; text: string; confidence: string; source_path: string }>;
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
            messages: [
              {
                role: 'user',
                content: `Retrieved context:\n${contextBlock}\n\nQuestion: ${parsed.question}`,
              },
            ],
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
