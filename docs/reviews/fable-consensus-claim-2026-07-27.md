# Is "beating consensus is unclaimable until ~2029" correct? — 2026-07-27 (Priority 2C)

**Verdict: the claim is wrong as stated, in three separable ways — the 2029 figure is a moot
artifact of a deleted parameter, the correct floor under the project's own conventions is ~2028
and was already derived once and then lost, and, most materially, "unclaimable" is being used to
mean "undecidable," which conflates a publication-grade claim with a private drafting decision.
The underlying inference stance (season as the resampling unit, no p-values at n=4) survives my
attack; the roadmap consequence drawn from it does not.**

---

## 1 · Where the number comes from, and which number is actually on record

The repo carries **two** figures with different provenance, currently marked "CONTESTED" in
`CURRENT-STATE.md:87-94`:

- **~2029** — `ADR-A-need-adjustment-scale.md:50`: Benjamini-Hochberg at 0.05 across a
  **14-test family** under the sign-test floor requires `(1/2)^n × 14 ≤ 0.05`, i.e. n ≥ 9 usable
  seasons; 2021+9 → 2029. The arithmetic is correct ((1/2)^9×14 ≈ 0.027; n=8 gives 0.055).
  **But the 14-test family existed to sweep `NEED_ADJUSTMENT_SCALE`, and D-001 (settled
  2026-07-27) deleted that parameter outright** (`decisions-needed.md`, D-001; CURRENT-STATE
  constants table). A power calculation for a test family whose subject no longer exists is not a
  roadmap constraint. The 2029 figure should be retired with its parameter.
- **~2028** — ADR-026 / `decisions.md:455` / `status.md:203`: the general single-test sign-test
  floor for "our board beats consensus," reopening at n ≥ 6 development seasons
  (2021–2027 minus the 2025 holdout = 6), floor ≈ 0.031. Under the project's conventions
  (two-sided sign test: p = 2×(1/2)^6 ≈ 0.031 at 6-of-6) this is internally consistent.

**The "contradiction" was already resolved, and the resolution was lost.** `status.md:1785-1788`
records exactly this analysis — "not a contradiction… ~2028 is the general sign-test floor…
~2029 was a 14-test family… and D-001 deleted that parameter, so the 2029 figure's [premise is
gone]" — after which a scope-narrowed session reverted `CURRENT-STATE.md` to "CONTESTED"
(`status.md:1823-1836`, thread 064's corrected scope). The statistical question has an answer
sitting in the banned-for-current-state file while the canonical file says "unknown." That is a
Priority-1-class coordination failure (in-place reverts destroying resolved knowledge), not a
statistics failure — but it means **the PM's standing "~2029" claim is not even the repo's own
best number.** Work order S1 below re-lands the resolution properly.

## 2 · The mandate's four attacks, evaluated against what the repo actually does

**(a) "The resampling unit may not be the season — ~1500 paired player-seasons, clustered at
G≈5; wild cluster bootstrap at G=5 is unreliable, which is materially different from
impossible."** The repo has already litigated this, correctly, in two places:
`ADR-B-rank-correlation-aggregation.md:63` — a within-season player-level bootstrap "must never
be presented as a claim about future-season skill… conflating them is how a 4-season problem gets
dressed up as a 200-player problem" — and ADR-E §3.3's honest statement (the within-2025 paired
interval "describes variation across players within one league-year, not across league-years").
On the technical merits the repo is right and the mandate's hedge is thin: at G≈5 clusters the
wild cluster bootstrap's size distortion is severe (the Rademacher weight space has 2^5=32
points), and cluster-level permutation collapses to… the sign-test floor itself. "Unreliable but
not impossible" buys, in practice, a test whose stated α cannot be trusted — which for a project
whose brand is calibrated claims is the same as impossible. **This part of the repo's position
survives.**

**(b) "Effect size is being ignored."** It is not — descriptively. `ADR-B:65` pre-commits to
reporting the 4 paired per-season differences "as raw numbers with no p-value," and ADR-E §7.2
makes the consensus comparison descriptive-only. What *is* missing is the decision layer on top
of those descriptives: nothing on record says what the founder should **do** if the board beats
consensus 4-of-4 by wide margins. The repo's own ADR-E §9 shows the correct device — a
pre-registered adoption rule with thresholds, no significance claim — applied to the *accuracy*
question. The identical device applied to the *consensus* question is runnable the day a
non-consensus-derived board exists: e.g. "adopt for drafting iff paired margin is positive in
every usable season AND the mean margin exceeds X points, reported with a season-level bootstrap
CI and the standing no-edge-claim language." Adoption is a private act under decision theory, not
a publication under NHST; the founder is drafting a team, not submitting to a journal. **This is
the over-conservatism the mandate suspected, located precisely: not in the inference, but in the
absence of a pre-registered decision rule beneath the inference bar.** Work order S2.

