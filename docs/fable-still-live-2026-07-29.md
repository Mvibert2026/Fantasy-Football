# What survives from Fable — 2026-07-29

Covers all 18 files in `docs/reviews/` (all dated 2026-07-27/28). Reports what still applies today,
what's dead, and what got more urgent because of what changed since: cloud migration, FFC unblocked
and half-PPR ADP now captured daily, ADP reached the board data (but not yet the screen — see the
companion triage doc), the app is live on the internet, the database rebuilds in one command, and
the founder reversed the ESPN-league deferral (wants a "generic" second tier — FR-027, 2026-07-29).

## Summary — plain English

Fable did four kinds of work: (1) a table-stakes correctness audit, (2) a deep methodology review of
the "beats consensus" ranking work, (3) a workflow/infrastructure review of how agents coordinate,
and (4) two schedule-feasibility passes. Most of (1) is now done. Most of (2) is still exactly where
Fable left it — nobody has run the confirmatory experiment yet. Some of (3) is done; the core problem
it warned about (ticket numbers colliding) has actually gotten worse, not better, since. (4)'s dates
were built around an "Aug 30" internal buffer target — the real Westwood draft is confirmed for
7 September, which is a week later than that review assumed, so there's a bit more room than it
thought, not less.

**What you can forget about:**
- The correctness-floor bugs (wrong scoring format input, no freshness check, no suspension list, no
  team-code crosswalk) — Fable's single loudest alarm — are now mostly fixed and tested.
- The FFC ADP harvest Fable recommended as a "relief valve" for the calibration problem is done —
  it's now capturing daily at far higher volume than the fallback Fable described.
- The one-off screenshot-testing harness Fable built is merged and in use.

**What's still exactly as open as Fable left it, and matters most:**
1. **Nobody has run the one experiment that decides whether the "our own ranking" work ships at all**
   (the confirmatory statistical test). This has been sitting ready to schedule for two days.
2. **Real mock-draft collection still hasn't started** — every calibration claim in the product is
   still based on one real draft.
3. **The recommendation card you'll actually see on draft day still doesn't use the one measured
   parameter in the whole system** (λ) — it runs on five made-up numbers instead. Fable found this,
   and it's still true.

**What got more important because of what changed today:** the finding that the model's roster-need
math is hardcoded to your Westwood league specifically (not read from settings) is now a bigger deal
than when Fable found it, because you've asked for a second, generic tier of support for your ESPN
and Yahoo leagues — and that hardcoding is exactly what would silently give ESPN/Yahoo users
Westwood's numbers instead of their own.

---

## Still live

### 1. The "does bottom-up ranking work" experiment chain — the single biggest still-open item

Fable specified a short, final sequence of tests (`fable-bottomup-next-tests-2026-07-28.md`):
one test to check if the two-stage model architecture is worth its complexity, one to settle whether
rookies belong in the evaluation, then the one real confirmatory test — all gated on a small piece of
plumbing ("H3," a safeguard that stops the model from accidentally peeking at 2025 results) that was
still not built as of the last check. **Nothing here has been falsified by anything that changed
today.** If neither running backs nor wide receivers pass the confirmatory test, the plan is to ship
consensus-only rankings and say so plainly — that's already the pre-agreed outcome, not a fallback to
invent later.

*Depends on:* one backend session for the safeguard, one for the two remaining tests, then the real
run. Nobody has picked this up.

### 2. Real mock-draft collection still hasn't started

Fable's schedule review (`fable-schedule-feasibility-2026-07-28.md`) did the arithmetic on this
directly: getting 30 practice drafts logged before the draft is not realistic alongside a job and a
life — it recommended cutting the target to 10-12 and being honest that the model's "how often will
this player still be there" claim stays unvalidated either way. **Still true.** The plumbing that has
to land before any practice draft can count (recording every pick, not just the final list) is still
an open ticket (thread 002) that's been open since day one.

*What changed:* the real draft date is confirmed for 7 September, a week later than the buffer date
Fable's arithmetic assumed. That's a small amount of extra room, not a fix to the underlying problem
(the founder's own time is still the bottleneck, not agent time).

### 3. The recommendation card you'll see doesn't use the one measured parameter

Fable's deepest single finding (`fable-lambda-sensitivity-2026-07-28.md`): the only parameter in the
whole system that's actually been fit to real data (how hard a manager reaches for a positional need,
called λ) doesn't drive the card the founder will actually see on draft day. That card runs on five
flat numbers nobody ever measured. **Confirmed still true** — no thread claims this was rewired.
This is a real, cheap-to-explain gap between "the model we tested" and "the model you'll see."

