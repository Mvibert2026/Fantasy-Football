---
ID: FR-027
STATUS: NEW
SOURCE: chat session 2026-07-29 (PM takeover)
RAISED: 2026-07-29
---

## Request
Two tiers this season - deep custom Westwood, generic modelling for ESPN and Yahoo leagues via connected settings

> "So i think for this season we need two things, a custom set up and calculations for westwood, then
> dynamic selection and generic modelling (no insights like we have for westwood participants) for my
> espn and yahoo leagues (ideal would be API in and use connected settings)"

Founder's own words, 2026-07-29.

## Why it matters

This is a **direction statement, not a feature request**, and it settles a question the project has
been carrying implicitly: how much of the product is Westwood-specific and how much is general.

The answer he gives is a clean two-tier split:

- **Westwood — deep and custom.** Its exact scoring including stacking yardage bonuses, its roster
  shape, and — the part nothing else gets — **opponent insight**, because he knows the ten humans in
  it and how they draft.
- **ESPN and Yahoo leagues — generic.** Correct settings and correct arithmetic, but explicitly *no*
  opponent modelling, because he does not know those drafters. He named that exclusion himself,
  which is the right instinct: modelling strangers' tendencies from nothing would be invention.

**It also reverses a recorded decision.** `docs/pm/MEMORY.md` §2 lists the ESPN league as "**Deferred
out of this season** by founder decision." That deferral is now lifted, for the generic tier only.

## Initial read

**The blocking dependency is already on the correctness floor, and this promotes it from hygiene to
critical path.** The first of the six standing priorities records that the model's assumptions about
the primary league are **hardcoded rather than read from configuration** — `live_availability.py`
takes no config, `run_availability.py` bypasses the config path whenever the league is primary, and
no test checks that two different roster shapes produce different survival numbers. It is *correct
today by accident*.

Generic modelling for arbitrary leagues is **not buildable on top of that**. A model that hardcodes
one league's roster shape and positional demand cannot serve a second league honestly — it will
produce confident numbers computed for Westwood and present them as answers about ESPN. So the fix
is no longer a tidy-up before mock collection; it is the enabler for this entire second tier.

There is a partial precedent worth reusing rather than rediscovering: League 2 ("Ethan's Expert
League", Yahoo) already has a real `LeagueConfig`, its own measured replacement levels, its own
board export, and 6 passing tests. That was built by hand. **The generic tier is essentially that
process made repeatable and driven from real settings rather than a transcribed screenshot.**

**On "API in and use connected settings" — the two providers are not equivalent, and this must not be
promised as one thing:**

- **Yahoo has an official OAuth Fantasy Sports API.** `CLAUDE.md` §10 explicitly prefers official
  OAuth over browser automation, so this is the sanctioned path and is likely viable. A researcher
  pass on the Yahoo API was already running when this was raised, for a different question.
- **ESPN has no official public fantasy API.** `docs/pm/MEMORY.md` §4 records ESPN alongside Yahoo
  and CBS as having **explicit written prohibitions on automated collection**. Reading his own
  league through ESPN's private endpoints with his own session cookie is his data, but it is still
  automated access against a recorded prohibition. **That needs a deliberate decision taken the way
  the FFC one was — by asking, not by assuming.** Do not build it first and raise it after.

The honest fallback if ESPN stays blocked is manual settings entry, which is how both existing
leagues were configured and takes minutes.

**Sequencing, and the capacity question that should not be glossed.** Westwood drafts **7 September**.
The founder's own bar — the three model questions — is unmet, availability has zero calibration
drafts, and mock collection has not started and is itself gated on the same config fix. This request
is real and correctly scoped, but it competes for the same weeks. **Recommend: the config fix
immediately (it serves both tiers), the generic tier scoped only after the availability work has a
verdict, and no promise that all three leagues are equally supported by 7 September.**

## Update (2026-07-29, frontend)

The UI-expression slice of this is done -- not the whole request (API-in / connected settings is
still untouched). `docs/design/TWO-TRACK-EXPRESSION.md` speced how a screen should say "this
league is the generic track" rather than reading as broken; built this session:

- League selector carries the track on every option (a ●/○ marker per league, before it's even
  selected) and a compact PRIMARY/GENERIC badge for whichever league is loaded, both reading
  `league.json:league_id`/`scoring_ruleset_note` -- real, sourced, computed once at sync time, not
  guessed client-side.
- `StrategyGuide`'s old single "Not available for this league" string (conflating "generic, by
  design" with "not yet run") is split by track.

STATUS left at `NEW` -- this closes the "does it read as broken" complaint for the screens
touched, not the deeper direction (API-in, connected settings, opponent modelling logic itself).
See `docs/founder-requests/FR-042-*.md`'s resolution for the backend half (the actual scoring
separation this UI is now honest about), and `docs/ideas-inbox.md` (2026-07-29, frontend) for
scope notes on what was deliberately left out this pass (`Opponents.tsx`, out of this session's
file ownership).
