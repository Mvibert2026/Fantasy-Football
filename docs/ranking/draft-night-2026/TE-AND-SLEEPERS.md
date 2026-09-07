# Tight ends and late-round sleepers — Westwood, 7 Sep 2026

Built from the 9/07 half-PPR ECR (135 experts) plus two measured findings from this project's own
campaign. Everything with a number attached is computed or cited; the judgment calls are marked.

---

## 1. Tight end is a barbell, and the middle is the trap

**TE is the only position whose last starter falls outside the top 100.** In a 10-team Westwood
roster (1QB/2RB/3WR/1TE/2FLEX/1DEF):

| Position | Last starter | Goes at overall ECR |
|---|---|---|
| RB20 | Cam Skattebo | 53 |
| WR30 | Mike Evans | 63 |
| QB10 | Dak Prescott | 76 |
| **TE10** | **Travis Kelce** | **105** |

TE1 (Bowers) goes at 17 and TE10 goes at 105 — an **88-pick spread, the widest of any position.**
That is the whole TE argument in one number: waiting at TE costs less draft capital than waiting
anywhere else.

### The tier structure is genuinely lumpy

| Tier | Count | ECR range | Who |
|---|---|---|---|
| 2 | 1 | 17 | Bowers |
| 3 | 2 | 25–41 | McBride, Loveland |
| 4 | 1 | 55 | Warren |
| **5** | **5** | **68–89** | Kraft, Fannin, LaPorta, Pitts, Kittle |
| **6** | **7** | **105–129** | Kelce, Kincaid, Likely, Goedert, Andrews, Ferguson, Johnson |

**Twelve broadly interchangeable tight ends between ECR 68 and 129.** That is four to six rounds
of a position where the market cannot separate the candidates.

**The implication:** the two defensible plays are *Bowers or McBride at their price*, or *wait and
take from the tier-5 block (rds 7–9), and if that's gone the tier-6 block is 7 deep (rds 11–13).*
The bad zone is TE3–TE4 — Loveland at 41, Warren at 55 — where you pay a near-premium and still
do not get a tier-1/2 player.

**Caveat, and it matters:** ECR tells you what a player *costs*, not what he's *worth*. I cannot
compute the projected-points gap between TE1 and TE10 — that needs the projection pipeline, and
the database is not in this container. The tier boundaries are the experts' own statement about
where the cliffs are, which is a reasonable proxy, not a measurement I made.

### Our own campaign's read on TE

`docs/CURRENT-STATE.md`: at the 10-player floor the usable season count is **QB 10 / RB 9 /
WR 11 / TE 7 — "TE gains nothing from tier 2."** The advanced-analytics factor panel added
nothing at tight end, and TE had the thinnest usable history of any position.

Read honestly, that is as much a data-depth finding as a predictability one. But it points the
same way as the market structure: **TE is the position where sophistication paid off least.**
Don't over-think it.

---

## 2. Sleepers, defined as something measurable

A "sleeper" is usually a vibe. The ECR feed carries each player's **most bullish expert**
(`rank_min`) alongside the consensus, so it can be made concrete:

> **upside = ECR rank − most optimistic expert's rank.** A big number means somebody who does this
> for a living thinks the room is badly wrong.

Biggest disagreements between ECR 90 and 200 (rounds 9–20):

| Rd | ECR | Player | Pos | Upside | sd |
|---|---|---|---|---|---|
| 16 | 156 | **Josh Jacobs** | RB52 GB | **+114** | 49.2 |
| 18 | 179 | Malik Washington | WR72 MIA | +86 | 35.1 |
| 20 | 197 | Ja'Kobi Lane | WR76 BAL | +75 | 42.5 |
| 15 | 147 | Jordyn Tyson | WR57 NO | +73 | 30.6 |
| 20 | 200 | Cade Otton | TE28 TB | +71 | 28.9 |
| 18 | 171 | T.J. Hockenson | TE21 MIN | +69 | 30.5 |
| 18 | 176 | Keenan Allen | WR69 IND | +63 | 46.3 |
| 14 | 137 | Deebo Samuel Sr. | WR55 SF | +58 | 31.7 |

**Josh Jacobs is the single largest disagreement on the entire board.** Consensus has him in round
16; at least one expert has him at pick 42. A spread that wide on an established player almost
always means a situation in flux rather than a difference of opinion about talent.

**I cannot tell you why.** There is no news or injury feed in this environment — that capture was
built but parked. What this list does is tell you *exactly where to spend your last hour of
research*. It localises the question; it does not answer it.

---

## 3. The one finding from our own work that should change your late rounds

This is the most valuable thing this project produced, and it is not something the market's board
tells you. From `docs/fable/M2-findings.md` §M2-1, measured on the frozen v1 panel with
pre-registered diagnostics:

> **v1's entire deficit against both crowds sits in one channel — projected games.** Substituting
> realised games at fixed per-game rates flips *every* losing cell to a win. The excess rank error
> concentrates in **players who missed ≥4 weeks the prior season** (86–131% of the market-panel
> excess). On players with a full prior season, v1 was already **at or better than parity**.
>
> "What consensus knows is who is going to play."

Two things follow, and they are the opposite of each other:

**a) The late-round trap is the discounted name coming off a lost season.** That is precisely the
population where our modelling failed worst and where the market's information advantage is
concentrated. The instinct — *"he was a stud two years ago and he's free in round 18"* — is the
single most measurable way this project got beaten. The current fallers list is full of exactly
this profile: James Conner (ECR 240, −8), Isiah Pacheco (195, −9).

**b) For players who were healthy last season, the crowd has no special edge.** At parity or worse
than us. So a full-season player where you have a genuine read is where your own opinion is
actually worth backing — and a high-`sd` full-season player is the best of both.

That is a sharper rule than "draft upside late": **discount for missed time more than the ADP
already has, and spend your risk budget on healthy players the room disagrees about.**

---

## 4. What I can't tell you

- **Points, only prices.** No database in this container, so no projections, no VBD, no
  replacement-level point values. Everything above is market structure plus cited findings.
- **Why any individual is falling or rising.** No news/injury/depth-chart feed.
- **Anything from our proprietary board.** It never finished. The factor campaign graded 1 of 8
  batches; the model that was supposed to beat consensus does not exist. What's above uses
  consensus as the input, which is exactly what the project set out to avoid — that framing is
  honest about where this stands, not a substitute for it.