**(c) "Subsetting buys no independence — reject 5 seasons × 6 positions = 30."** The repo does
not make this error anywhere I looked, and explicitly refuses it where it matters: ADR-A:50
treats positions as a multiplicity *cost* ("before multiplicity across 5 positions"), ADR-B
reports per-position with no aggregate and pre-commits that position-multiplicity makes claims
harder, and ADR-E §10 applies BH across declared family sizes. **Checked; clean.**

**(d) "Is there a defensible bar below significance the project should report instead of staying
silent?"** Partially already answered by (b): the raw paired differences are reported. The gap is
that FR-005's roadmap language ("Alpha detection is closed until ~2028… beating consensus cannot
be claimed from four seasons," `founder-requests.md:162-165`) has been operationalised as *"do
not build toward the comparison until then"* in places, when the correct operationalisation is
*"build it, run it, report descriptives yearly under a pre-registered rule, and claim nothing."*
Every season that passes without the paired comparison running prospectively is a season of the
n=6 clock not started. The cheapest thing the project can do for its 2028 self is register the
comparison protocol now (S2) so that 2026 and 2027 accrue as *pre-registered* seasons rather
than as retrospective ones.

## 3 · One error nobody flagged: the comparison's object does not exist yet

The entire 2028/2029 debate quietly assumes there is a "we" to compare against consensus. There
is not — the 2B review establishes the current board *is* re-scored consensus, so a
board-vs-consensus sign test today would compare consensus to itself at player level and measure
only the VBD positional re-weighting. The n-floor is therefore not even the binding constraint
on the clock: **the clock has not started, because season-differences can only accrue from the
first season in which a genuinely independent board exists and is frozen pre-draft.** If the
bottom-up board ships for the 2026 draft (ADR-E's prospective registration, §3.3), the first
usable paired season is 2026 and n=6 arrives after the **2031** season — unless the paired
comparison is also run retroactively on backcast bottom-up boards for 2021–2024 under the frozen
protocol, which is legitimate for descriptives but is *retrodiction*, with every forking-path
caveat the 2D review covers. Neither 2028 nor 2029 is the honest date for a prospective claim;
both are dates for a mostly-retrospective one. This distinction appears nowhere in the repo.
**Unresolved by the repo; stated here as the correction.**

## 4 · Summary judgement

| Claim component | Verdict |
|---|---|
| Season is the resampling unit; player-level clustering at G≈5 cannot rescue power | **Correct, survives attack** (ADR-B:63, ADR-E §3.3) |
| "~2029" | **Wrong** — moot 14-family figure; parameter deleted (D-001) |
| "~2028" as the single-test sign floor | **Arithmetically consistent** under stated conventions; already derived in `status.md:1785` and lost to a revert |
| "Unclaimable until then" ⇒ "undecidable / deprioritise until then" | **Over-conservative** — a pre-registered descriptive adoption rule is runnable now; publication-claims and drafting-decisions have different bars |
| Any "seasons × positions" independence inflation in the repo | **Not found; explicitly refused** where relevant |
| The date itself, for a *prospective* claim | **Both figures optimistic** — the clock starts when an independent board first exists frozen pre-draft (§3); retrodicted seasons carry 2D's caveats |

## Work orders

**S1 — Re-land the 2028/2029 resolution** [librarian, small]
Re-derive (or lift from `status.md:1785-1788`, verifying the arithmetic as done here) the
two-claims-not-one resolution; update the CONTESTED block in `CURRENT-STATE.md` to: "~2028,
single two-sided sign-test floor at n=6 development seasons; the ~2029 figure was ADR-A's
14-test family, mooted by D-001." This also closes thread 064's item 2 properly. (Fable cannot
edit CURRENT-STATE under this mandate; this is the PM/librarian's to land.)

**S2 — Pre-register the consensus-comparison protocol and its adoption rule, now** [strategist,
one session]
A registration (family `F-CONSENSUS-PAIRED`, m fixed) specifying: the paired unit (season), the
metric (per-position τ_b difference per ADR-B:65 plus roster-level margin once ADR-F simulation
exists), the universe/freeze dates, the descriptive reporting format (raw per-season differences,
season-level bootstrap CI, no p-values below n=6), **and a founder-facing adoption rule**
(dominance-and-margin thresholds under which the founder drafts from the new board while the
no-claims language stands). Explicitly mark which seasons are retrodicted vs prospective, per §3.
Cost: one strategist session; benefit: 2026–2027 accrue as pre-registered evidence instead of
being re-litigated in 2028.

**S3 — Correct the roadmap language** [PM, minutes]
Wherever "unclaimable until ~2028/2029" appears as a *sequencing* justification
(`founder-requests.md` FR-005 block, briefing docs), append the distinction: unclaimable ≠
undecidable; descriptive dominance reporting starts as soon as an independent board exists. The
PM's standing claim shapes the roadmap; it should carry the correction in the same documents
that carry the claim.
