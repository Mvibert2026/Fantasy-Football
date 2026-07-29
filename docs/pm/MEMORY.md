# PM memory

**Update this at every closeout, and whenever a belief here turns out to be wrong.** A session in the
repo forgets between runs; this file is what makes that not matter. It is the difference between a PM
that accumulates judgement and one that restarts every morning.

Last updated: **2026-07-29** (second PM session that day — the in-repo PM taking over from the
outside-the-repo one, running in the cloud).

---

# 0 · Corrections made this session — things believed here that were false

**THE APP IS ONLINE. 2026-07-29.** `https://fantasy-football.soft-water-e755.workers.dev`, a
Cloudflare Worker serving the static Vite build from `main`, rebuilding itself on every push.
**Founder confirmed it working in his own browser** — the only evidence standard this project
accepts for a screen. Verified independently too: `/data/board.json` serves `contract_version
1.14.0` with Bijan Robinson at the top, so it is today's build and not a stale shell.
`maplerock.net` is on Cloudflare DNS (nameservers `ashley`/`margo`) with the custom domain added;
it had not answered yet when this was written — certificate issuance, expected to resolve on its
own. Config is `wrangler.jsonc` at the repo root. **Cloudflare holds its own deploy token; no
credential is in this repo.** The site is **public by the founder's explicit choice** — the trade
was stated to him (nine league mates could read his board) and he chose public for now. Cloudflare
Access can gate it for free in about ten minutes without touching the build.

**This closes the last dependency on his machine.** Development, tests, the database rebuild, the
daily capture, and now *viewing the app* all run without it.

**OPEN, founder-decided, needs following up:** the live site is **public without a password**, and
every source authorisation this project holds — FFC (FR-023), FantasyPros (D-020), the FFC history
pull (D-021) — is scoped *"private use by one person, void if the product ever reaches a second
human."* The founder was told, judged the risk low while it is only his own board on an obscure URL,
and **chose to leave it open for a day or two because it makes his own testing easier** (2026-07-29).
That is his call and it is a reasonable one.

**Do not let it drift.** He said he will add the password himself in the next day or two. If it is
still open after that, raise it once — not as a lecture, as a reminder he asked for. The gate is
free, takes about ten minutes, and the application already exists in Cloudflare Access with no policy
attached. **Related defect he hit while trying: an Access application with no policy denies everyone**,
which is why the email code appeared to fail.

**New founder constraints, learned the expensive way:**

- **Fable work happens at the END OF THE WEEK, before the budget reset. Never mid-week.** Fable runs
  on a separate weekly budget the founder spends deliberately. This PM dispatched all three M
  mandates on a Wednesday and he stopped them. **Write mandates as the questions arise; queue them;
  run the queue at the end of the week.** Now recorded in `ROLE.md` under Managing Fable.
- **FFC is UNBLOCKED.** The founder asked them directly: *"we have no blocks from FFC, we can use as
  needed."* This supersedes the conservative-default block in §4 below, in
  `docs/research/source-audit-2026-07.md`, and in every thread that cites it (055, 057, 062, 064,
  078). It is broader than the earlier one-time-historical-pull authorisation — recurring use is
  covered. Standing caveat unchanged: scoped to private use by one person, void if a second human
  ever uses the product. Still rate-limit and cache; permission is not licence to hammer a hobby
  endpoint.

**PM defects committed this session — read these before running parallel chains:**

