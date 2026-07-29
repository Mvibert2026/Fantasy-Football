# UNALLOCATED handoff body — competitive UX findings (researcher → pm, frontend)

**This is not a thread. It has no ID and must not be given one by hand.**

The researcher session that produced `docs/research/competitive-ux-2026-07-29.md` ran in a cloud
container with **no shell tool**, so `python tools/handoffs.py new` could not be run. Thread IDs come
only from the allocator — hand-typing or computing max+1 is what collided at ADR-048 and threads
043 / 049 / 053. The body is staged here so the next session with a shell can allocate it in one
command and paste this in.

**Allocator command:**

```
python tools/handoffs.py new --from researcher --to pm,frontend \
  --subject "Competitive UX: the overhaul case is weaker than expected; three scoped changes instead" \
  --blocks "the frontend overhaul decision, FR-034 (selectable draft slot)"
```

---

## Ask

`docs/research/competitive-ux-2026-07-29.md` is the full artifact. Four things need a decision or an
owner; none of them is a researcher's call.

### 1. The overhaul decision itself — a founder call, and the evidence points one way

**Recommendation: do not do a visual overhaul. Do three scoped structural changes instead.**

The prior competitive UX pass already concluded the fix here was token-level rather than a redesign,
and that work shipped (two type roles, elevation surfaces, radius discipline, accent discipline,
colourblind redundancy — `docs/design-handoff/README.md` Addendum 3). Nothing found this session
contradicts it, and ESPN's 2025 redesign is `[SECONDARY]` evidence that the marginal return on visual
investment in this category goes *negative* past a threshold we appear to have crossed: *"Font is
atrocious and it is so zoomed in, can barely see any of the roster"*; *"Everything just blends
together"*; *"The only reason people chose to use ESPN over any other app is because the interface
was cleaner."*

Against that, `docs/operating-model.md` records a 38K-character spec port that hit a hard stop at
~97% usage and self-reported inaccurately. An overhaul re-incurs that risk across every screen. The
three scoped changes are additive and independently shippable.

**If the founder wants an overhaul anyway, that is fine — but it should be recorded as a preference,
not as a finding, and `CLAUDE.md` §2/§8 means it needs a spec amendment rather than a sprint.**

### 2. Three scoped changes, in priority order — needs a frontend owner

1. **Uncertainty on the board row.** Render *"not distinguishable from ranks X–Y"* in the rank cell's
   own visual weight, from the `vbd_lo`/`vbd_hi` already exported. The precedent is Draft Sharks,
   which ships 80% and 95% confidence prediction limits alongside individual player projections and
   publishes its own MAE, ROC-AUC and a calibration plot `[VERIFIED]`. The internal case is already
   in `docs/ideas-inbox.md`: *"Josh Allen's CI [57.0, 155.2] overlaps 29 of the top 40 players"* while
   the point estimate is what gets read. Add a verbal form too — Boris Chen's *"If experts are 50/50,
   there's no wrong choice"* `[VERIFIED]` does the work of an error bar in one sentence.
2. **Draft slot selectable in the prep setup block, with a "random slot" option.** FantasyPros'
   guidance is *"Draft from a specific slot if your draft order is already set, or select at random
   each time to prepare to draft from every pick"* `[VERIFIED]`. The steal is the *loop*, not the
   control: for a founder with three leagues and three slots, the useful question is which picks are
   fragile across slots. Closes the actionable half of **FR-034**.
3. **State ownership labelled on screen — league-scoped vs. account-scoped.** Sleeper's split is the
   clean primitive and this project already adopted half of it: *"Watchlist is account-wide which
   means your tracked players will be visible on all leagues, not for each league"*, while the draft
   queue is league- and draft-scoped `[VERIFIED]`. Generalise it: board, slot, roster, queue → league.
   Watchlist, notes, model version, preferences → account. That is the cheapest answer to "make
   multi-league not feel like a settings chore."

Four further items with lower value-per-cost are listed in §7 of the artifact (snake grid view,
on-deck state, reach indicator, designed degraded state). **The reach indicator carries a constraint
from thread 082 that must not be lost: never render an ADP number without its `adp_source` label, and
only 144 of 510 board rows carry one — the other 366 need a real null state.**

### 3. A missing artifact — librarian/PM, and it is why this dispatch was partly rework

`docs/operating-model.md`'s budget calibration table logs a completed, verified **"Competitive UX +
platform + Reddit research"** pass. At least six live documents cite its conclusions:
`docs/design-handoff/HANDOFF-NOTES.md` §"What changed this round", `docs/design-handoff/README.md`
Addendum 3, `docs/handoffs/030`, `docs/handoffs/047`, `docs/adr-drafts/ADR-A`,
`docs/screenshot-checklist.html`.

**The artifact itself is not in the repository.** I searched the whole tree including every agent
worktree under `.claude/worktrees/`. Its findings survive only as paraphrase inside the documents
that consumed them — including the 5/10 visual-polish and 4/10 light-mode scores, which are quoted
with no evidence behind them anywhere in the repo.

Two consequences: this project has now bought the same research twice, and any decision resting on
those two scores is resting on an unverifiable number. Worth a `docs/state-claims.toml` entry of the
"cited document must exist" class, which is exactly what ADR-059's checker is for.

### 4. Two corrections to prior work — for the record, no action needed

- **Thread 061's** *"no competitor found publishes calibration evidence"* needs narrowing. It holds
  for **availability** modelling, where nobody publishes anything. It is false as a general
  statement: Draft Sharks publishes out-of-sample ROC-AUC 0.809, R² 0.401, MAE 1.610 and a binned
  reliability check for its injury model `[VERIFIED]`. The defensible differentiator is
  *pre-registered calibration of the availability model specifically* — still unmet at 1 of ~30 mocks.
- The thread 061 audit lives at `docs/research/competitor-recommendation-audit-2026-07.md`, not in
  `docs/reviews/`. Several dispatches have now pointed at the wrong directory.

## Why

The founder asked for this before committing to an overhaul, which is the right sequence. The answer
is that the overhaul is not what the evidence supports, and saying so plainly is more useful than
returning a feature list. The three scoped changes are all things a designer can act on without
reopening every screen.

## Constraints honoured

Every recorded block was honoured and none was routed around. `www.reddit.com` was **refused by the
tool** and is the largest hole in the voice-of-customer section — recorded, not worked around.
ESPN/Yahoo/CBS not attempted. `forums.footballguys.com` and `www.fantasylife.com` both had relevant
material surface in search and were left unfetched for consistency with the blocks recorded in thread
009, even though `fantasylife.com/articles/` is not robots-disallowed; flagging that path-level
loophole rather than exploiting it alone.

**Fetching vs. redistributing:** everything in the artifact is design intelligence — descriptions of
interactions and published claims. **No competitor's data is proposed for ingestion, storage or
display, and no numeric value from any competitor appears as a candidate product input.**

## Done looks like

PM records the overhaul decision (build / don't build / amend `CLAUDE.md`), frontend takes or
declines the three scoped changes with a thread each, and librarian/PM disposes of the missing
artifact in §3. Then reply here and set `STATUS:` appropriately — only the `TO:` role may resolve.
