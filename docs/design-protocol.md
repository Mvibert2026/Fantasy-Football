# Design protocol

**Owner:** `design` · **Written:** 2026-07-27 · **Status:** true as of today, not aspirational

This describes how the design role actually works in this repo, including the parts that
do not work yet. Where a capability is missing it says so rather than describing the
intended end state.

---

## 1. The access constraint — read this first

**Design has read access to this repo and no write access.** I can read every file, search
the tree, and compare refs. I cannot commit, push, open a branch, or open a pull request.

This has two consequences that the rest of this document is shaped around:

- **Branch discipline is not something I can execute.** The instruction to work on my own
  branch, pull before starting and push at close describes a capability I do not have.
  I read at a named ref and produce files; landing them is a human or agent hop.
- **Every output of mine arrives as a file to be committed by someone else**, at a stated
  path, with the commit left to the PM or to frontend. If a design output is not in the
  repo, the most likely reason is that nobody landed it — not that it was not written.

`docs/handoffs/README.md` currently states *"design cannot read this repo"* and instructs
agents to mark threads `TO: design VIA: pm`. **The first half of that is now false** and the
`VIA: pm` hop is only needed in one direction. See §6.

## 2. What I own

The design system in this repo: `docs/design-system/`.

| Path | Contents |
|---|---|
| `docs/design-system/tokens.json` | Canonical tokens, both themes. Diff against this file. |
| `docs/design-system/components.json` | Component inventory — variants, states, screens, rules. |
| `docs/design-system/components/*.dc.html` | Reference files. Each opens standalone with every variant visible. |
| `docs/design-system/AUDIT.md` | Consistency findings and retrofit specs. |

A component is mine when it makes a **claim** that recurs — a shape of meaning, not a shape
on screen. Tokens, primitives, and the null vocabulary are the core of it. If two screens
render the same claim differently, that is my defect regardless of which screen shipped first.

## 3. What I do not own

Production screens, data wiring, and everything under `frontend/`, including
`frontend/ui/views/`. I do not edit them and I do not file gap lists against them as though
they were mine to fix.

Three things in production code are frontend's to uphold and mine only to specify:

- the data contract,
- the five-way null vocabulary — `—`, `<1%`, `0%`, `not yet`, `·` are five different
  claims and never substitute for one another,
- the traceability tests.

## 4. Where my outputs live and what they look like

Outputs are always one of three things, never prose alone:

1. **A component reference file** — `components/<name>.dc.html`, every variant visible,
   opening standalone. This is the artifact. A component described only in JSON is not built.
2. **An inventory entry** in `components.json` — claim, variants, screens, rule.
3. **A token change** in `tokens.json`, with the supersession recorded in the file.

Nothing I produce is a screen. If an output looks like a screen, it is a reference file
showing components in context, and it is not a spec for layout.

## 5. How I hand off

Per `docs/handoffs/README.md`, with two deviations forced by §1:

- I reply in-thread as `### design · YYYY-MM-DD`, one thread per session, no batching.
- **I cannot set `STATUS:` on a thread addressed to another role.** Rule 6 reserves
  `RESOLVED` for the `TO:` role. Where I have contributed to a frontend thread, my reply is
  a contribution and the status stays with frontend.
- Because I cannot commit, my reply text and any new-thread file are produced as files for
  the PM to land. A design reply that never appears in the repo did not fail to be written.

## 6. What I need from the PM

Four things, in order of how much they cost to keep doing manually:

1. **Land my files.** Everything I produce arrives as a path-matched file. Committing them
   is currently a human step and it is the only thing between my output and the repo.
2. **Correct `docs/handoffs/README.md`.** Design can now read the repo. Threads addressed
   to design no longer need `VIA: pm` for me to *see* them — only for me to *reply*.
   Leaving the line as-is means agents keep routing design questions through a human hop
   that is half-unnecessary, and `OPEN.md` keeps printing an inbox warning that is wrong.
3. **Address design threads to `design`.** My inbox in `OPEN.md` reads zero waiting while
   thread 058 — substantially a design-system question — sits in frontend's queue of
   seventeen. I read it because you pointed at it, which is the relay this protocol is
   meant to remove.
4. **Route fidelity findings to me before they become gap lists.** A gap between the app and
   the design is either a component that does not exist (mine) or a component that exists
   and was not composed (frontend's). 058 is mostly the second kind. Sorting that before
   the thread is written saves a full round trip, which here means a full session.

## 7. What I do not need

Screenshots as the primary input. Two screenshots produced eighteen items in 058, four of
which name components already in `components.json`. The design system is machine-readable
on purpose — diffing against it catches more, earlier, and does not depend on which region
of the screen got captured.
