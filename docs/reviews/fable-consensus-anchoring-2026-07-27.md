# Is the ranking secretly consensus-anchored? — 2026-07-27 (Priority 2B)

**Verdict in one sentence: the current board is not *secretly* consensus-anchored — it is openly,
structurally, 100% consensus-anchored, by documented design, and the genuinely bottom-up ranking
does not exist yet; the planned framework (ADR-E) survives the circularity attack on paper, with
three specific leak points named below that need pinning before its first run.**

The distinction matters because the two failure modes the mandate warns about are different. A
hidden anchor produces false confidence in independence. This repo has the opposite posture: it
states the anchoring at the top of the module. The risk here is not deception but *drift of
summary* — anyone describing "our board" without reading `make_board.py`'s header will call it
proprietary, and it is not.

---

## 1 · What the shipped ranking actually is

`src/make_board.py:12-38` is explicit: `projected_points` is
`E[our_points | position, consensus positional rank]` — a per-position curve
`points ~ alpha + beta·ln(rank)` fitted on historical seasons, applied to **FantasyPros ECR rank**
(`SOURCE = "fantasypros_ecr"`, `make_board.py:85`). The header states the consequence plainly:

> "Every player at the same positional rank gets the same projection. The board's value is in the
> positional re-weighting, not in disagreeing with consensus about individual players."
> (`make_board.py:36-38`)

Three implications, stated as findings:

- **Player-level edge is structurally zero.** The board cannot rank any player differently from
  consensus within a position, ever. Its only edge channel is *positional* revaluation under this
  league's scoring (VBD re-weighting with measured replacement levels). Errors at player level are
  consensus's errors, correlated 1.0 — the mandate's "cannot find where the market is wrong"
  condition holds *exactly*, and the module says so itself.
- **This is by design and defensible** — the module's purpose (b) is to be "the PRIMARY null
  hypothesis for the backtest… If the model cannot beat this, it has no edge"
  (`make_board.py:7-10`). A consensus-derived *baseline* is supposed to be consensus-derived.
- **But the baseline is currently also the product.** The same artifact is purpose (a): "a usable
  draft artifact that stands alone" (`make_board.py:4-6`). Until ADR-E ships, everything the
  founder sees — board order, VBD, the suggester's "TOP 5 BY BOARD RANK", the RECOMMENDED stopgap
  (explicitly labelled "unvalidated stopgap score, not a backtested model", thread 051) — is
  re-scored consensus. Compounding: the consensus being re-scored is the *wrong scoring format*
  (standard, not half-PPR — `ingest_rankings.py:25-36`; see the 2A review, T1).

## 2 · The hunt, path by path

Per the mandate's list. Cited or "unresolved" — nothing filled in.

| Circularity path | Finding |
|---|---|
| Consensus as a feature / prior / sort order | **Present and disclosed** — it is the board's only player-level input (§1). In the *planned* bottom-up framework, consensus rank is restricted to the baseline arm and an explicitly-labelled hybrid arm; "the bottom-up model's confirmatory arm must not consume consensus rank, or 'bottom-up beats consensus-derived' becomes circular" (`ADR-E §4.1`, Market row). The rule exists; nothing *enforces* it yet — see leak point L1. |
| Consensus as missing-value fallback | **Present in the availability layer, disclosed.** The optional MFL ADP source falls back to FP-ECR rank for the ~370+ players MFL doesn't cover (`availability.py:100-105, 133`), making it "a blend of real MFL data at the top and a copy of the other source beneath it" — the module says exactly this and deliberately does not wire it in (`availability.py:80-83, 89-109`). Legitimate: the availability/hazard model predicts *other drafters' behaviour*, for which market rank is the correct kind of input. The hazard model consuming consensus is not circularity; the *ranking* consuming the hazard model's consensus would be — see leak point L2. |
| Player universe selected by ADP | **Board:** yes, definitionally — the universe is "rows in `rankings` where source='fantasypros_ecr'" (`export_contract.py:119-123`). Fine for a consensus baseline, but it means the *product's* universe today is consensus-defined too (a player consensus omits does not exist on the board). **ADR-E:** largely fixed — universe frozen from "prior-season positional finish" at declared depths, which is production-based, **plus "rookies inside the pre-season consensus depth where consensus exists"** (`ADR-E §2`, universe bullet). That rookie clause is the one consensus dependency in the confirmatory universe — see leak point L3. |
| Replacement level from where players go, not what they produce | **Clean, on the record.** RB30/WR40/TE10/QB10 are "measured over 26 seasons under this league's rules" (CURRENT-STATE, constants table) — production-derived, not draft-position-derived; flex split likewise measured (ADR-029, `league_config.py:61-65`). Not independently re-derived this pass; provenance accepted from the constants table's own caveats. |
| Hand-tuned constants chosen because output "looked right" | **One recorded instance, disclosed:** the isotonic rank-curve estimator was "discarded after inspection" because it put a QB at overall #1 (`make_board.py:40-48`). The stated reasoning is diagnostic (estimator artifact, 5 obs/rank) and I find it defensible — but it is post-hoc model selection against the same data, and it belongs in the 2D forking-paths count, where I have counted it. `RELEVANT_DEPTH` (`make_board.py:89-93`) is roster arithmetic, not ADP-tuned. `delta=0.10` is an admitted unvalidated prior with a pre-registered kill rule (D-004). `NEED_ADJUSTMENT_SCALE` is deleted (D-001). No hidden magic numbers found in the modules read this pass; not exhaustive over all 36 modules — unresolved beyond the ones named. |