- **The PM manufactured a phantom collision, twice.** A repo stop-hook requires a clean tree at the
  end of every turn; background agents share the PM's working directory; satisfying the hook with
  `git add -A` swept two running chains' in-flight files into PM commits. The first passed unnoticed
  (a frontend revert landed under a docs commit message). The second cost a full decision cycle: the
  data-ops chain saw its own files under another agent's commit message, concluded a parallel chain
  was duplicating its work, and halted to escalate. Verified afterwards with `git diff HEAD` —
  **byte-identical, 609 lines, nothing to reconcile.** Rules now in `PLAYBOOK.md` ("Committing while
  agents are running"), and every agent definition carries a section telling it what this looks like
  and not to halt. **Never stage a path you did not write.**
- **The worktree rewrite was an overcorrection.** This session's charter edit declared worktree
  discipline obsolete in the cloud. Half right — worktrees isolated the *database* and the *dev
  server* locally, and those reasons are gone. The *concurrent-write* reason was not; it moved from
  session level to agent level, and removing the discipline without noticing caused the defect above
  within hours. Corrected in `CHARTER.md` rule 2.
- **A dispatch that misreads scope is the most expensive error available to the PM** — more than
  choosing the wrong model tier. "Optimize all for phone viewing right now" was read as *build
  responsive layouts* and dispatched as engineering; roughly a third of the single largest agent run
  on record (~374k tokens) went on work the founder cancelled once he saw the scope implied.
  **"Right now" is about urgency, not scope.**

**Latent numbering collision, not yet a problem:** `docs/decisions.md` has exactly one ADR-054 (the
FFC ingester, this session) and the allocator says next is 55. But `CURRENT-STATE.md` records
ADR-054 as belonging to the unmerged, unreviewed `backend/mock-calibration-kickers` branch. **When
that branch merges, two ADR-054s meet.** Same structural cause as thread 081 and the 043/049/053
collisions: the allocator only sees its own working tree.

**Things this memory and `CURRENT-STATE.md` asserted that turned out false:**

- **The ADP capture has NEVER run on schedule.** The previous entry said the cloud capture "has been
  observed to succeed" and that the Windows Scheduled Task was redundant. Measured via the Actions
  API: **exactly one run exists, `event: workflow_dispatch`, triggered by the founder by hand at
  15:38 UTC.** The 09:15 UTC cron has never fired. **Do not tell him to disable the Windows task
  until a `schedule`-triggered run succeeds.** Re-check with a `list_workflow_runs` call filtered on
  `event: schedule` — the run's *author* being `github-actions[bot]` does not distinguish a manual
  dispatch from a scheduled one, which is exactly how the previous session got this wrong.
- **The `PreToolUse` hook was already inert in cloud sessions** — it was registered with a Windows
  conda interpreter path that does not exist in a Linux container, so it silently never ran. "Zero
  approvals" was true here **by accident, not by design**, which is worse than either extreme
  because nothing announced it.
- **`docs/pm/HANDOFF.md` was not in the repo.** The founder had to upload it. Now committed at
  `docs/pm/HANDOFF.md` so the next PM does not repeat the search.

**Still true from the earlier session, re-verified:**

- The mailbox passes: 81 threads, none stale, **47 open / 34 resolved**. Section 7's "~45 open" is
  superseded by 47.
- **Fetch before trusting `origin/*` in a cloud session** — the clone can be hours old. `origin/main`
  moved `4a299df` → `a617611` mid-session.
- **Cloud sessions cannot see the founder's local worktrees.** Thread 081's untracked duplicate 079
  lives in a worktree on his machine and **cannot be fixed from the cloud.** Do not dispatch it.
- **The Fable "M" mandate is still unrun** — and per the timing constraint above, that is now
  correct rather than a gap. Run it at the end of the week.

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

**A full clean-clone rehearsal was run in a cold cloud container on 2026-07-29** (branch
`claude/cloud-path-rehearsal-kafx7m`, commit `6c23c13`). Clone → rebuild → both suites green in
**~8m50s with zero credentials and zero environment variables**: backend **641 passed / 8 skipped /
0 failed**, frontend **202 passed / 0 failed**, database 22 tables / 2,856,629 rows / 854.4 MB. The
three rescued artifacts did their job — nothing that exists only on his machine was needed.

**Corrected by that rehearsal — the previous entry here was wrong:**

- **The 2021–2025 rankings history re-pulls.** This memory said five seasons "no source will sell back
  at any price," and `can-we-rebuild-the-database.md` cited it as blocking cloud migration. Measured:
  `ingest_rankings.py` unmodified against an empty database returned all six seasons in 4.3s, and a
  row-level diff of **2,540 rows across all 14 data columns against the committed rescue CSV found
  zero differing fields and zero missing keys either way.** An earlier session tested this with the
  ingester's `resolve_snapshot_date` and concluded the opposite. **Two honest measurements disagree**
  — either the mirror changed between them or the earlier method was wrong; it was not worth settling.
  Either way the mirror is live and can change again, so **keep the rescue CSV as a pin** — but note
  nothing currently loads it back into the database, so the pin cannot actually be used yet.
- **The remaining genuinely unrestorable artifact is the ADP snapshots, and it is a code gap, not a
  source gap.** `ingest_mfl_adp.py` writes the canonical CSV but **cannot read one back** — there is
  no CSV→DB loader. The committed point-in-time rows are therefore unrestorable and a rebuild gets
  only the current day. Its own docstring calls the CSV canonical and the DB a cache of it, and no
  code can rebuild that cache. **This gap widens by one snapshot every day.** Highest-value fix on
  the data side; dispatched 2026-07-29.

**Still exists only on his machine and cannot be regenerated:**

1. **The 160 picks from the real 2025 draft** — hand-transcribed from screenshots, the sole empirical
   basis for the need parameter. Committed as a fixture (thread 080); a restore path exists.
2. **The 2026 half-PPR board export** — a manual export from a logged-in session; re-exporting gives
   today's file, not that one. Committed; a restore path exists.

**Two things block a fresh machine at the first command, both one-line fixes** (dispatched): `pandas`
is missing from `requirements.txt` despite 15 `src/` modules importing it — pytest collection aborts
and *zero* tests run; and no Python version is declared anywhere, while `scipy==1.18.0` needs ≥3.12.

**`tools/state.py --tests` hard-crashes off Windows** — it hardcodes the founder's conda interpreter.
That is the *mandated* `CURRENT-STATE.md` write-back, broken in every cloud session. Fix dispatched.
`handoffs.py`, `status_log.py` and `founder_requests.py` all work fine.

**`github.com/dynastyprocess/*` returns 403 in any Claude session** — session repo-scoping, and
`add_repo` cannot cross owners. `raw.githubusercontent.com` serves the identical file. This affects
Claude sessions only; a normal machine and GitHub Actions never see it. **Never commit a base-URL
change to work around it** — that would break the environments that actually run the capture.

**Two feeds drift** — depth charts and contracts are live, not archival. A rebuild gives today's
state. Pin artifacts, not commands, for anything that must reproduce exactly.

**ADP is not an archive.** The endpoint serves a rolling accumulated aggregate stamped today; re-pulling
a past season and treating it as a preseason board is look-ahead bias. The committed daily snapshots
are the only point-in-time capture that exists. **Keep taking them; a missed day is permanent.**

**What the daily capture actually asks for** (checked 2026-07-29, `src/ingest_mfl_adp.py` defaults,
mirrored in `tools/ci_adp_snapshot.py`): `FCOUNT=10` (ten-team leagues — matches Westwood exactly),
`IS_PPR=1`, `IS_MOCK=0` (real drafts, not mocks), `IS_KEEPER=0`, `CUTOFF=10`, `PERIOD=2026`.

**The one imperfection, and it is not fixable at the source:** Westwood is **half**-PPR, and MFL's
flag is binary — there is no half-PPR option on that endpoint. Full PPR is the nearer of the two
available settings, so the current default is the right call. **But it is an approximation nobody
wrote down**, and receivers come off the board earlier in full PPR than in half, so the captured
market is slightly receiver-forward relative to his league. Anything learning drafter behaviour from
these snapshots inherits that tilt. Do not silently treat the capture as format-matched.

## Source constraints — do not override without re-taking the decision

- **FFC**: **UNBLOCKED 2026-07-29.** The founder asked them directly and reported no restrictions —
  *"we have no blocks from FFC, we can use as needed."* Recurring use is covered, not just the
  earlier one-time historical pull. Rate-limit and cache anyway. **The old entry read "terms
  unretrievable, conservative default, do not scrape" and every FFC-blocked thread cites it —
  those threads are now actionable.** Historical note kept because it explains an agent's past
  refusal: the PM once instructed an FFC scrape without reading the audit, and an agent correctly
  stopped it. That refusal was right *at the time*.
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
| Pick-level draft capture | **Unblocked 2026-07-29** — FFC is available (see §4). MFL genuinely cannot supply per-pick data (needs a league ID we do not hold), so FFC is the route. Not yet scoped or built |
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

# 9 · 2026-07-29, second half — decisions that must survive this session

**Two tracks, not one product (FR-042).** Westwood is the custom case: verified scoring, real
opponent knowledge. Everything else is generic — standard scoring varying PPR only, no opponent
identity, no tendency modelling. This is a founder ruling, not a proposal. It supersedes part of
ADR-047.

**Presets currently carry Westwood's ruleset and are labelled as platform defaults.**
`src/generate_config_matrix.py:71-74` deep-copies `LEAGUE` and swaps only the reception value. The
file's own docstring contradicts itself on whether ESPN scoring was ever verified (lines 6-11 say
confirmed, lines 52-53 say bot-detection blocked the fetch). **Regenerate, do not edit** — this
invalidates projections in all 24 preset exports. Sequence it *before* the custom-league builder, or
the builder inherits the bug into every league the founder creates.

