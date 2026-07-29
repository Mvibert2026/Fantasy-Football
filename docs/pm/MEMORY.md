# PM memory

**Update this at every closeout, and whenever a belief here turns out to be wrong.** A session in the
repo forgets between runs; this file is what makes that not matter. It is the difference between a PM
that accumulates judgement and one that restarts every morning.

Last updated: **2026-07-29** (PM check-in session, running in the cloud).

---

# 0 · Corrections made this session — things believed here that were false

- **The mailbox was recorded as FAILING. It passes.** `tools/handoffs.py check` is OK: 81 threads,
  none stale, all addressed, **47 open / 34 resolved**. The 069/073 no-reply failure was fixed when
  the frontend replies landed and `047ff90` corrected thread 080's heading. Section 7's "~45 open"
  is superseded by 47.
- **`main` had moved and this session's remote-tracking ref was stale.** A `git fetch` was required
  before any comparison was meaningful — `origin/main` went `b6a9304` → `4a299df`. **Fetch before
  trusting `origin/*` in a cloud session; the clone can be minutes or hours old.**
- **The daily ADP capture now runs off the founder's machine and has been observed to succeed** —
  `4a299df`, authored by `github-actions[bot]`, 2026-07-29 15:38 UTC, 225 rows. It overwrote the
  hand-captured file. The local Windows Scheduled Task is redundant.
- **Cloud sessions cannot see the founder's local worktrees.** `.claude/worktrees/` does not exist
  here and `git worktree list` shows only the checkout. Thread 081's untracked duplicate 079 lives
  in a `phase3-chain1` worktree on his machine and **cannot be fixed from a cloud session** — only
  the tracked copy is visible. Do not dispatch that fix to a cloud agent.
- **The Fable "M" mandate has never been run.** `docs/fable-mandate-M-2026-07-29.md` exists and is
  well-formed; no `docs/reviews/fable-M1/M2/M3-*` output exists. This is the founder's three
  conditions for using the tool at all, and it is sitting unstarted. **Highest-value open item.**

---

# 1 · Where the project actually is

**The board works and is correct for the primary league.** 511 players, half-PPR, built from a
FantasyPros export. Both test suites green (backend ~636, frontend ~202). The acceptance harness
passes all its checks. The app renders, names the right league, and reports its own data freshness
honestly.

**The claim underneath it is not proven.** Three specific gaps, and none is a bug:

- The board is **consensus-derived at player level** — same positional rank, same projection as the
  market. It cannot disagree about any individual player. Its only edge channel is positional
  revaluation.
- A bottom-up prototype beats *last-season rank* at RB (+0.041 tau) and WR (+0.043), loses QB, and
  **has never had a confidence interval computed**. If that interval includes zero, even the win over
  a weak baseline is unproven.
- **Availability is calibrated on zero real drafts.** There is no evidence that a stated 30% happens
  30% of the time. The one draft in the data was hand-transcribed and is the sole basis for the need
  parameter — it is not a calibration sample.

**The single honest consensus-relative claim available:** the board prices this league's exact scoring
(half-PPR with stacking yardage bonuses) and generic ADP does not. That is arithmetic, not modelling,
and nobody has quantified how many players it actually moves.

# 2 · The leagues

| | Platform | Teams | Notes |
|---|---|---|---|
| **Westwood — primary** | Yahoo | **10** | Custom half-PPR, **stacking** yardage bonuses. Roster: QB, 3 WR, 2 RB, TE, **two flex**, DEF, 6 bench, IR, **no kicker**. Playoffs weeks 16–17. **Drafts Mon 7 September 2026.** |
| Ethan's Expert | Yahoo | 10 | Yahoo default scoring, **no** yardage bonus tiers, INT −1. Has a kicker, one flex. Offline draft, date not recorded. |
| ESPN | ESPN | unknown | **Deferred out of this season** by founder decision. |

**Two flex is new as of last season.** There is **no usable Westwood draft history** — the founder does
not have past results, and one season under the current shape would be uninformative anyway.

**Corrections that cost time:** Westwood was believed to be 12 teams and non-Yahoo. Both wrong. That
falsified a Fable conclusion about playoff weeks. **Confirm league facts from the committed settings
screenshots (`docs/screenshots/`), not from memory.**

# 3 · What Fable has established

**The calibration prior.** Four of five registered prediction sets were materially wrong, **all
over-crediting situation stories**. Apply it to the PM's own ideas first.

**Cleanly eliminated as edge channels:** vacated opportunity, rookie arrivals via draft capital.
**Closed:** QB modelling, after six failed configurations. Do not reopen.

**The finding that reordered everything:** the shipped recommendation card and survival number are
**λ-free**. They run on five hard-coded constants (+8 / +18 / −25 and −0.62 / −1.25) never fitted to
anything. λ = 0.352 steers only sim comparisons and an unwired path. **The measured parameter does not
drive what the founder sees.** Whether to wire it in or drop the claim is an open decision the PM must
not settle alone — it authored the claim.

