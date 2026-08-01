# 2026-08-01 — fable — B1: the first build mandate (ranking v2)

Second fable dispatch of the day (end-of-week slot; M2 was the review, B1 the response). Founder's
authorisation verbatim in `docs/fable-mandate-B1-2026-08-01.md`: independent bottom-up rankings,
iterate, don't unlock 2025.

What happened, in order, each step committed before the next:

1. **Registration before compute** (`a80c2e3`): batch-B1 in the campaign manifest (m_b=12),
   `ranking_versions/v2.json`, build log opened at `docs/fable/v2-build-log.md`.
2. **Package** (`a9d7b75`): `experiments/bottomup/v2/` — gated week-shape loader +
   `V2Panel(SeasonPanel)`, feature builders, binomial-GLM games model, model subclasses, runner.
   Harness gates inherited, not hand-rolled; first verified run of this pipeline under pandas 3.
3. **Smoke → Amendment 1** (`fba26a9`): two-position peek recorded verbatim in the manifest, the
   G1 specification gap named (cannot express "resolved absence still carries moderate risk"),
   G1a/G2a registered before running, m_b 12→20, campaign M=92.
4. **Full span + grading** (`86a5207`): G1 and G1a **rejected by their own registered rules**
   (each 0 WIN / 1 BH-robust WR HARM downstream); mandate's naive-persistence bar earned at RB
   only (+0.084 BH-robust); **G2a (week-1 roster status) 3 WIN / 0 HARM** (RB +0.072, WR +0.048
   BH-robust) and the only arm beating naive MAE — adoption conditional on the strategist as-of
   ruling, exactly as pre-registered. Portability demonstrated after catching a false-PASS NaN
   defect in the first demo run (all-NaN points ordered by tie-break → "0 changes"; fixed,
   recorded). Absolute steering levels G0→G2a: RB 0.440→0.519, WR 0.560→0.595, TE 0.397→0.447,
   QB 0.245→0.255.
5. Handoff opened: `2026-08-01-g2a-week-1-status-as-of-ruling-and-v2-ship-revie` (fable →
   strategist; the as-of ruling is the one open decision; nothing merges on fable's sign-off).

The honest sentence for the founder: the timing-of-absence repair alone did not fix the games
channel; who-is-able-to-play-at-cutdown is where the real, reachable signal is; whether v2 may
use it is now a draft-date policy question with strategist, not a modelling question. Most of the
oracle gap (M2-1's D1) is irreducible from September information — absolute games ordering tops
out ≤0.27 even for the best arm.

2025 never read; audits clean on every run; all artifacts committed under
`experiments/bottomup/results/ranking_v2_*`.
