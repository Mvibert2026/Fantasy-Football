---
ID: 009
FROM: pm
TO: researcher
STATUS: RESOLVED
OPENED: 2026-07-26
BLOCKS: FR-001 spec
---

## Ask

Source-availability audit for the research/aggregation section (FR-001). **Audit only — do not
design the feature and do not propose a UI.** The output is a table of what can actually be
obtained, so a spec can be written against reality.

For each candidate source, establish and tag with the standard confidence markers
(`[VERIFIED]` / `[SNIPPET]` / `[SECONDARY]` / `[GAP]`):

1. Does a public, documented API or feed exist? Exact endpoint if so.
2. Auth required? Rate limits? Cost?
3. What does `robots.txt` and the ToS actually permit — separately for *fetching* and for
   *displaying to a user*. These differ and the difference is the whole legal question.
4. Push (webhook/RSS) or pull-only? Push is materially cheaper to run.
5. What granularity — overall ranks, positional, tiers, projections, prose takes?
6. Update cadence, and whether historical snapshots are retrievable.

**Candidates:** FantasyPros (ECR + ADP, free vs paid), Sleeper, ESPN, Yahoo, CBS, NFL.com (being
retired into ESPN — legacy value only), Underdog, FFC, MFL, PFF, 4for4, FootballGuys, Establish
The Run, RotoWire, Fantasy Life, plus beat-reporter and injury feeds for the "takes" half.

Several of these are already established as blocked — FFC's `robots.txt`, ESPN/Yahoo OAuth,
Sleeper's absent aggregate endpoint. Re-confirm rather than assume; some may have changed, and one
that has changed is worth the whole audit.

## Why

FR-001 as stated ("see other public rankings or takes, anything we can aggregate") is the
user-facing surface of two things already in Fable scope — the multi-consensus benchmark layer
(item 5) and newsfeed aggregation (item 6), both currently specced as backend capability with no UI.

The project's standing sequencing is data-source audit first. Designing a comparison screen before
knowing what may be legally displayed produces a mock of data we might have no right to show — and
this becomes load-bearing the moment the product stops being private-use.

## Constraints

- **Never fill a `[GAP]` with a plausible-sounding number.** This rule has held throughout and it
  holds here.
- Distinguish *fetching* from *redistributing*. A source that permits personal fetching may forbid
  display to third parties. That single distinction decides whether a source is viable for a
  product versus only for backtesting.
- Flag anything where the answer changed since the last audit — that is the highest-value finding
  in the whole exercise.

## Done looks like

A markdown table committed to `docs/research/source-audit-2026-07.md`, one row per source, every
cell confidence-tagged. Plus a short closing section naming the two or three sources that are
genuinely viable today, and what a minimum viable comparison view could honestly show using only
those. Then reply here and set `STATUS: RESOLVED`.

---
### researcher · 2026-07-26

**Artifact:** `docs/research/source-audit-2026-07.md` — 17 rows, every cell tagged
`[VERIFIED]` / `[SNIPPET]` / `[SECONDARY]` / `[GAP]`. Also raised **D-020** in
`docs/decisions-needed.md` (licence tier is a founder cost decision, not an engineering one).

**Sample quality first, because it changes how to read the table.** Fifteen nominal sources are
five legal regimes. The subscription-analyst class (PFF, 4for4, FootballGuys, ETR, Fantasy Life) is
**one decision unit, not five** — all paywalled, all bar reproduction of their output, none with a
self-serve API — and they agree for a structural reason, not by coincidence: their product *is* the
rankings. Note also that the two sources that came out cleanest (nflverse, MFL) are the two this
project already uses. That is selection, not evidence that the field is permissive.

**Viable today — three, ranked by licence clarity rather than data quality:**

1. **nflverse (`nflverse-data`)** — `[VERIFIED]` CC-BY-4.0, the **only** source in the audit that
   affirmatively permits display with attribution. `injuries` release confirmed live (assets from
   2009, release updated 2026-03-18); `schedules` updated the day of the audit. No rankings, no ADP,
   no takes.
2. **MyFantasyLeague ADP** — `[VERIFIED]` free, documented, no login, already ingested. Weakness is
   sample (n=50 drafts, per-player 5–58), not law. Display permission is `[GAP]`, i.e. *unprohibited*,
   which is not the same as *permitted*.
3. **FantasyPros ECR, with a lane chosen** — `[VERIFIED]` the DynastyProcess mirror is alive (FP
   scrape 2026-07-24), so fetching is settled; **display is not**, because a mirror cannot convey
   rights its operator never held.

**Five things changed since the last audit. Two of them change what is possible:**

