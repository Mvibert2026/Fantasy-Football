# 2026-07-29 · researcher · competitive UX ahead of a possible frontend overhaul

**Role:** researcher (Opus, effort 4–5) · **Type:** research only, nothing built · **Shell:** none

## What was asked

The founder is weighing a major frontend overhaul and wants to know what good looks like first —
*"features of other apps out there to see if we want to include them, or looking at good UI/UX
features."* He also corrected the PM's framing: **this is a multi-league tool, three leagues at
least, and draft position must be selectable in prep** (FR-034). Four questions: what the good ones
do well (weighted toward under-the-clock, density, uncertainty, multi-league/multi-slot), what they
do badly, what exists that this project has not considered, and what to deliberately not build.

## Artifact

`docs/research/competitive-ux-2026-07-29.md` — conclusion-first, every factual claim tagged
`[VERIFIED]` / `[SNIPPET]` / `[SECONDARY]` / `[GAP]` / `[ANALYSIS]`.

## Headline

**The evidence weakens the case for an overhaul rather than strengthening it.** ESPN's 2025 redesign
is the category's cautionary case and the verbatim complaints are about density specifically
(*"so zoomed in, can barely see any of the roster"*, *"everything just blends together"*). The prior
competitive UX pass already concluded the fix here was token-level, and that work shipped. What the
evidence *does* support is a scoped structural change: league and slot as first-class selectable
state, uncertainty surfaced on the board row, and three or four on-the-clock affordances.

Three to steal: (1) publish the uncertainty already computed at the point of decision — Draft Sharks
ships 80%/95% confidence prediction limits per player plus a published MAE, ROC-AUC and calibration
plot, so the honest version is commercially survivable; (2) rehearsing from a *randomised* draft slot
as a prep loop, not a settings value; (3) modelling actual league-mates from your own league's draft
history (FantasyPros "Draft Intel") — this project holds 160 real 2025 picks and spends them only on
λ. Three to avoid: spending an overhaul on whitespace, an ambient "trending/recommended" feed (the
one feature ESPN users explicitly asked to have removed), and live platform sync (ToS-blocked here
*and* the category's most common in-draft failure).

**One correction to prior work:** thread 061 concluded *"no competitor found publishes calibration
evidence."* That needs narrowing — it holds for availability modelling, but Draft Sharks publishes
out-of-sample metrics and a reliability check for its injury model. The defensible claim is
pre-registered calibration of the *availability* model specifically, which this project still cannot
make at 1 of ~30 mocks.

## Three things that had never been considered

1. **An agent-facing MCP surface instead of an in-app chatbot.** STACKED ships a hosted, OAuth-scoped,
   read-only MCP endpoint exposing 20 tools to Claude/ChatGPT/Codex `[VERIFIED]`. This dissolves the
   hallucination trade-off that caused the LLM prose renderer to be deferred, rather than resolving
   it. Recorded as an option, explicitly **not** recommended as work — no consumer, out of Phase 1.
2. **League-mate tendency modelling from your own league's history.**
3. **The product as the *second* screen.** Every screen spec assumes this app is the screen being
   looked at. On draft day it will be beside Yahoo's draft room. Nothing in the repo addresses that.

## Decided, not escalated

- **Did not halt on the premise, but recorded three challenges** (§0.5 of the artifact): the thread
  061 audit is in `docs/research/`, not `docs/reviews/`; a frontend overhaul sits outside written
  Phase 1 scope per `CLAUDE.md` §2/§8 and needs a spec amendment rather than a sprint; multi-league is
  *not* a contradiction with §1 because one founder with three leagues is still one user.
- **Escalating, and it is the reason this dispatch was partly unavoidable rework:** the prior
  **competitive UX research artifact does not exist in this repository.** `docs/operating-model.md`'s
  budget table logs the pass as completed and verified, and at least six live documents cite its
  conclusions (`design-handoff/HANDOFF-NOTES.md`, `design-handoff/README.md` Addendum 3,
  `handoffs/030`, `handoffs/047`, `adr-drafts/ADR-A`, `screenshot-checklist.html`). I searched the
  whole tree including every agent worktree. Its conclusions survive only as paraphrase inside the
  documents that consumed them. **This project has now bought the same research twice.**
- **Honoured every recorded block rather than routing around it.** `www.reddit.com` was refused by the
  tool outright and is the single largest hole in the voice-of-customer section — recorded, not
  worked around. ESPN/Yahoo/CBS not attempted. `forums.footballguys.com` and `www.fantasylife.com`
  both had relevant material surface in search and were left unfetched to stay consistent with the
  blocks recorded in thread 009 and the Yahoo audit, even though `fantasylife.com/articles/` is not
  robots-disallowed. Flagging that path-level loophole rather than exploiting it alone.
- **Refused to convert a `[GAP]` into a number** in three places: the visual form of Boris Chen's
  tier charts (output is a PNG my tools cannot read), what a BeerSheet contains (page carries only
  download links), and whether any user anywhere has asked for uncertainty display (every search
  returned vendor marketing). That last one is flagged in the artifact as the gap that would most
  change the confidence of the headline recommendation.
- **Flagged sample quality as the main caveat, including where it agreed with us.** Five of the
  richest sources are vendors describing their own products; the best competitor comparison is
  written by a competitor; the App Store review sets are curated by Apple and skew positive. And the
  ESPN density finding is exactly what this repo already believed — I went looking for it and found
  it, and did not look as hard for a disconfirming source.

## Not done — no shell in this session

This container has no Bash tool, so `python tools/handoffs.py new` and
`python tools/founder_requests.py new` could not be run. Hand-typing an ID is refused (threads
043/049/053, ADR-048). Two bodies are staged with their exact allocator commands:

- `docs/research/HANDOFF-BODY-unallocated-competitive-ux-2026-07-29.md` (researcher → pm, frontend)
- `docs/founder-requests/NEW-look-at-other-apps-ux-before-committing-to-an-overhaul.md`

Also not run: `python tools/status_log.py sync` to regenerate `docs/status/INDEX.md`, and
`python tools/state.py --apply`. `docs/CURRENT-STATE.md` was **not** edited — nothing in this
session changed build state, and this is research, not a state change.

## Fourth session to report it

`docs/ideas-inbox.md` still carries unresolved merge-conflict markers (`<<<<<<< HEAD`, `=======`,
`>>>>>>>`) around the strategist PR-004 and backend ADR-057/ADR-059 entries. Both sides look like
real work. I appended below them without touching either side. Three prior sessions reported the same
thing.
