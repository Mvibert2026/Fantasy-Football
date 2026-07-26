# Operating Model — roles, gates, and effort defaults

Who does what, what evidence counts as "done," and what model tier each role runs at.
Read this once at session start. `docs/CURRENT-STATE.md` tells you where the project is;
this file tells you how the work is run.

---

## Roles

| Role | Runs in | Default tier | Owns |
|---|---|---|---|
| **Backend** | Claude Code, this repo | Sonnet, effort 2 (→4 for a new formula with sanity checks) | `src/` statistical and modelling code, exports, tests, ADRs |
| **Data Ops** | Claude Code, this repo | Sonnet, effort 1–2 | Ingestion, snapshots, mock logging, scheduled pulls, board re-pulls |
| **Frontend** | Claude Code, separate working copy | Sonnet, effort 3 (→4–5 for any full spec port) | React app, client state, API wiring, `/design-sync` operation |
| **Design** | Claude Design (no repo access) | n/a | Tokens, components, screen specs |
| **Strategist** | Chat, **no database access** | Opus, effort 4 | Independent statistical red-team, validation protocols, pre-registration |
| **Researcher** | Chat, web enabled | Opus, effort 4–5 | Competitive, platform, and voice-of-customer research |
| **PM / Chief of Staff** | Cowork chat | Sonnet | Dispatch, verification gatekeeping, budget calibration, Fable briefings |
| **Fable** | Weekly, outside review | Heaviest tier | Framework-level questions: VONA, opponent model, proprietary ranking, data-source audit |

**Strategist's lack of database access is deliberate.** It exists to be a second, independent set
of eyes on Backend's statistics. Granting it DB access would collapse it into an extension of
Backend and destroy the reason it exists. Do not "fix" this.

**Concurrency:** roughly 3 active workstreams at a time. This is a deliberate complexity and cost
choice, and it is what makes a heavier per-workstream effort setting affordable.

---

## Evidence standards — what counts as "done"

| Work type | Sufficient evidence | Never accept |
|---|---|---|
| Statistical constant | Measurement + standard error + n + a non-trivial test | A number with no stated uncertainty |
| Pipeline / ingestion | Passing tests + row counts + quarantine report | "Ingested successfully" |
| Export / contract change | Version bump + frontend explicitly notified | A schema change with no version bump |
| **UI screen or component** | **A screenshot a human has looked at** | **A passing test suite** |
| Research claim | `[VERIFIED]` / `[SNIPPET]` / `[SECONDARY]` / `[GAP]` tag | A plausible number filling a `[GAP]` |

The UI row is the one that has actually failed. The Opponents and Predictions tabs were reported
complete, tests passed, and the screens did not exist. A test suite can be fully green while an
entire screen is missing, because nothing asserted the screen existed. **Report UI work as "built,
pending screenshot verification" — never as done.**

---

## Session protocol for Claude Code

**Read, in this order:**
1. `docs/CURRENT-STATE.md` — canonical state
2. this file — your role, tier, and gates
3. only the specific ADR or doc your task names

Do **not** read `docs/status.md` for current state. It is an append-only historical log carrying
superseded figures in the same voice as live ones.

**Write back, every session:**
- Update `docs/CURRENT-STATE.md` **in place** — replace stale lines, do not append
- Append the session narrative to `docs/status.md`
- New decision → an ADR in `docs/decisions.md`
- Contract schema change → bump the version **and** note that the frontend must be told

**Report** commit hash and test count. Not prose summaries.

---

## Effort discipline

Default to the lowest tier that has historically completed the task type correctly. One standing
exception, learned expensively: **never downgrade effort on a long, fidelity-critical spec port.**
The 38K-character port ran at escalated effort to a 97% usage stop and still self-reported
inaccurately. Under-effort there does not save tokens — it defers them into a more expensive
discovery later.

---

## Budget calibration log

Append a row whenever usage data is available.

| Date | Role | Tier | Task | Usage | Verified complete? |
|---|---|---|---|---|---|
| pre-2026-07-26 | Backend | Sonnet, low–moderate | 31 tests, ADRs, measured constant, 24-config matrix | Comfortable | Yes |
| pre-2026-07-26 | Frontend | Sonnet, effort→5 | Full 38K-char spec port | Hard stop ~97% | **No — false completion claim** |
| pre-2026-07-26 | Researcher | Opus, 4–5 | Competitive UX + platform + Reddit research | Within session | Yes |

---

## Open threads — do not resolve unilaterally

1. **AI assistant guardrail redesign.** Stripping conversational guardrails is a *different*
   decision from loosening the four architectural principles. Do not conflate them.
2. **Injury / real-time context pipeline.** Deliberately deferred over hallucination risk, with the
   reasoning stated in the code itself. Do not reverse mid-sprint.
3. **Proprietary ranking system.** Fable-scoped. Framework and validation methodology first,
   defended, then build. Not before.
4. **Design ⇄ code drift.** `/design-sync` covers the design system (tokens, components) and is run
   from Claude Code by Frontend. It does **not** cover screens. Screenshot comparison remains the
   only check that a screen exists at all.