### 4. The model's need-math is hardcoded to Westwood specifically — now more urgent

Same review found that the roster-need calculation assumes Westwood's exact roster shape (no kicker,
16 rounds, this league's positions) baked in as constants, not read from each league's settings. It
called this "wrong by construction the moment a second league uses it." **That day has arrived** — the
founder now wants a generic (if simpler) version of the tool for his ESPN and Yahoo leagues
(FR-027, 2026-07-29), and this is exactly the piece of code that would silently misfire for them.
Flagged as escalated by the founder's own new request, independent of this document.

### 5. The draft-time assistant (an AI chat feature) still shouldn't be built yet

Fable's review (`fable-assistant-constraint-2026-07-27.md`) concluded a chat assistant is buildable
safely only in a constrained form (it can only recite computed numbers, never invent reasoning) and
specifically **should not be built until the "what if I wait a round" simulation feature exists** —
otherwise its two most-asked questions have no real answer to recite. That simulation feature
(thread 045/059/060) is still unbuilt. Unchanged; still correctly blocking.

### 6. In-season features (waivers, start/sit, trade help) — still correctly not started

Fable's in-season review (`fable-in-season-2026-07-27.md`) said the current draft engine can't
express these questions and shouldn't be stretched to — they need a new, structurally similar
sibling tool, gated on the same "week-by-week" data shape as the assistant work above. Nothing
about this changed; it's correctly still on the "later" list, unaffected by anything today.

### 7. Statistical guardrail bugs (holdout-sealing enforcement) — likely still open

Fable found the "don't peek at 2025 results" safeguard only covers four of the places it should
(`fable-overfitting-2026-07-27.md`) and a naming collision that makes an unprotected code path look
protected. No thread found confirms this was fixed. Small, cheap, still worth doing before item 1
above runs its real experiment.

### 8. The ticket/ADR numbering collision problem — got worse, not better

Fable's workflow review recommended a specific fix (auto-assign ticket numbers at sync time instead
of by hand) and it **was built** — confirmed in the code today. But the session log from earlier
today records the same *class* of collision happening three more times in one day, in ways the fix
doesn't cover (a decision-numbering collision, and a duplicate founder-request number, both across
parallel work branches rather than parallel folders). Fable's diagnosis was right; the fix shipped
was necessary but not sufficient. Still open, arguably more urgent now that it's demonstrably
recurring.

---

## Now dead (premise falsified)

| Recommendation | Why it's dead |
|---|---|
| Build a repeatable FFC ADP harvest as a "relief valve" for calibration data (fable-schedule-feasibility, headline 5's "harvested pool") | **Done.** FFC is unblocked for recurring use and now captures half-PPR ADP daily at roughly 27× the sample of the old proxy source, per today's session. |
| Fix the wrong-scoring-format consensus input, add a freshness check, add a team-code crosswalk, add an interim suspension list (fable-table-stakes' T1/T5/T9/T4) | **Mostly done and tested** — these were Fable's loudest alarm and have since landed (half-PPR CSV ingested, freshness tripwire wired into every board build, team-code crosswalk shipped, suspension mechanism wired with an honestly-empty list). |
| Build a scripted, repeatable UI regression check ("acceptance harness") to stop the founder from being the only regression detector (fable-acceptance-harness) | **Built and merged** — `npm run smoke`, 16/16, screenshots produced automatically. |
| "No ADP source exists to test the model's availability claims against" (implicit premise behind several data-source recommendations, e.g. fable-consensus-claim and parts of fable-schedule-feasibility) | **False now** — two ADP sources exist and are captured daily (an existing proxy, and FFC's real half-PPR feed). |

## Got more important (say so plainly)

- **The hardcoded-to-Westwood need-math** (item 4 above) — moved from "a fragility worth fixing
  eventually" to "the direct blocker for a feature the founder asked for this week."
- **The ticket-numbering fix** (item 8) — moved from "a nuisance that's been fixed" to "a nuisance
  that's been partially fixed and is still actively causing collisions," because more parallel work
  is now happening (cloud sessions, multiple branches) than when Fable first measured it.

## What I did not reach

All 18 review files were read in full. Given the volume, this document reports Fable's own
conclusions and recommendations rather than re-deriving or re-checking every number inside them —
per the task's own instruction not to re-argue Fable's findings. Two items were spot-checked
directly against the current code (the ticket-allocator fix, and whether λ reaches the shipped
recommendation) because they were cheap to check and central to the "still live vs. dead" call.