**The custom-league backend already exists.** `src/league_builder.py` —
`create_league(...)` / `create_and_export_league(...)`. Found by accident. **This triggered FR-043**
(audit for built-but-unused capability) and it is the single best argument for running that audit
before any build planning.

**The static deploy splits "custom league" in two.** `board.json` ships `projected_points` and `vbd`
but **no component stats**. So team count, roster shape, draft slot and playoff structure can be
recomputed in the browser; anything touching scoring cannot. **Rule: the settings screen must never
accept a setting it cannot apply.**

**Design direction is temporarily reversed (founder instruction).** The built app is the reference;
design catches up to code until parity, then we hold until an overhaul is scheduled. Exception: a new
feature needing visibility before the overhaul still gets specced up front. Briefing addendum is in
`docs/design-briefing-2026-07-29.md` §7-12.

**The overhaul case is weaker than assumed.** `docs/research/competitive-ux-2026-07-29.md` (thread
086). Also: the 5/10 visual-polish and 4/10 light-mode scores cited in six live documents trace to a
research artifact **that is not in the repository**. Treat them as unsourced.

**Six present-but-inert controls (FR-037)**, not one. Export CSV, Export PDF, League settings,
Compare, Ask, Ask-the-assistant. The founder is finding them by clicking. One design treatment covers
all six; it is the cheapest high-value design deliverable available.

