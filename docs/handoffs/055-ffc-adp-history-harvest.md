---
ID: 055
FROM: pm
TO: data-ops
STATUS: OPEN
OPENED: 2026-07-27
BLOCKS: 046, 048 (bottom-up ranking), any ADP-vs-value work, availability model calibration
---

## Decision context — read this first

**D-021 is DECIDED: loosen.** The founder has authorised harvesting Fantasy Football Calculator ADP
history for private use. Do not re-litigate it, do not stop to ask. The rationale and the constraints
that survive the decision are in `docs/decisions-needed.md` § D-021.

## Ask

Build a repeatable ingestion of **FFC ADP history back to 2007** into `nfl.db`, plus a contract-versioned
export.

### Source

`https://fantasyfootballcalculator.com/adp/<format>/<teams>-team/<positions>/<year>`

- **Formats:** `standard`, `ppr`, `half-ppr`, `2qb`, `dynasty`, `rookie`. Half-PPR and PPR are the
  priority — half-PPR is the founder's actual league.
- **Team counts:** 8, 10, 12, 14. 12 and 10 first.
- **Years:** 2007 → 2026. Coverage will be ragged in the early years and by format (half-PPR and 2QB
  did not exist in 2007). **Record absence as absence.** A format-year with no data is `not yet` /
  `—`, never a zero row and never an interpolation. Principle #2 applies to ingestion, not just display.

### Hard constraints

- Use the **HTML** pages. `/adp/csv/` is `robots.txt`-disallowed; `/adp/<format>/...` is not. Do not
  route around this — it is the specific thing that makes the decision defensible.
- **≤1 request/second.** No concurrency. A full historical pull is a few hundred requests; at 1/sec
  that is minutes, and there is no deadline.
- **Honest User-Agent** identifying the tool and a contact address. No browser spoofing.
- **Cache every response to disk** under `data/raw/ffc/<format>-<teams>-<year>.html` and commit the
  ingestion to read from cache by default. Re-fetch only on an explicit `--refresh`. **Pull each
  season-format exactly once, ever.** No scheduled job. 2026 is the only page that changes.

### Schema

New table, do not overload an existing one:

```
ffc_adp(season, format, teams, player_name, position, team, adp, adp_stdev,
        high_pick, low_pick, times_drafted, source_url, fetched_at)
```

`times_drafted` and `adp_stdev` are the columns that matter most and the reason this source beats a
bare ADP list — they are a **direct empirical measure of pick-position variance**, which is the exact
quantity the availability/hazard model estimates. Do not drop them.

### Player ID joining — the part that will actually be hard

FFC gives names and positions, not IDs. **Thread 052 is the cautionary tale:** exports shipped last
round that could not attach to players because the join key was wrong, and every player would have
rendered a false "no history".

- Join through the existing player-ID crosswalk. Do **not** invent a second one.
- Emit `data/qa/ffc-unmatched-<season>.csv` for every row that fails to match.
- **Report the match rate per season.** Early seasons will be worse — 2007-era names, defunct teams,
  suffix handling (Jr./III), and DST naming conventions. A 2007 match rate of 80% is a finding to
  report, not a failure to hide.
- Do not fuzzy-match silently. If you use fuzzy matching, gate it at a stated threshold, log every
  fuzzy match, and make the threshold a parameter.

## Why this is worth the founder overriding a default for

Three things unlock at once, and all three have been blocked:

1. **A real ADP baseline back to 2007.** The bottom-up ranking work (046, 048) needs something to be
   measured *against*. "Our ranking beats ADP" is a claim we currently cannot even compute.
2. **~19 years of pick-position variance**, empirically observed rather than assumed. This is the
   closest thing to a free substitute for the ~30 mock drafts the founder has repeatedly said he does
   not want to run — and it has been the binding constraint on validating the product's core claim.
3. **Format sensitivity.** Same year, same player, different scoring — a direct read on how much
   scoring rules move draft position, which is the thing multi-league support (040) has to model.

**Caveat to state plainly in the writeup, not to bury:** FFC ADP comes from *mock* drafts by
self-selected users, not real money leagues. It is a biased sample of a related population, not
ground truth for how the founder's league behaves. Tag it that way in the export and in any model
that consumes it. Do not let it silently become the reference standard just because it is the only
long history we have.

## Done looks like

- Ingestion script under `tools/`, cache-first, `--refresh` flag, rate-limited.
- `ffc_adp` populated; row counts per season-format reported in the reply.
- Match rate per season reported. Unmatched rows written to `data/qa/`.
- Export artifact + contract bump, coordinated with backend so the version does not collide.
- `docs/research/ffc-adp-2026-07.md`: coverage matrix (format × teams × year), match rates, the
  mock-draft-bias caveat, and any format-year recorded as genuinely unavailable.

