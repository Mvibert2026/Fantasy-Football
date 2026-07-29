/**
 * Cloudflare Worker for the hosted draft assistant.
 *
 * TWO JOBS, and they exist because the hosted build previously had neither.
 *
 * 1. GATE THE SITE. `CLAUDE.md` §1 says single user, and every data source this
 *    project uses -- FantasyPros, FFC, Sleeper -- permits personal use only. A
 *    public URL with no auth is the one fact that turns "personal use" into
 *    "distribution", for all three at once. HTTP Basic is used deliberately over
 *    Cloudflare Access: Access sends an email code per login, which the founder
 *    reported as both annoying and unreliable (the mail did not arrive). Basic
 *    auth is one password, remembered by the browser, with no third party in the
 *    login path and nothing to deliver.
 *
 * 2. GIVE THE ASSISTANT AN LLM IN PRODUCTION. `frontend/ui/assistant/reasoning.ts`
 *    POSTs to `/__reasoning`, which until now existed only as a Vite dev-server
 *    plugin (`frontend/server/proxy.ts`). On the hosted site that path was dead --
 *    the same class of defect as the Refresh button: a control whose backend only
 *    exists on a developer's machine. This implements the identical contract at
 *    the edge.
 *
 * THE KEY NEVER REACHES THE BROWSER. It lives in Cloudflare's secret store and is
 * read here as `env.ANTHROPIC_API_KEY`. `frontend/vite.config.ts` deliberately
 * keeps it out of the bundle (only `VITE_`-prefixed variables are exposed and
 * nothing is written into `define`); that is correct and is not changed.
 *
 * THE CONTRACT IS COPIED, NOT REDESIGNED. Request shape, response shape, the
 * system prompt and the failure vocabulary all mirror `frontend/server/proxy.ts`
 * exactly, so local and hosted behave identically. If that file changes, this one
 * has to change with it -- there is no shared module because a Worker cannot
 * import from the Vite server build.
 */

// Founder's call, 2026-07-29: "The assistant can start as a sonnet high, if I want to
// change it I will." Sonnet is the right default for a retrieval-grounded lane whose
// system prompt forbids reasoning beyond the supplied context -- the hard part is
// obedience, not capability. Change it here AND in frontend/server/proxy.ts together,
// or local and hosted answer differently.
const MODEL = 'claude-sonnet-5';
const MAX_TOKENS = 2048;

/**
 * The renderer contract, restated as a system prompt.
 *
 * SOURCE OF TRUTH IS `docs/assistant-persona.md`. This is a copy, and so is the
 * one in `frontend/server/proxy.ts`. Change all three together or local and hosted answer differently.
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
8. Be concise. Two or three sentences unless the question genuinely needs more.`;

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });

/**
 * Constant-time-ish comparison. Not a defence against a serious attacker -- this
 * is one password on a personal site behind Cloudflare's own rate limiting -- but
 * an early-exit `===` on a secret is a bad habit to write down.
 */
function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/**
 * Returns null when the request is authorised, or a 401 challenge when it is not.
 *
 * If SITE_PASSWORD is unset the site stays open. That is deliberate and stated:
 * the gate is opt-in via a secret, so deploying this Worker never silently locks
 * the founder out of his own board before he has set one.
 */
function requireAuth(request, env) {
  const expected = env.SITE_PASSWORD;
  if (!expected) return null;

  const header = request.headers.get('authorization') || '';
  if (header.startsWith('Basic ')) {
    let decoded = '';
    try {
      decoded = atob(header.slice(6));
    } catch {
      decoded = '';
    }
    const sep = decoded.indexOf(':');
    const user = sep === -1 ? '' : decoded.slice(0, sep);
    const pass = sep === -1 ? '' : decoded.slice(sep + 1);
    const userOk = !env.SITE_USERNAME || safeEqual(user, env.SITE_USERNAME);
    if (userOk && safeEqual(pass, expected)) return null;
  }

  return new Response('Authentication required.', {
    status: 401,
    headers: {
      'www-authenticate': 'Basic realm="Draft Assistant", charset="UTF-8"',
      'content-type': 'text/plain; charset=utf-8',
    },
  });
}

