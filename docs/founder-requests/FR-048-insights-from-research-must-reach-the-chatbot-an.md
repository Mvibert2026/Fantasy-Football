---
ID: FR-048
STATUS: NEW
SOURCE: chat 2026-07-29, PM session
RAISED: 2026-07-29
---

## Request
Insights from research must reach the chatbot and the draft screen

Founder's own words:

> "For the website chatbot, these answers you're giving me to research and strategy should
> absolutely be accessible - and in a perfect world these insights would show near relevant picks in
> the middle screen there on the draft page"

And, on the specific finding that prompted it:

> "Like this is great: But there's a real finding underneath, and it's better than the original idea.
> Around picks 75–113 — roughly rounds 8 to 11 — a tight end costs you nothing against the
> alternative. Same expected value as taking a receiver there, better than a running back, far better
> than a quarterback. And it buys a 25% shot. One pick there beats three darts in the last rounds,
> and costs two fewer picks."

## Why it matters

**Every research finding this project produces currently dies in a markdown file.** The tight-end
result above is measured, holds a confidence interval, is tied to a specific pick range — and the
only way the founder learned it was a chat message that will be discarded. On draft day he will be
at picks 75–113 with none of it on screen.

This is the gap between having an edge and being able to use one. It is also what the whole
research programme is *for* — an insight nobody can act on at the moment of decision is a document,
not a product feature.

## Initial read

Not the founder's own words — PM's read. Two deliverables, and the first is the hard one.

**1. Findings need a machine-readable home.** Today they live as prose in `docs/ranking/` and
`docs/research/`. Nothing can query them. What is needed is a small, structured store — the finding,
the pick range or condition it applies to, its strength, its confidence interval, and the source
document. The pattern already exists: `docs/assistant-context.md` was created for exactly this
reason (curated current-state-only summary, edited in place, never appended) and is what the
assistant is supposed to read instead of the raw decision log.

**Discipline that must not be lost in transit:** the tight-end finding is 25% with an interval, from
n=16, in a specific band, on a proxy for ADP because no ADP history exists yet. A tile reading
"TAKE A TE" would be a lie. The uncertainty travels with the claim or the claim does not travel.

**2. Surfacing at the point of decision.** The founder's ask is that it appears *near relevant
picks*, not on a separate page. That makes it a contextual trigger — pick range, position, roster
state — which is a design problem before it is an engineering one.

**Nothing enters this store that has not passed the project's own gates.** The TE result is
explicitly exploratory: nothing registered, nothing shipped, and thread 087 has the confirmatory
window with `strategist` for exactly this reason. Showing an unregistered finding on the draft
screen would be the project overriding its own evidence standard at the one moment it matters most.