**Non-primary leagues are thinner than anyone said.** Primary carries 11 export artifacts; the 26
sub-leagues carry 7. Missing everywhere: `strategies.json`, `player_descriptions.json`,
`season_stats.json`, `weekly_finishes.json`. **The Strategy guide is empty in 26 of 27 leagues.**

**TE is the ranking finding with legs.** 33.6% of a tight end's stable quality is unpriced by
consensus, against 15.1% RB/WR and 6.3% QB. The founder's addition — that it is only spendable in
the late rounds if you are not taking TE or QB early — is the right question and **is not yet
answered**. If the mispricing concentrates in the top few TEs, the finding argues the opposite way.
Survivorship is the specific way that analysis fails.

**Correct the 98% goal when it recurs.** That figure came from fitting a curve to *realised* finish
— hindsight, not prediction. 12.5% of scoring variance is pure weekly noise and availability is
near-unforecastable (r = 0.09-0.18). The achievable goal is not out-predicting experts; it is
rankings computed for his scoring, roster and draft slot, which consensus can never do.

## Operating lessons from this session

- **The shell working directory persists between Bash calls.** A `cd` into a worktree silently
  changes the target of every later command. Verify with `pwd` before trusting a `git status`.
- **When the API throws 500s, stop resuming and start preserving.** Commit each agent's worktree as
  an explicit `WIP (pm-preserved)` commit, labelled as *not* agent-verified, then probe with **one**
  agent rather than retrying all of them. Five agents died in ~15 minutes; every blind retry cost
  tokens and produced nothing.
- **Tell interrupted agents to commit after each step, not at the end.** Correct only under
  instability, and it is correct then.
- **Screens can be data-driven and still stale.** Methodology and Glossary auto-update their numbers
  and were still missing ADP entirely. "It reads from the export" is not the same as "it is current."