/**
 * Turn an upstream failure into something a person can act on. Mirrors
 * `explainUpstreamError` in the dev proxy: the user is told what they can do,
 * never handed a raw API error body.
 */
function explainUpstream(status) {
  if (status === 401 || status === 403) {
    return {
      reason: 'no_key',
      detail:
        'The reasoning lane is not configured — its API key is missing or rejected. Everything ' +
        'else on this page keeps working; it is all computed from static files.',
    };
  }
  if (status === 429) {
    return {
      reason: 'rate_limited',
      detail: 'The reasoning lane is rate limited right now. Try again in a minute.',
    };
  }
  if (status === 402) {
    return {
      reason: 'no_credit',
      detail: 'The reasoning lane has no API credit left.',
    };
  }
  return {
    reason: 'upstream_error',
    detail:
      'The reasoning lane could not be reached. Everything else on this page keeps working — ' +
      'the board, the guide, the glossary and every template query are computed locally.',
  };
}

async function handleReasoning(request, env) {
  if (request.method !== 'POST') return json({ status: 'error', reason: 'method_not_allowed' }, 405);

  const apiKey = env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    // Permanent and expected when the secret is unset, not a transient blip.
    return json({
      status: 'unavailable',
      reason: 'no_key',
      detail:
        'The reasoning lane is not configured on this deployment. Everything else on this page ' +
        'keeps working; it is all computed from static files and never touches the network.',
    });
  }

  let parsed;
  try {
    parsed = await request.json();
  } catch {
    return json({ status: 'error', reason: 'bad_request' }, 400);
  }
  if (!parsed || typeof parsed.question !== 'string' || !Array.isArray(parsed.context)) {
    return json({ status: 'error', reason: 'bad_request' }, 400);
  }

  // No context means answering from the model's own knowledge, which rule 3
  // forbids. Short-circuit before spending a call.
  if (parsed.context.length === 0) {
    return json({
      status: 'no_context',
      detail: 'Nothing in the exports matched that question, so there was nothing to reason over.',
    });
  }

  const contextBlock = parsed.context
    .map(
      (item) =>
        `- [${item.id}] (confidence: ${item.confidence}; source: ${item.source_path})\n  ${item.text}`,
    )
    .join('\n');

  let res;
  try {
    res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: MAX_TOKENS,
        system: SYSTEM,
        messages: [
          {
            role: 'user',
            content: `Retrieved context:\n${contextBlock}\n\nQuestion: ${parsed.question}`,
          },
        ],
      }),
    });
  } catch {
    return json({ status: 'unavailable', ...explainUpstream(0) });
  }

  if (!res.ok) return json({ status: 'unavailable', ...explainUpstream(res.status) });

  const message = await res.json().catch(() => null);
  if (!message) return json({ status: 'unavailable', ...explainUpstream(0) });

  // A refusal returns HTTP 200 with an empty or partial content array, so
  // stop_reason has to be checked before content is read.
  if (message.stop_reason === 'refusal') {
    return json({
      status: 'unavailable',
      reason: 'refused',
      detail: 'The model declined to answer that question.',
    });
  }

  const text = (message.content || [])
    .filter((block) => block.type === 'text')
    .map((block) => block.text)
    .join('\n')
    .trim();

  return json({
    status: 'ok',
    text,
    model: message.model,
    context_ids: parsed.context.map((item) => item.id),
  });
}

export default {
  async fetch(request, env) {
    const unauthorised = requireAuth(request, env);
    if (unauthorised) return unauthorised;

    const url = new URL(request.url);
    if (url.pathname === '/__reasoning') return handleReasoning(request, env);

    // Everything else is the static Vite build, served by the assets binding
    // with single-page-application fallback (see wrangler.jsonc).
    return env.ASSETS.fetch(request);
  },
};
