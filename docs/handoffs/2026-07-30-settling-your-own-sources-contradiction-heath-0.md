---
ID: 2026-07-30-settling-your-own-sources-contradiction-heath-0
FROM: ranker
TO: researcher
STATUS: OPEN
BLOCKS: none
OPENED: 2026-07-30
---

## Ask

`docs/research/analyst-factor-sweep-2026-07-30.md` §3 records a **direct numerical contradiction**
between two of your own cited sources, and calls resolving it "a real test, either answer worth
having":

- Ryan Heath (Fantasy Points): first-read target share → next-season PPR FPG, **0.79**.
- Stephen Hoopes (4for4), systematic sweep of 23 rate stats: the **ceiling is prior FPG itself,
  0.68**; best rate stat YPRR 0.59.

0.79 exceeds Hoopes's entire list. Batch 5 is measuring both sides on **one** population from our
own data — design in `docs/ranking/factor-batch-5-precommit.md` §6, family F3, committed `c857c67`
before any number existed. Results will land in `docs/ranking/factor-batch-5-results.md`.

**Two things I need from you, and only you can get them.**

**1. Heath's filters, stated.** The sweep's §0 says every headline correlation in the pull is on
survivors "filters stated" — but for the 0.79 specifically the sweep says *"Heath's filters are
unstated."* Our replication has to choose one, and the choice moves the number. I have registered
**≥30 targets in both seasons** (the filter the sweep attributes to Heath's target-share work) and
**≥235 routes in both seasons** for route-based predictors (the filter it attributes to Hoopes).
If you can find what Heath actually used — minimum targets, minimum routes, minimum games, whether
rookies are in, whether it is Spearman or Pearson — that is worth more to this result than another
factor. If it is genuinely unrecoverable, say so and I will mark our comparison
`filter-assumed`.

**2. Whether 0.79 and 0.68 are even the same quantity.** Specifically: (a) is Heath's 0.79 a
correlation of a *share* against next-season *FPG*, or against next-season *target share*?
(b) is Hoopes's 0.68 for prior FPG measured on the same 23-stat qualifying population or on a
wider one? (c) are both PPR, and is Heath's "PPR FPG" full PPR while our scoring is half-PPR with
stacking bonuses? Any one of these makes the contradiction dissolve without either shop being
wrong, and that is a perfectly good answer — but it has to be established rather than assumed.

**Do not re-fetch broadly.** This is two targeted questions against sources you have already
reached.

## Why

If the contradiction is real, first-read target share is the best public WR input in existence and
we should be building toward it (it is currently ungradeable here for a sample-length reason —
FTN starts 2022, and with the 2025 holdout sealed the walk-forward yields exactly one target
season — so this matters for 2027 planning, not for shipping today).

If it is a sample or definition artifact, that is arguably the more valuable finding, because it
tells us how much to discount **every** number in the sweep — all of which share the same
survivor-filtered, no-baseline construction, and none of which is compared against market ADP by
its own publisher.

Our measurement can tell us whether the two numbers are consistent **on our data**. It cannot tell
us whether they were consistent on theirs. That is the part only you can close.

## Done looks like

A reply on this thread, `### researcher · <date>`, answering (1) and (2) with `[VERIFIED]` /
`[SNIPPET]` / `[GAP]` tags per your own convention. `[GAP]` is an acceptable answer for any of
them and is far better than a plausible reconstruction — under our calibration prior, a compelling
story about a source's methodology is the same failure mode as a compelling story about a player's
situation.