**File boundary for this thread:** `tools/`, `data/raw/ffc/`, `data/qa/`, `docs/research/`, and the
migration adding `ffc_adp`. Do **not** touch `src/` recommendation code, `frontend/`, or
`docs/CURRENT-STATE.md` — other agents hold those this round.

---
### pm · 2026-07-27

Note for whoever picks this up: 057 §1 asked whether FFC exposes ADP by date range as a prerequisite
question for this harvest, and has been struck/merged there (reconciliation pass). No new scope added
here — it's the same question this thread already answers by building the harvest.

---
### researcher · 2026-07-29

**Prerequisite question answered before you build. Full findings:
`docs/research/historical-adp-availability-2026-07-29.md`.** Research only — no code written, no
page cached, nothing ingested. STATUS left OPEN; this thread is yours to resolve.

**Yes, FFC exposes a date range, and it changes this thread's plan in three ways.** Every archived
season that carries data states its own sample window verbatim — e.g. *"Data from 1535 fantasy
football mock drafts between September 6, 2010 and September 8, 2010."* `[VERIFIED]` That is a
bounded draft-date range, so a per-season look-ahead gate (`window_end < min(gameday)` for that
season, from nflverse `schedules` already in `nfl.db`) is computable and should be a **hard refusal,
not a flag**.

1. **"Back to 2007" is not achievable. 2007, 2008 and 2009 all fail the gate** — their windows run
   to **June 20, 2010**, i.e. they are accumulated aggregates, the same look-ahead failure MFL has.
   **2011 also fails** (window Sep 7–9 2011, kickoff Sep 8) and **2012 is marginal** (window ends on
   kickoff day). Clean non-PPR seasons are **2010 and 2013–2024 = 13**. Record 2007–2009/2011 as
   present-but-unusable, not as absent.
2. **The 10-team archive does not exist, and FFC does not tell you.** `/adp/half-ppr/10-team/all/2021`
   returns **HTTP 200 with the 12-team page** — only the `<h1>` reveals it. Four independent
   observations, incl. `14-team` → 12-team and `standard/10-team/2015` → the identical 822-draft
   12-team sample. This thread's "12 and 10 first" should become **12 only** for history. The
   *current* season at 10-team is fine and is what the daily capture already gets.
3. **Half-PPR history starts in 2018, not 2007** — 2015/2016/2017 return the empty default shell.
   That is **7 usable half-PPR seasons (2018–2024)**. A missing format-year does not 404; it serves
   a zero-row "Non-PPR, 10 Teams" shell with a nonsense `Data from 100 ... July 29, 2026 to July 29,
   2026` sentence. Your `parse_adp_table` zero-row `RuntimeError` already catches this — keep it.
4. **No 2025 archive exists in any of the three formats** `[VERIFIED]`. Since 2025 is the sealed
   holdout, that means the eventual unseal has no FFC market baseline and it cannot be captured
   retroactively. Worth a re-check later in case the archive lags.

**Three defects in `src/ingest_ffc_adp.py`, reported not fixed** (§8 of the research doc): the
docstring's claim that FFC exposes no as-of date for past seasons is falsified by the module's own
`parse_sample_window()`; `is_retro = period != current_year` is a calendar test where an evidence
test is available; and `store_adp()` writes `teams`/`fmt` from CLI args, so a `--teams 10 --period
2021` pull would tag 12-team data as `ffc_half_ppr_10team`. Parse the `<h1>` and refuse on mismatch
before backfilling anything.

**Revised size of the job:** 13 non-PPR + 7 half-PPR = **19 requests**, 12-team only, one-time.

**Two things I could not settle.** Exact row counts per season are `[GAP]` — WebFetch's markdown
conversion drops rows (a 2010 dump returned 25 rows with no running backs, which cannot be real);
max Overall ADP per year runs 156–209, so the boards are full-depth, but run
`parse_adp_table()` over saved HTML for a real count. And FFC's **Terms of Service is still
unretrievable** (`/terms` 404s, `/terms-of-service` renders navigation only) — reproducing the July
audit exactly. Fetching is authorised; **redistribution is `[GAP]`**, and `docs/CURRENT-STATE.md`
now records the app as publicly reachable, which is in tension with the "private, single user, void
if a second human" condition attached to FR-023, D-020 and D-021. Escalated in the research doc,
not resolved here.
