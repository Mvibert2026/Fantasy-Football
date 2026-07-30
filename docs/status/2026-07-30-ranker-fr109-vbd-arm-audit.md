# 2026-07-30 — ranker — FR-109 audit of the FR-085 VBD arm

Pointer file. The substance lives in `docs/ranking/fr085-zero-rb.md` §5.5 (new), §5.4 (replaced),
§1(6) (withdrawn) and in the response section of
`docs/founder-requests/FR-109-the-vbd-arm-in-the-zero-rb-sim-may-be-wrong-and-.md`. Do not read this
file for numbers.

**What was asked.** The founder challenged the claim that plain VBD takes its first RB in round 6.3
— *"there's not 60 better players than the first rb"* — and FR-109 argued this contradicted the
ledger's RB1 168.5 slot value, implying a broken baseline that every arm compared against would
inherit.

**What was found.** The arm is not mis-specified: at pick 1 the highest-VBD player on the board is
RB1 and the arm takes him. The two results do not contradict; both estimators rank RB1 first. What
was wrong was my reporting — 6.33 is the mean of a bimodal distribution (45% round 1, 44% rounds
11–12, zero drafts in round 3) and the most extreme cell of its own 14-cell σ grid. One real code
bug found and fixed: §5.4's slot table was printed from the σ=20 cell under a "primary σ" heading.

**What changed in the code.** Three new read-only audit modules in `experiments/strategy/`
(`audit_vbd.py`, `why_first_rb.py`, `slot_sweep.py`) and one bug fix in `run_strategies.py`. The
simulator itself is unmodified; §5.2's margins were not recomputed and did not need to be.

**What is now open and not mine to close.** Replacement level flips the round-2 RB-vs-WR call
depending on which of two defensible baselines is used, and it has never been tested — needs a
`strategist` pre-registration. The need-penalty amendment carries ~46% of the first-RB behaviour and
still needs the ruling I asked for. Both are recorded in `docs/ideas-inbox.md` and in the FR-109
response.