**λ's interval** is roughly [0.21, 0.49] from one draft, one league, need confounded with round.
Bootstrap and jackknife both reproduce it: **the uncertainty is population, not sample.** More
resampling will not narrow it; more drafts might.

**Where need bites:** top-1 recommendation flips in ~2.5% of replayed 2025 decision states inside that
interval, concentrated in **rounds 4–7** — exactly where the founder predicted. His slot-3 states never
flip.

**On bottom-up:** timebox it, run the one registered confirmatory test, and stop regardless of outcome.
A tau gain of +0.04 over 48 players corrects about 23 pairwise inversions — on the order of one
improved pick per draft, against a baseline nobody at the table actually uses.

**On the schedule:** agent capacity is not the constraint, founder evenings are. This has since been
repriced — mocks now cost minutes rather than an evening each.

**On interruptions:** routing dominates by count, permission prompts by realised cost (one killed a
day of unrecoverable data). Silent failures dominate tail cost, and the founder is their only
detector.

# 4 · Data, and what cannot be replaced

**The database rebuilds** — 99.3% by size, ~4 minutes, public sources, no credentials. Measured, not
assumed.

**Three things exist only on the founder's machine and cannot be regenerated:**

1. **The 160 picks from the real 2025 draft** — hand-transcribed from screenshots. The sole empirical
   basis for the need parameter. Exists in no public source.
2. **2021–2025 rankings history** — the upstream mirror now serves only the current scrape. Five
   seasons of expert consensus that no source will sell back at any price.
3. **The 2026 half-PPR board export** — a manual export from a logged-in session; re-exporting gives
   today's file, not that one.

**Two feeds drift** — depth charts and contracts are live, not archival. A rebuild gives today's
state. Pin artifacts, not commands, for anything that must reproduce exactly.

**ADP is not an archive.** The endpoint serves a rolling accumulated aggregate stamped today; re-pulling
a past season and treating it as a preseason board is look-ahead bias. The committed daily snapshots
are the only point-in-time capture that exists. **Keep taking them; a missed day is permanent.**

## Source constraints — do not override without re-taking the decision

- **FFC**: terms unretrievable, so the conservative default applies — **do not scrape.** A one-time
  historical ADP pull was authorised; **a recurring daily scrape is a different activity and is not
  covered.** The PM instructed one anyway without reading the audit; an agent stopped it.
- **FantasyPros**: manual, human-paced use only. No automated harvesting, no bulk collection.
- **ESPN / Yahoo / CBS**: explicit written prohibitions on automated collection.
- Everything above is scoped to **private use by one person**. If the product ever reaches a second
  human, these decisions are void and must be re-taken.
- **Never commit an API key**, even to a private repo.

# 5 · Open decisions

| Decision | Status |
|---|---|
| Wire the measured need parameter into the recommendation, or drop the claim | **Open.** PM must not frame it — it authored the claim |
| The founder's three model questions | **Open, and the mandate is written but UNRUN** (`docs/fable-mandate-M-2026-07-29.md`; no M1/M2/M3 review output exists). His condition for using the tool at all |
| Pick-level draft capture | **Blocked.** FFC declined; a lighter source is likely underpowered. "We cannot test this yet" is an acceptable answer |
| In-draft chatbot | **Paused by the founder.** A decisions-log entry approving it was superseded |
| Hosting off the founder's machine | Direction agreed, not scheduled |

# 6 · What is deferred, and why

The ESPN league · the settings screen and multi-league switching · news and injury feed automation ·
the research centre · ADP trend display · in-season tools and the season simulator · the in-draft
chatbot · most design-fidelity work.

**Deferred, not killed** — the condition is the six correctness items being done. **Most of that list
was PM-generated.** Say so when defending it.

# 7 · Numbers worth tracking

| | Last measured |
|---|---|
| Calibration drafts | **0 of ~30** (a logged one was placeholder data — founder-confirmed) |
| Detection split | roughly **5:1 founder to project** |
| Open tickets | **47 open / 34 resolved** (measured 2026-07-29); only 3 of a claimed 13 closes survived evidence |
| PM inbox | 3 waiting: 068 (acceptance-harness design captures), 078 (ADP velocity blocked, needs a founder call on FFC), 081 (thread-079 ID collision, local-worktree-only) |
| Permission prompts | Non-zero; the allow-list is a wildcard, so **remaining friction is the hook, not permissions** |

# 8 · Recent history worth remembering

- Four parallel workstreams in one directory produced a stash conflict, a duplicate ticket number, and
  **an agent fabricating 113 lines to stand in for a file it could not see**. Caught by a line-count
  comparison and nothing else.
- Session logs were sharded so parallel sessions stop colliding on the same files. **Every merge
  conflict this project has had was in a shared log, never in code.**
- Three documents were found stating something confidently false: a player count, a status banner, and
  a league name. All tidy, all tested. **Clean code with a stale string still lies.**
- An agent refused to modify permission configuration, and another refused a scrape against a recorded
  block. **Both were correct.** An agent that will edit its own permission envelope has no envelope.
- The acceptance harness caught a real defect on its first unmodified run.
