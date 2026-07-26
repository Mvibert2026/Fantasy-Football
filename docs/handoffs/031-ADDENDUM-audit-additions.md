
---

## Addendum — 2026-07-26, requested by Design

Two additions to the audit, both cheap if done during the pass and expensive to reconstruct later.

### 1. Retrofit status — picked up or deferred?

`docs/design-system/AUDIT.md` specifies five retrofits, RETROFIT-1 through RETROFIT-5. For each,
record whether the shipped app already reflects it, partially reflects it, or does not. RETROFIT-5
(the TypeAhead back-port to the Draft board — key map, autofocus, order randomisation, `entry_mode`)
is the one most likely to be partially present, since a type-ahead already exists there in a worse
form.

The point is to know which retrofits can be closed for free versus which are real work.

### 2. Null vocabulary — did it survive contact?

This is the higher-value of the two and the reason Design asked for it.

The product distinguishes five null-ish renderings, and they are **different claims**:

| Rendering | Means |
|---|---|
| `—` | no value exists for this field |
| `<1%` | a real, computed, very small probability |
| `0%` | a real, computed zero |
| `not yet` | will exist, has not been computed |
| `·` | structurally not applicable here |

Audit whether all five remain distinct in the running app, or whether any have collapsed into one
another.

**Why this specifically.** Design's framing is exact and worth preserving: *drift here is silent and
compounds, because each individual substitution looks reasonable in isolation.* Nobody ever decides to
degrade the null vocabulary. Someone renders `—` where `not yet` belonged because it looked tidier,
and six months later the distinction no longer exists anywhere and no commit is responsible for
removing it.

This is also the single place where drift attacks the product's actual thesis rather than its polish.
Principle #2 exists because `0%` and "not computed" are different claims; a build where they render
identically has quietly abandoned the differentiator while every test still passes.

Report per screen: which of the five appear, and any place two are rendered the same way.
