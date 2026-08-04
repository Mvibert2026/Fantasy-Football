# Batch C5 — registration (tier-2, ADR-070): the rest of the base pool

**Registered by `ranker`, 2026-08-04, before any C5 arm is graded.** Pool authority:
`docs/ranking/standalone-screen-2.md`. Code: `experiments/bottomup/v2/factors_c5_ct1.py`.
Binding: ADR-070 in full; ADR-069.

With C1–C4, AB1 and this batch, **every base factor in the 35-factor pool is a registered arm**:
C5 covers the newly-unblocked pair and the four screen "incumbents" that are built by the feature
builder but consumed by no running spec — for those the correct arm is **additive** (they are
candidate additions), and batch-AB1's not-in-model table documents why they have no ablation.

| arm | factor | positions | family | columns |
|---|---|---|---|---|
| C5P | PROE (`pbp.xpass` residual, lag-1 team) | QB RB WR TE | T2P | `proe_1`, `proe_known` |
| C5O | OC continuity (play_callers Wikipedia proxy, lag-1) | QB RB WR TE | T2P | `oc_disruption_1`, `oc_known` |
| C5D | draft capital, veteran-additive | QB RB WR TE | T2A | `log_draft_pick_v`, `undrafted_v` |
| C5A | aDOT (lag-weighted `adot_num/adot_den`) | RB WR TE | T2P | `adot_w`, `adot_known` |
| C5R | roster/depth status trio (lag-1) | QB RB WR TE | T2P | `ros_absent_v`, `offroster_v`, `depth_first_v`, `ros_absent_known` |
| C5I | injury designations pair (lag-1) | QB RB WR TE | T2P | `injm_v`, `injum_v`, `injm_known` |
| F0C5 | **placebo** (salt `C5-placebo`) | QB RB WR TE | T2A | `placebo_noise_c5` |

k-controls: C5Pk/C5Ok/C5Ak/C5Rk/C5Ik (not in m_b, lazy for WIN candidates). **`m_b = 27`**
(23 treatment + 4 placebo). One arm one change; every read gated (proe/oc loaders are
holdout-bounded SQL + an access-log entry; the rest are base-frame columns).

**Registered predictions** (screen 2's exploratory read, priced at half weight): C5P and C5O NULL
everywhere (screen: raw ρ inside the placebo band); C5R the strongest candidate (screen: the most
season-consistent signal in the pool, raw-negative 28/28 season-position cells); C5I directionally
with C5R but weaker; C5D partial-negative pattern means the additive arm is likelier HARM/RE-SPECIFY
than WIN at positions where `ppg_w` already carries the level.

Standing constraints: holdout sealed; targets ≤ 2024; no proxy reads; placebo carried; seeds sha256.
