# Founder mocks, 2026-07-30 — ingestion, scoring-format inference, admissibility

Two Yahoo mock drafts pasted by the founder, transcribed to TSV, converted to the
`mock_drafts`/`mock_picks` JSON shape used by `src/ingest_mock_drafts.py`, and ingested.

## Task 1 — ingestion

| mock_id | teams | rounds | picks | resolved | quarantined | format_conforms |
|---|---|---|---|---|---|---|
| `yahoo-10team-slot4-2026-07-30` | 10 | 15 | 150 | 131 | 19 | **False** — `flex_slots=1, need 2; rosters a kicker, need none` |
| `yahoo-12team-slot2-2026-07-30` | 12 | 15 | 180 | 160 | 20 | **False** — `teams=12, need 10; flex_slots=1, need 2; rosters a kicker, need none` |

Total: **330 picks ingested, 291 resolved, 39 quarantined.**

Source TSVs: `data/mock-drafts/yahoo-10team-slot4-2026-07-30.tsv`,
`data/mock-drafts/yahoo-12team-slot2-2026-07-30.tsv`. Converted JSON (same shape as
`founder-mock-2026-07-29.json`, no parallel ingestion path invented):
`data/mock-drafts/yahoo-10team-slot4-2026-07-30.json`,
`data/mock-drafts/yahoo-12team-slot2-2026-07-30.json`.

