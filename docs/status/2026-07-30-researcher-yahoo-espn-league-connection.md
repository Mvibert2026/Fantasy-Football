# 2026-07-30 — researcher — Yahoo/ESPN league connection (FR-062)

**Worktree:** `.claude/worktrees/agent-abb38970ac8972f07`. **No Bash tool** — no commit, no
allocator, no `sync`. Research only; nothing built, no credential handled, no OAuth app registered.

## What was asked

FR-062, from the founder: *"what happens if I cant get a yahoo API, can I still connect through my
username and password somehow through you"* — with an explicit instruction to test the assumption
inside the question before costing the fallback.

## What was found

The assumption did not hold. Full artifact: `docs/research/yahoo-espn-league-connection-2026-07-30.md`.

| Question | Answer | Strongest tag |
|---|---|---|
| Yahoo API available to an individual today? | Self-serve registration at `developer.yahoo.com/apps/create/` is documented identically by five independent SDKs, one released 2025-09-14 | `[VERIFIED]` on the SDKs; `[GAP]` on whether a *new* app still gets scope in 2026 |
| Registration steps | Installed Application, `https://localhost:<port>`, Fantasy Sports → Read, Client ID + Secret shown immediately | `[VERIFIED]` (yfpy README, yahoofantasy PyPI) |
| League settings + scoring + **yardage bonuses**? | `stat_modifiers`, `roster_positions`, `uses_playoff_reseeding`, and a `Bonus` class carrying `points` / `target` | `[VERIFIED]` on `yfpy/models.py`; `[GAP]` on whether `bonuses` populates for football |
| **Live draft state** | Reading picks-so-far: probably yes, **n = 1 source**. Making a pick: no | `[VERIFIED]` docstring quote; `[GAP]` latency, throttling, `draft_status` value set |
| ESPN | No public API, no OAuth; cookie replay only, which Disney ToU §2.B.x names by name | `[VERIFIED]` ffscrapr "cannot be done programmatically"; `[VERIFIED — prior audit]` on the ToU |
| Password fallback | Yahoo: buys nothing OAuth doesn't. ESPN: reportedly blocked by recaptcha | `[SNIPPET]` ToS fragment; `[SECONDARY]` recaptcha |
| The clause that actually binds | 24-hour retention, storable-indefinitely set reported as GUID + token only | `[VERIFIED — prior audit]` + `[SNIPPET]` |

## Decisions taken without asking

Logged in full at the end of `docs/ideas-inbox.md`. Summary: honoured the "do not fetch Yahoo/ESPN
hosts" instruction even where it conflicted with the brief's demand to *quote* Yahoo's ToS clause,
and reported that clause as `[SNIPPET]` with the URL rather than fetching it or dropping it; did not
route around three tool refusals (`web.archive.org`, `reddit.com`/`stackoverflow.com`,
`support.fantasypros.com` 403); left the decisive registration question as an explicit `[GAP]`
rather than filling it with my prior.

## Escalations, not resolved here

1. **Public-hosting exposure now has a third source.** Yahoo's no-competing-product clause + a
   publicly-reachable draft assistant. Same fault line already open for FFC and FantasyPros. One
   ruling should cover all three. Founder call.
2. **Repo contradiction.** FR-062 says all three leagues are Yahoo or ESPN; FR-052's body carries the
   founder's own correction that they are not, while FR-052's filename slug still says otherwise.

## Left undone, and why

- **No commit, no thread.** No Bash. Handoff body staged unallocated at
  `docs/research/HANDOFF-BODY-unallocated-yahoo-league-connection-2026-07-30.md` with the exact
  allocator command. IDs are never hand-typed (043/049/053, ADR-048).
- **`FR-062` not updated.** The file does not exist inside this worktree. Its `STATUS: NEW` →
  `SCOPING` change and `## Update` section must be applied by whoever owns it, followed by
  `python tools/founder_requests.py sync`.
- **`docs/status/INDEX.md` not regenerated** — needs `python tools/status_log.py sync`.
- **`docs/CURRENT-STATE.md` deliberately not edited.** Nothing here changes measured build state, and
  a concurrent in-place edit to that file is the known collision shape. If the PM wants a Top-open-item
  for the league-connection question, it should be added by one session, once.
