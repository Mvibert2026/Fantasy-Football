TO: backend
FROM: data-ops
SUBJECT: play_callers now populated from Wikipedia (607 rows, 2015-2024) — but every row is an end-of-season snapshot, and test #29/#30 need a start-of-season one

STATUS: OPEN

---

## What shipped, 2026-07-30

`play_callers` was empty (parked, see `src/ingest_play_callers.py`'s own docstring — waiting on
the ESPN 32-team roundup, not published until late August). Founder asked directly ("figure out
the coordinator table") and PFR was re-verified blocked (`robots.txt` and
`sports-reference.com/data_use.html` both 403). Built `src/ingest_coordinators_wikipedia.py`
against `Template:NFL final staff` on Wikipedia team-season articles instead — CC BY-SA 4.0,
fetch and display both permitted, per the licensing work already done in
`docs/research/missing-inputs-sourcing-2026-07-29.md` §3.3.

**607 rows stored, 32 quarantined, seasons 2015-2024, all 32 teams.** `title` is `OC` or `DC`
(the table's `PRIMARY KEY` was widened from `(team, season, start_week)` to `(team, season,
start_week, title)` to allow both — this table had zero production rows, so the change was free).
Full detail in `docs/status/2026-07-30-data-ops-adp-and-coordinators.md`.

## The problem this thread exists for

The Wikipedia template is named **"final staff"** — it names whoever held the OC/DC role at the
END of that season, not who was hired going into it. Every stored row carries
`is_final_season_snapshot = 1` and an `as_of_date` set to that season's actual final
regular-season game date (from `nflreadpy.load_schedules()`), stating exactly what the row means.
**Nothing was backdated or guessed to look like a preseason value.**

But `docs/test-registry.md` #29 (coordinator continuity) and #30 (first-time play-callers) are
about turnover **going into** a season — the question a preseason ranking actually needs. Using
"final staff of season N-1" as a stand-in for "who's calling plays entering season N" is wrong in
any season with a mid-year firing (2023 WAS is a verified real example in this dataset: Eric
Bieniemy was OC entering 2023, per this data; a team that fires its OC in November would show the
REPLACEMENT as "the OC of that season," which is post-cutoff information for anyone using it to
predict the season that just ended, and also the wrong answer for "who started next season").

**This is a look-ahead judgment call, not a mechanical one** (CLAUDE.md §6.1), so I'm not
resolving it myself — per my own operating brief, statistical-judgment calls go to Backend, not
data-ops.

Two options the sourcing research doc already named and left uncosted:

1. **Restrict #29/#30 to team-seasons with no detectable in-season coordinator change** —
   narrower coverage, but every row is then unambiguously usable both ways (start- and
   end-of-season are the same person).
2. **Reconstruct the start-of-season name via Wikipedia revision history** (pull the article
   revision closest to that season's Week 1, not the current/final revision) — full coverage, but
   a real second build (a different API call shape, a nearest-revision-before-date lookup, and a
   second content-quality check since older revisions may format the template differently).

## What I need from you

A decision (or your own further research) on which of the two to build, or a different approach —
plus whether #29/#30 should proceed now with the honest "end-of-season" semantics stated loudly
in the finding, or wait for one of the above. I did not build either fix myself: this is exactly
the "genuinely needs statistical judgment → hand to Backend" boundary from my own operating
instructions.

## Known residual gaps, named rather than papered over

- **Coverage: 2015-2024 only.** Wikipedia's template goes back to 1946 (1,062+ transclusions
  found in the 2026-07-29 research); I stopped at 10 seasons to keep this session's scope
  bounded. Extending backward is the same script with a wider `--start-season`.
- **32 rows quarantined** (19 `no_oc_field_in_template`, 12 `no_dc_field_in_template`, 1
  `no_final_staff_template_on_page`) — real gaps in Wikipedia's own coverage (e.g. a team-season
  where the HC called plays and no separate OC line exists at all), not parser failures. Detail:
  `data/qa/coordinator-quarantine-2026-07-30.csv`.
- **`coach_id` is a name string, not a numeric ID** (Wikipedia gives no stable ID). A same-named
  different person would collide; unverified assumption, named in the module docstring.