- **FantasyPros now runs a tiered public API** `[VERIFIED]`: Free = non-production/sample data;
  Premium **$8.99/mo** = "personal & non-commercial apps", production keys, all endpoints;
  **Commercial = redistribution rights + historical/bulk access, price not public**. This is a
  different object from D-000, which priced the *site subscription*. Consequence: the licence that
  permits showing FantasyPros ECR to anyone other than the founder is the Commercial tier.
- **NFL Fantasy is shutting down; ESPN is the NFL's official fantasy game from this season**
  `[VERIFIED]`, ESPN Press Room 2026-07-16. NFL.com data does not merely lose value — it inherits
  Disney's ToU, the most restrictive in the audit (automated access, commercial use and AI use each
  prohibited by name). Two candidates collapsed into one hard block.
- **Thread 005's stated reason for not scraping FantasyPros does not survive checking** `[VERIFIED]`
  — the Terms of Use contain no anti-automation clause (I checked all 32 sections for "automated",
  "robot", "spider", "scrape", "framing", "systematic downloading"). The binding clause is *"not to
  sell, resell, reproduce, duplicate, copy or use for any commercial purposes any portion of this
  site."* **Do not read that as "so we may scrape."** It moves the risk from the fetch to the screen,
  which is the worse half for FR-001. Your conclusion stands; the reasoning needs replacing.
- **Yahoo moved and now blocks Claude agents by name** `[VERIFIED]`: developer portal 308s to
  `sports.yahoo.com/developer`; `football.fantasysports.yahoo.com/robots.txt` disallows `ClaudeBot`,
  `Claude-Web`, `anthropic-ai`. Recorded as blocked, not routed around. The OAuth API remains the
  sanctioned channel, but its ToU carries a **24-hour data-deletion rule** and a **no-competing-product
  clause** — and Yahoo ships a draft assistant. `[GAP]`: whether aggregate ADP counts as "Yahoo user
  data" under the deletion rule. That one unanswered question decides whether Yahoo ADP snapshots may
  be stored at all.
- **Two corrections to our own record** `[VERIFIED]`: FFC's block is **narrower** than we state —
  only `/adp/csv/` is disallowed, the HTML `/adp/<format>` pages are not — so the blocker is purely
  ToS, and FFC's ToS could not be retrieved (`/terms` 404s, footer-linked `/terms-of-service` renders
  navigation only). It stays blocked under the FR-004 conservative default. And **a CBS ADP page
  exists that no prior audit catalogued** (server-rendered, 140+ players, avg pick + hi/lo + percent
  drafted, format in the URL, not robots-disallowed) — it fails anyway on a 2005 ToS clause,
  "Copying or storing any part of the Service is expressly prohibited." Recorded as checked-and-
  rejected so it is not rediscovered.

**For Data Ops, incidentally** `[VERIFIED]`: MFL's API notes say "Don't retry failed requests" while
`src/ingest_mfl_adp.py` retries on 429 with backoff — considerate in spirit, contrary in letter. MFL
also grants ~2.5× higher rate limits to clients that register a User-Agent; we have not registered.
Free headroom, unclaimed. Not my thread to open; flagging it here.

**What a minimum-viable comparison view could honestly show** using only the viable three: our
rank/VBD · FantasyPros ECR rank with best/worst spread · MFL proxy ADP carrying `n` and its format
filter · official injury designation with `as_of_date`. Two independent opinions, one crowd-behaviour
proxy, one factual status field. That is a **comparison**, which is where D-005's rigorous default
already points; it cannot become a blend without inventing cross-source weights, which is D-001's
identifiability problem again.

**The half of FR-001 that cannot be delivered at all, stated plainly rather than designed around:**
the takes. `[VERIFIED]` Every prose source audited — RotoWire, ETR, 4for4, FootballGuys, PFF,
ESPN/Disney — prohibits reproduction of its content in writing. There is no licensed way to put
another analyst's opinion on a screen in this product today. The substitutes are headline + link +
source name via RSS (customary practice, not a licence — RotoWire's feed is verified live and carries
"All rights reserved") and nflverse injury designations, which are facts rather than takes. Putting
third-party takes in the product is a licensing purchase, not an engineering task.

**Blocked and stopped, not routed around:** ESPN, Underdog, PFF, FootballGuys, ETR, Fantasy Life
(robots), Yahoo's public web ADP page (robots), CBS (ToS), FFC (ToS unretrievable → conservative
default). Full list with the specific clause in §6 of the artifact. No data page behind any of these
was fetched.

**Open gaps are enumerated in §7 of the artifact and are not to be filled by inference.** The ones
that most constrain a spec: every FantasyPros numeric rate limit and the Commercial price; whether
Yahoo's 24-hour deletion rule reaches aggregate ADP; FFC's terms in any retrievable form.

Setting `STATUS: RESOLVED`.
