# Handover to the PM agent — 2026-07-29

You are taking over from a PM that ran outside the repo and could not read files. **Read
`docs/pm/MEMORY.md`, `docs/pm/ROLE.md`, `docs/pm/CHARTER.md` and `docs/pm/PLAYBOOK.md` before
acting.** Then verify state rather than trusting this list.

Challenge every premise below. Several were written from memory by a PM with a documented habit of
asserting things it had not checked.

---

## 1 · Get the founder to zero approvals

He should not approve anything. **The local protections were compensation for a risk that no longer
exists** once work happens in disposable cloud sandboxes.

- Remove the `PreToolUse` hook and its blocking rules.
- Remove the approval rules that force prompts on deletions, force-pushes, credentials.
- Drop the command-style restrictions from dispatches — no chaining, no leading `&` — they exist only
  to avoid stopping on his machine.
- Prune the accumulated permission entries; they sit behind a wildcard and do nothing.

**Do this only for cloud sessions.** Anything still running on his Windows machine keeps them. Confirm
which context you are in before stripping anything.

**What does not get removed:** verify before instructing · evidence closes work · nothing asserts a
fact it did not derive. Those are about truth, not safety, and they apply everywhere.

## 2 · Finish the move off his machine

- Confirm the clean-clone rehearsal passed — fresh clone, rebuild the database, both suites green.
- Confirm a **scheduled** ADP capture run succeeds on GitHub, not just a manual one.
- Then have him disable the Windows scheduled task. Not before.
- Note what still requires his computer, if anything, and tell him plainly.

## 3 · Check the ADP capture is the right scoring format

His league is **half-PPR with stacking yardage bonuses**. If the daily capture requests standard
scoring, the availability model is learning from the wrong market — receivers come off the board
earlier in PPR formats. Report the parameter and the file, and what changing it would cost.

## 4 · Make the handoff system efficient

He asked whether the mailbox is now obsolete. Half of it is. It does two jobs: **message-passing**
between sessions that could not talk to each other, and a **durable backlog**. You dispatch subagents
directly, so the first job is largely gone; the second is not.

Roughly 45 tickets are open, most from the project's first two days, and reading them you cannot tell
which are live work and which were conversations that ended.

**Fable mandate K already frames this properly** — `docs/fable-mandate-K-2026-07-28.md`, item B, with
the measured failure record and five objections to press. **Do not re-derive it, and do not scope it
yourself** — the PM is the main user of that system and cannot judge it cleanly.

Two things worth fixing regardless: the numbering tool should **refuse a hand-typed number** rather
than asking agents not to use one, and there is a rescued mock-draft-capture branch that was never
merged or judged.

## 5 · The six — the correctness floor

1. **The app does not lie about itself** — including that the model's assumptions about the primary
   league are hardcoded rather than read from configuration. Correct today by accident. **Fix before
   mock collection begins.**
2. **Mode switching works** under a clock.
3. **Injuries and roster status.** Drafting a player who cannot play is his named unacceptable error.
4. **Mock drafts and the recording that makes them data.** He joins Yahoo rooms and autodrafts —
   minutes each. The recording must land before the first one.
5. **On-the-clock usability.**
6. **The daily capture keeps running.** Now on GitHub Actions.

## 6 · The founder's bar — this outranks the six

> "If I don't have those three things in place, I don't want to use the tool for my real draft."

The best **bottom-up rankings**, the best **availability prediction**, and the best **suggested-pick
model** — accounting for his roster, opponents' rosters and availability, dynamically during the
draft.

**These are this-season questions.** The previous PM framed them as off-season design work and was
overruled. Mandates are written and unrun: `docs/fable-mandate-M-2026-07-29.md`.

**Run M-2, availability, first.** It is the differentiator, it has zero calibration evidence behind
it, and it is the one where "how many mocks is enough" has an actual answer.

## 7 · Fable mandates written and unrun

`docs/fable-mandate-G-2026-07-28.md` — **G-B** per-league constant sweep *(urgent; first instances
already confirmed)* · G-C availability audit · G-D pre-mortem refresh · G-E test-coverage audit.

`docs/fable-mandate-K-2026-07-28.md` — **K-A** the recommendation decision *(the PM must not frame
it)* · K-C quantify the scoring-translation claim · K-D the kill list.

`docs/fable-mandate-2026-07-28-short.md` — F-B, F-C, F-D.

**Fable is the best value per token in this project.** Every sharpest finding came from it.

## 8 · Keep your own memory

Update `docs/pm/MEMORY.md` at every closeout and whenever something in it turns out to be false. **A
memory file that is merely old is worse than none, because it will be trusted.**

---

## How he wants to be treated

**English, not identifiers.** No ticket numbers, no Greek letters, no internal shorthand unless he
used it first. If something cannot be made clear without a label, say why it is unclear rather than
hiding behind it.

**Brief.** He has asked repeatedly. Lead with what changed or what he must decide, not with what you
did.

**Report by exception.** Silence is a valid update.

**Tell him when he is wrong, and when you are.** He has been right against the PM repeatedly — a false
tooling-bug claim, an archive instruction that would have broken a live fixture, the league size, the
framing of his own three questions. **He is still the most reliable error detector in this system.**

**Ask according to how he is working — he will tell you.** Stepping away or on a phone: decide, log
the reasoning, continue. At the computer: ask if it genuinely matters.

**The draft is Monday 7 September 2026.** Everything above serves that.
