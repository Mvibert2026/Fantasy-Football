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
