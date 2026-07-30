# Competitor screenshots

Captured by the founder from live platforms, 2026-07-29. **These exist because agents cannot get
them.** Every Yahoo host blocks research agents by name, and two full research passes closed with
"zero behavioural observations of any competitor under a real clock" as their largest gap. Five
founder screenshots produced more competitive fact than both passes combined.

**What is here**

| File | What it shows |
|---|---|
| `yahoo-01-league-rankings-selector.png` | Yahoo's per-league pre-draft rankings selector |
| `yahoo-02-roster-and-stat-categories.png` | Roster positions and stat categories for a non-Westwood league — nine starters, one flex, **with a kicker**, versus Westwood's ten starters, two flex, no kicker |

**Not here, and worth chasing.** The founder also sent, in chat only, five screenshots of a live
Yahoo draft room and five of FantasyPros. Those are the more useful set and they are described in
detail — feature by feature — in `docs/founder-requests/FR-053-yahoo-draft-room-reference-capture-features-to-c.md`,
including its FantasyPros addendum. **Read that file whether or not you can see images.** It records
what was observed, not what was inferred.

The short version of what those showed:

- **Yahoo's centre pane is tabbed** — Players / Board / Results / Standings. That is FR-049.
- **Yahoo's Board tab is the periodic-table grid** — managers as columns, rounds as rows, cells
  coloured **by position**, undrafted cells showing their pick number so the grid doubles as the
  schedule. That is FR-044, and it confirms the founder's "pretty standard draft room stuff":
  follow the convention, do not invent a palette.
- **A "YOUR TURN — 14TH PICK" divider drawn across the ranked player list.** Close to FR-051, but
  expressed as a position in the list rather than a number in a column — probably better than either
  thing we specified.
- **FantasyPros' Draft Configuration** is the settings screen FR-040 is about to specify, already
  built by someone else: league type, scoring, draft type, **Opponent Pick Logic**, team count,
  **Draft Position with a Randomize button**, pick clock, per-position opponent bias.

**The founder's own verdict on both, and it is the strongest single piece of direction in the design
record:**

> "yahoo seems to have gotten worse and looks like a childs toy"
> "fantasy pros still looks pretty good"

He named his own bias — he has used FantasyPros for years. That makes the read more useful, not less:
it is the standard his eye will judge our screens against.

**One caution carried from thread 086.** "A competitor ships it" is evidence of convention, not of
value. That pass found a Yahoo-style feature users explicitly asked to have *removed*. Use these as
evidence of what people already know how to read, not as a specification.

---

## FantasyPros, second capture set — 2026-07-30

**Not saved as images.** These arrived inline and could not be written to disk. Recorded here in
detail instead, because the detail is what design needs and it is what survives.

### Draft Configuration — the screen FR-040 is about to specify, already built

**Sync Your League Settings From: [Yahoo ▾] [Sync Your League]** — one control, and it is the whole
of FR-040's ambition. Free tier allows one sync.

| Group | Options |
|---|---|
| League Type | 2026 Season · Dynasty |
| Scoring | Standard · PPR · Half PPR · **Custom (locked, paid)** |
| Draft Type | Snake · Linear · Salary Cap (locked) · Custom (locked) |
| **Opponent Pick Logic** | **Basic · Advanced (locked)** |
| Then | # of Teams `10` · Draft Position `7th` **[Randomize]** · Pick Clock `None` |

**Roster Positions** as separate steppers: QB 1 · RB 2 · WR 3 · TE 1 · **Flex 2** · **K 0** ·
DST 1 · Bench 6, plus "Show More Positions". **That is Westwood's exact shape** — the founder had
configured it. Note `K 0` is expressible; our own preset matrix cannot say that.

**Draft Against** — two columns, explicitly *chosen* rather than blended: Expert Rankings (All
Experts · FantasyPros Experts) against ADP (Composite ADP, plus six Best Ball ADPs — DraftKings,
Drafters, RTSports, Underdog, BB10 — and Yahoo/ESPN Pre-Draft Rankings, each with a VIEW link).

**Position Values** — QB/RB/WR/TE/DST/K/Rookies each a `Normal ▾` dropdown, all locked behind
payment. **This is FR-047's per-position opponent bias, shipped as seven dropdowns.**

