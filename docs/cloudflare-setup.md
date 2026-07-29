# Cloudflare setup — the assistant's API key, and the password gate

Written for the founder, 2026-07-29. Both changes are settings in the Cloudflare dashboard. **No code
to write and no deploy to trigger** — `worker/index.js` and `wrangler.jsonc` are already on `main`.

Two secrets. The site behaves differently depending on which are set, and it never breaks if you set
neither:

| Secret | What it does | If you leave it unset |
|---|---|---|
| `ANTHROPIC_API_KEY` | The assistant can call an LLM | Assistant says the reasoning lane isn't configured. Everything else works |
| `SITE_PASSWORD` | Browser asks for a password before the site loads | Site stays public, exactly as now |
| `SITE_USERNAME` | Optional. Sets which username is accepted | Any username works; only the password is checked |

---

## 1 · The assistant's API key

You need an Anthropic API key first — **console.anthropic.com** → API keys → Create key. It starts
`sk-ant-`. Copy it when it's shown; it isn't shown again.

Then:

1. **dash.cloudflare.com** → **Workers & Pages** → **fantasy-football**
2. **Settings** tab
3. **Variables and Secrets** → **Add**
4. Type: **Secret** (not Text — Secret hides the value and keeps it out of logs)
5. Name: `ANTHROPIC_API_KEY`
6. Value: paste the key
7. **Save**, then **Deploy** if it offers

**Type must be Secret, not Text.** Text variables are visible in the dashboard afterwards.

The key never reaches the browser. It's read inside the Worker, which runs on Cloudflare's servers.

## 2 · The password gate

1. Same place: **Settings** → **Variables and Secrets** → **Add**
2. Type: **Secret**
3. Name: `SITE_PASSWORD`
4. Value: whatever you want the password to be
5. **Save** and deploy

Now visiting the site pops the browser's own login box. **Leave the username blank** unless you also
set `SITE_USERNAME` — only the password is checked. Your browser will offer to remember it, so it's
one prompt per device rather than per visit.

This is deliberately not Cloudflare Access. Access emails a code every login, which you found
annoying and which didn't reliably arrive. This has no email in the path and nothing to deliver.

**To turn the gate off:** delete `SITE_PASSWORD`. The site goes public again immediately.

## 2b · One thing that had to change in the code (already done)

The founder asked whether setting the password alone was actually enough. **It was not, and the
instinct was right.**

By default Cloudflare serves a matching static file straight from the edge and never runs the Worker
— faster, and it skips the password check entirely. `index.html`, the JavaScript bundle and every
board JSON would have stayed publicly readable no matter what `SITE_PASSWORD` was set to. Only
`/__reasoning`, which is not a file, would have been gated.

Fixed by `run_worker_first: true` in `wrangler.jsonc`, which forces every request through the script
before any file is served. Already committed and deployed; nothing for you to do.

## 2c · How agents get in

The live site is gated. Agents that need to test it — screenshots, endpoint checks, verifying a
deploy — need the password, and the founder has instructed that they get it.

**It is passed in the dispatch prompt, never written to a file.** Not here, not in
`.claude/agents/*.md`, not in a test fixture, not in an env file that might be committed. This repo
is on GitHub; anything written down is published.

- **Username: blank.** `SITE_USERNAME` is unset, so only the password is checked.
- `curl -u ":<password>" https://draft.maplerock.net/...`
- In Playwright: `browser.newContext({ httpCredentials: { username: '', password: '<password>' } })`

**If you are an agent and you were not given it, ask — do not guess and do not go looking for it in
the repo.** It is not there by design.

## 3 · Checking it worked

- **Password:** open the site in a private window. A login box means it's on. **Then check a file
  directly** — `draft.maplerock.net/data/board.json`. It must also ask for the password. If the page
  is gated but that file loads, the gate is cosmetic and the data is still public.
- **Assistant:** ask it something the templates can't answer. "Not configured" means the key isn't
  set or was saved as Text rather than Secret.
- **Neither should affect the board.** Every other screen is computed from static files and doesn't
  touch the network. If the board breaks, that isn't these settings.

## 4 · What it costs

The assistant calls Sonnet, capped at 2,048 tokens per answer. A question is fractions of a cent.
Only the reasoning lane spends anything — every template answer and every number on the board is
computed locally and costs nothing.

Anthropic's console has spend limits under **Billing** if you want a ceiling.

---

## Why the password matters beyond privacy

Every data source this project uses — FantasyPros, FFC, Sleeper — permits **personal use only**. FFC's
permission says in its own text that it is void if the product reaches a second human.

A public URL with no gate is the single fact that turns "personal use" into "distribution", for all
three at once. The founder's decision to proceed on personal-use terms (FR-056) rests on this being
set.
