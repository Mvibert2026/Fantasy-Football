---
ID: FR-072
STATUS: ANSWERED
SOURCE: coordinator relay, 2026-07-30 ranker session
RAISED: 2026-07-30
---

## Request

Rank positions by volatility for the founder's own knowledge, and per roster slot — not just per
player.

**NO `ID:` FIELD ON PURPOSE.** `tools/founder_requests.py new` allocated **FR-072** for this in
worktree `agent-a2668c91115660701`, which is a collision: this worktree only carries FR-001..FR-071,
while FR-072 ("Ok for our model, let's do the other positions too, why just WR") and everything up to
FR-095 already exist on branches this worktree does not have. The allocated file was reverted to this
unallocated form so PM's sync assigns a real ID. Same failure mode as threads 093/094 and ADR-054/055,
which `tools/handoffs.py check` is currently red on.

## Founder's own words

> "volatility matters for archetype and I'd like to know also which positions tend to be more
> volatile in general, for my knowledge"

Relayed with two framing requirements from the coordinator: normalise (report a scale-free measure
alongside the raw one and say which is decision-relevant), and answer it **per roster slot** given
this league's 1 QB / 3 WR / 2 RB / 1 TE / 2 FLEX shape, since a TE and a WR with identical CV do not
contribute identical risk to a weekly lineup.

## Status

**Answered in the same session.** `docs/ranking/fr086-volatility.md` §1.
Code `experiments/volatility/volatility.py`. Raw `data/qa/fr086-volatility-2026-07-30.json`.

**Per player** (8,703 player-seasons, 1999–2024, this league's scoring, bonuses stacked):
WR CV 1.084 · RB 1.047 · TE 1.002 · QB 0.573. **RB vs WR is a clean NULL.** The only robust
position-level statement is that QB is ~45% less volatile than every skill position (all three
comparisons SURVIVES). Reporting on raw SD would rank QB *most* volatile (7.42, the highest of any
position) and would be arithmetic, not insight.

**Per roster slot**, using ADR-029's measured flex split and a **measured** same-position weekly
correlation of +0.001 to +0.009 (so the √k diversification is valid rather than convenient):
**TE 1.002 · RB 0.600 · QB 0.573 · WR 0.545.** The ordering inverts. WR — the most volatile player
type — is the least volatile slot group because you start four of them; **the TE slot is the most
volatile thing on this roster, by 67% over the next worst**, because there is one of it and ADR-029
measured a TE winning a flex slot in 2 of 26 seasons.

Also measured, since it follows directly: at equal expected points, **team-level variance is worth
about half a percentage point of title probability across a 3.3× range**, and the "worse getting in,
better once in" hypothesis is not supported — P(title | made playoffs) is flat too.