**Snake order verified programmatically, not trusted from the file.** For each draft: built the
manager→slot mapping from round 1's pick order, then asserted every even round's manager sequence
is the exact reverse of round 1's and every odd round matches it forward (`overall_pick =
(round-1)*teams + pick_in_round`). Both files passed on the first try — no correction needed.
Script: `/tmp/.../scratchpad/convert.py` run this session (not committed; trivial to regenerate
from the TSVs if the conversion needs re-running).

**Quarantine reasons** (none guessed, all recorded):
- Team defenses (`Texans`, `Rams`, `Broncos`, `Seahawks`, `Patriots`, `Eagles`, `Vikings`,
  `Steelers`, `Jaguars`, `Chargers`, `Ravens`) — 11/10, no `players_canonical` entry for a team
  name, expected (DEF isn't a player).
- Kickers (`Andy Borregales`) — same reason, expected.
- Ambiguous names needing a real disambiguation (not guessed): `Justin Jefferson` (2 matches),
  `Lamar Jackson` (2), `DJ Moore` (2), `Marvin Harrison Jr.` (3), `Michael Pittman Jr.` (2),
  `Oronde Gadsden` (3, 12-team only).
- Genuinely unresolved (no match at all): `Chig Okonkwo`, `Kenny Gainwell`.

`league_config_id` used for ingestion is a **best-guess placeholder** (`yahoo_10_half`,
`yahoo_12_half`) chosen only so the pipeline has a `LeagueConfig` to check format against — it is
not a claim about these mocks' real scoring, which is exactly the open question Task 2 addresses.
It does not affect the `format_conforms` result: both mocks fail on kicker/flex-slot shape
regardless of which scoring guess is plugged in.

## Task 2 — scoring-format inference

Compared each mock's realized pick order against FFC ADP (`ffc_adp_snapshots`) at the matching
team count, all available formats, using Spearman rank correlation on resolved picks only
(`mfl_id` join).

### 10-team (vs. current 2026-07-29 FFC snapshots — same vintage as the draft)

| ADP format | n matched | Spearman ρ | p |
|---|---|---|---|
| `ffc_non_ppr_10team` (standard) | 126 | **0.9333** | 5.4e-57 |
| `ffc_half_ppr_10team` | 130 | **0.9485** | 9.5e-66 |
| `ffc_ppr_10team` | 130 | **0.9541** | 7.1e-69 |

Ordering is monotonic — standard fits worst, PPR fits best — consistent with the founder's own
guess of half-PPR-or-fuller. **But the three correlations are close (0.933 → 0.954), and no
significance test for the difference between correlated correlations (e.g. a Steiger/Hittner
test on the same underlying pick set) was run here.** That is a judgment call past this role's
remit — see the handoff below rather than treat 0.954 vs. 0.933 as a settled finding.

### 12-team

| ADP format | n matched | Spearman ρ | p |
|---|---|---|---|
| `ffc_non_ppr_12team` | 104 | 0.5590 | 6.9e-10 |
| `ffc_half_ppr_12team` | 101 | 0.5707 | 4.6e-10 |

**No `ffc_ppr_12team` source exists in `ffc_adp_snapshots` at all** — only non-PPR and half-PPR
are present for 12-team. Worse: **the most recent as-of-date for either 12-team source is
2024-09-01** (checked: `ffc_non_ppr_12team` and `ffc_half_ppr_12team` both top out at 2024-09-01;
`ffc_non_ppr_10team`/`ffc_half_ppr_10team`/`ffc_ppr_10team` all have a live 2026-07-29 snapshot).
The 12-team comparison is therefore against a **stale, ~2-year-old market**, not the current one —
the correlations above are real numbers but a weaker basis for inference than the 10-team ones,
and the near-50% "missing from ADP" rate (56/160, 59/160) reflects 2024's smaller player pool, not
a real name-resolution problem.

### Positional-ordering checks

- **Rounds 1–4 position mix:** 10-team WR 19 / RB 17 / TE 3 / QB 1; 12-team WR 22 / RB 22 / TE 3 /
  QB 1. Mildly WR-leaning in the 10-team draft, even in the 12-team draft — directionally
  consistent with reception-value scoring, but WR-early is also the general 2026 market trend
  regardless of format (nflverse-independent), so this is weak evidence on its own.
- **TE landing spots, the sharpest single signal requested:** Bowers went 3.03 (pick 23 overall,
  10-team) / 2.03 (pick 15, 12-team). McBride went 3.08 (pick 28, 10-team) / 2.08 (pick 20,
  12-team). Checked against current 2026-07-29 FFC ADP for both players at 10-team: Bowers ranks
  50th/46th/37th (standard/half/PPR), McBride 48th/39th/32nd. **Both TEs went far earlier in this
  mock than even the most reception-friendly FFC format predicts.** This is real evidence, but it
  cuts against a clean scoring-format read: it looks like this specific mock's draft pool ran TEs
  early for reasons the FFC-format axis alone doesn't explain (small-n mock/bot behavior, a
  TE-scarcity narrative, etc.), not simply "this room scores receptions higher than the market."

### Confidence

**LOW-to-MODERATE, standard scoring ruled out; half-PPR vs. full PPR not separable at this
sample.** The 10-team draft is closer to half-PPR/PPR than standard — the direction the founder
guessed — but the ρ gap between half-PPR and PPR is too small to call without a proper test for
correlated-correlation difference, which needs Backend/Strategist judgment, not a Sonnet/low
data-ops call. The 12-team comparison is weakened further by the ADP staleness above and should
not be treated as confirming or contradicting the 10-team read.

**Handoff opened:** `docs/handoffs/112-founder-mock-scoring-format-inference-needs-sepa.md` to
`strategist` — asks for (a) a formal separability test on the 10-team ρ's, (b) a decision on
whether the missing current-2026 12-team/PPR ADP snapshots are worth back-filling, (c) any read
on the TE-early anomaly.

## Task 3 — roster-shape mismatch

**Both mocks contain K and DEF rounds; Westwood has neither a kicker slot nor these flex/roster
shapes.** Confirmed programmatically via `format_conforms()`: both fail on `flex_slots=1` (need 2)
and "rosters a kicker" (need none); the 12-team additionally fails on `teams=12` (need 10). This
directly contradicts the founder's statement that these have "the same roster constraints as the
first I sent you" — the first (`founder-mock-2026-07-29.json`, FantasyPros) was **also**
non-conforming (standard scoring, one flex, with a kicker, per its own `capture_note`), so the
founder's mental model of "same as the first" is consistent internally but the first one was never
Westwood-shaped either. **Two K/DEF rounds out of fifteen (13.3% of every roster) is not a rounding
error** — it changes the effective non-K/DEF player pool available in rounds 13-15 and shifts late-
round ADP/run behavior versus a 13-round, no-K/DEF Westwood draft. Not resolved by assumption here;
reported plainly per the task instruction.

## Task 4 — admissible uses

| Use | Admissible? | Reasoning |
|---|---|---|
| **λ / opponent-noise calibration** | **Probably yes, with a caveat.** These are real human draft sequences at two new team counts (10, 12) and two new slots (4, 2), tripling the sample base from 160 to 490 total picks. But both differ from Westwood's actual shape (10-team half-PPR, 3WR/2FLEX, no K) in roster construction, and the 12-team draft differs in team count outright. λ measures opponent unpredictability in the *pick sequence*, which is less roster-shape-sensitive than, say, positional-run timing — so transfer is more defensible for λ than for anything positionally granular. State this explicitly if λ is re-measured with these included: **the 12-team draft's structural difference (2 more teams, no flex-2 slot) is a bigger transfer risk than the 10-team draft's kicker/flex mismatch.** |
| **ADP proxy** | **No.** A mock is one draft, not a market average — `mock_drafts.is_mock=1` and `format_conforms=False` for both already mark this correctly in the schema. Do not treat `overall_pick` from either file as an ADP substitute for anything; use the real `ffc_adp_snapshots`/Yahoo consensus for that. |
| **Positional-run behavior** | **Yes, this is the genuine unblock.** `mock_picks` now stores real per-pick `team_slot`/`round`/`overall_pick` sequences for 330 more picks (291 resolved), which is exactly the per-pick draft state `live_availability.py`'s run-detection term needs and did not have before this session beyond the single 150-pick FantasyPros draft. This does not resolve the roster-shape mismatch (Task 3) — a run captured in a 1-flex/kicker draft is not automatically the same run that would happen in Westwood's 2-flex/no-K shape — but it is real per-pick sequence data where before there was a final-sequence-only schema gap. Recommend the run-detection prior review these three drafts (450 picks total) rather than the founder's original single 150-pick one, while continuing to flag the shape mismatch as a caveat on the result, not silently absorbing it. |

## Commit / evidence

- Commit hash: see below (added after commit).
- Rows ingested: 291 resolved picks (131 + 160), 39 quarantined (19 + 20), across 2 `mock_drafts`
  rows and 330 `mock_picks` attempts.
- Tests: `tests/test_ingest_mock_drafts.py` — 21 passed (pre-existing suite, unmodified by this
  session; no schema change was needed since these mocks use the same JSON shape as the existing
  fixture).