## 3 · The three leak points to pin before ADR-E's first run

**L1 — The no-consensus rule for the confirmatory arm is prose, not a check.** ADR-E §4.1 forbids
consensus features in the confirmatory arm and §3.2 enumerates fold-local estimation, but nothing
asserts the prohibition mechanically. The project's own standard (guardrails: structural, not
procedural; the strategist's missing Bash) says this should be a test: the confirmatory pipeline
object declares its feature manifest, and a test fails if any column with `consensus`/`ecr`/`adp`
provenance appears in it. Cheap, and it converts §4.1's most load-bearing sentence into a
structural impossibility. **Work order C1** [backend, small, at ADR-E implementation time — not
before, there is no pipeline yet].

**L2 — The recommendation surface blends ranking and availability, and only one of them is
consensus-free even in the future state.** The draft-room recommendation ("RECOMMENDED…stopgap")
combines board value with availability/roster context. Post-ADR-E, a bottom-up board scored
through an ECR-driven hazard model is *fine* (availability legitimately models the market), but
any summary claiming "our independent view" must scope the claim to the projection, not the
recommendation. This is a language rule in ADR-E §7.3's spirit that currently covers backtest
artifacts but not the product surface. **Work order C2** [librarian: extend §7.3's forbidden-list
to product copy; one line in the design/frontend guidance].

**L3 — Rookies enter the confirmatory universe via consensus, and only where consensus exists.**
ADR-E §2 admits rookies "inside the pre-season consensus depth where consensus exists" — consensus
history starts 2021, so pre-2021 folds have no rookie-inclusion source. Either those folds exclude
rookies (universe composition then differs systematically across folds — the old-fold universes
are survivors-of-a-prior-season only, which flatters accuracy on exactly the folds with the most
weight in a 24-fold LOSO) or an undeclared alternative gets invented at implementation time.
ADR-E does not say which. **Unresolved in the ADR; it should be resolved in the registration, not
in code.** Options worth stating for the strategist: (a) NFL draft capital as the rookie-inclusion
criterion (available all 26 seasons, production-independent, market-ish but a *different* market
from ADP); (b) exclude rookies from all folds and say so in every reported n; (c) rookies in
2021+ folds only, reported as a split sample. **Work order C3** [strategist, one section added to
the F-BOTTOMUP-CORE registration before first run].

## 4 · What survives the attack

Stated plainly, per the mandate:

- The **honesty architecture survives.** Every consensus dependency I found is documented at the
  point of use, usually with the failure mode named (`make_board.py` header, `availability.py`
  MFL-source docstring, ADR-E §4.1/§7.3). I hunted for a *hidden* anchor — consensus smuggled
  through a fallback, a sort, a tuned constant — and did not find one that the code does not
  itself announce. The repo's problem is the gap between what is built (consensus, re-scored) and
  what the ambition documents talk about (bottom-up), not concealment.
- The **source-separation principle holds where it matters**: ranking sources are separate enums,
  the MFL/ECR blend is refused as a default precisely because it is a blend
  (`availability.py:89-109`), and ADR-E's baseline-refit rule (§7.1) plus its forbidden-language
  list (§7.3) are the strongest anti-circularity language in the repo.
- The **consensus-anchored errors** consequence the mandate describes is real but currently moot
  in the dangerous direction: the project has (correctly) never claimed player-level edge from
  this board — the claims discipline (ADR-B, ADR-E §7) exists to prevent exactly that. The 2C
  review covers whether the claims *about* beating consensus are calibrated.

## Work orders

- **C1** [backend, at ADR-E build time] — feature-manifest guard: confirmatory pipeline declares
  its input columns; test fails on any consensus/ECR/ADP-provenance column. Fixture: a deliberately
  contaminated manifest must fail.
- **C2** [librarian, doc-only, small] — extend ADR-E §7.3's forbidden-language scope to product
  surfaces (frontend copy, assistant responses): "our independent projection" may describe S1–S3
  output only, never the recommendation blend.
- **C3** [strategist, before F-BOTTOMUP-CORE registration] — resolve the pre-2021 rookie-universe
  rule (options a/b/c above) inside the registration; whatever is chosen, the per-fold universe
  construction rule becomes part of the declared protocol, not an implementation choice.