### The live simulator

Left rail Rankings / Teams / Queue · centre **Suggestions / Cheat Sheets / Draft Board** · right rail
Picks with real manager names and *"Next turn in 7 Picks"*. Header: "You're on the clock! Pick 1.07
(7 Overall)". Suggestion cards carry a **"76% Experts"** share, an **Upside Mode** toggle, and a
locked **Draft Strategy** button.

### The one that matters most: their chatbot

A "Coach" panel, LLM-backed, **10 free messages**. Its four suggested prompts:

- *"Should I draft Jaxon Smith-Njigba or Amon-Ra St. Brown?"*
- *"Who's the backup RB for the Seahawks?"*
- *"What position should I draft next?"*
- **"Will Jaxon Smith-Njigba be available at my next pick?"**

**That fourth prompt is this project's signature claim, offered by a competitor as a chatbot
question.** The distinction is everything and it is the product argument in one line: theirs is an
LLM answering from general knowledge; ours is a Monte Carlo simulation with three sigma readings per
pick — **which is also uncalibrated, on zero of ~30 drafts, and must not be overclaimed either.**

Their own footer: *"Coach can make mistakes. Double check important info."* A blanket disclaimer
under every answer. `docs/assistant-persona.md` takes the opposite approach — uncertainty attached to
the specific claim, in the same sentence, rather than a standing caveat the reader learns to ignore.
**Worth keeping that contrast deliberately.**

### The player card, in full — the layout design asked about

Header band: photo, name at display size, `WR - SEA | Bye 11 | Age 24`, a **Draft Now** primary
button, and a scoring-format selector (`STD ▾`) so the whole card re-prices without leaving it.

**Four stats as a single strip, equal weight, no hierarchy between them:**

| ADP | ECR | Last Season | SOS |
|---|---|---|---|
| WR3 | WR3 | WR1 | 21st |

Every one is expressed **as a positional rank, not a raw number** — WR3, not 8.2. That is the
readable form under a clock, and it is worth noting against our own board, which shows overall rank
and raw ADP.

Then a bar reading **Latest News · Game Logs · Season Stats · Outlook · News & Analysis · Depth
Chart**, with **Full Profile →** pushed right as a separate escape hatch.

**Correction from the founder, who used it: that bar is not a tab set.** Verbatim: *"the bar across
the top just zooms you down to the section, you could scroll all the way down if you wanted."*

**It is a jump-to-section nav over one continuous scrolling page.** Everything is always present;
the bar is a shortcut, not a filter. That is a materially different interaction from tabs and the
distinction matters for the pane spec — tabs hide what you are not looking at, this does not.

Design should read this as evidence for the pattern it already flagged: the app's own top-level tabs
**swap the whole body**, so Predictions during a live draft removes the board and roster.
FantasyPros solved the same crowding problem without hiding anything. Whether that generalises from
a player card to a draft pane is design's call, but the option is now on the table and it was not
before.

**The `STD ▾` selector is a real re-pricing control** — it opens to **STD / HALF / PPR** and re-prices
the card in place. Confirms that a scoring switch on a player card is expected behaviour in this
category, not an invention.

**The AI panel, and this is the one to study rather than copy.** "Consensus Draft Sentiment, powered
by Coach AI": three meters — **OVERALL · UPSIDE · BUST** — each a five-segment bar with a word
(`Very High`, `Very High`, `Low`) and an ⓘ. Beneath, a paragraph of generated prose.

**Two observations, and they cut against each other.**

The meters are a genuinely good idiom: a five-segment bar plus a word survives greyscale, reads at a
glance, and refuses false precision — no "87% upside". Worth stealing as a *form*.

**What is behind them is the opposite of this project's standard.** The prose is confident,
sourced to nothing checkable, and hedged only by the standing "Coach can make mistakes" footer. It
says the ceiling case "probably" holds and names three specific worries. **Nothing states where any
of it came from or how strongly it is held.** A reader cannot tell an analyst consensus from a model
output from a paraphrase.

`docs/assistant-persona.md` forbids exactly this — every claim traceable to one retrieved item, no
number that is not verbatim in context, uncertainty in the same sentence as the claim. **The
constraint is not a limitation to design around; it is the difference between the two products.**
If we ship meters, they must be computed from something and say what.
