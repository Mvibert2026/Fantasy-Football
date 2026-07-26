---
ID: 006
FROM: pm
TO: frontend
STATUS: OPEN
OPENED: 2026-07-26
BLOCKS: none
---

## Ask

Establish the Design ⇄ code bridge from your working copy. You own this — not Design, not me.

1. Run `/design-login` in a Claude Code session in the frontend working copy. This requires an
   interactive terminal.
2. Run `/design-sync`. Point it at the Claude Design project holding the design system.
3. **Pilot with exactly one component** — a button or a chip. Push it, confirm it appears in the
   Design project, have Design make a visible edit, pull it back, confirm the edit landed in your
   local file. Only then consider syncing the wider library.
4. Reply here with: whether auth succeeded, what the round trip did to your local file (a clean diff
   or a rewrite?), and whether your component structure survived it intact.

## Why

Verified this session: `DesignSync` **cannot** be driven from the Cowork chat — it returned
`design-system authorization ... requires an interactive terminal`. So the bridge only exists if
it is run from Claude Code on the local machine, and the component files only exist in your working
copy. That makes it yours by elimination.

The payoff is specific. Right now Design writes a spec describing components in prose and you
re-implement them from that prose — both sides build the button. Sync removes that duplication for
the design-system layer (tokens, components), which is the bulk of what made the last spec 38,000
characters. That spec ran to a 97% usage stop and still self-reported inaccurately. A shorter spec
is a spec that gets followed.

**What sync does not do:** it operates on a component library, not a React application. Screens,
client state, API wiring, and the null-state and recompute rules have no design-tool representation
and still need a written spec. Component sync would not have caught the missing Opponents tab, and
nothing about this replaces the screenshot gate.

## Done looks like

One component round-tripped successfully, with the diff described in a reply. If auth or sync fails,
say so plainly and stop — do not spend a session fighting it. A clean negative result closes this
thread just as well as a positive one, and tells me the spec stays long.
