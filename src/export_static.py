"""
Emit the hand-authored contract artifacts: glossary.json, nulls.json, opponents.json.

These are prose, not computation, so they live in source rather than being
derived. Every definition is written for a smart non-statistician.

OPPONENTS: MOSTLY NOT SUPPLIED. Only two of the nine opponents have any known
information, and even for those the only behavioural fact on record is "took a
TE in round 3 in 2025" -- with no pick number attached. Draft slots ARE derivable
from the pick numbers that were supplied, and are computed rather than guessed.
Everything else is emitted as null with `data_status` saying so. The contract
asks for cited 2025 pick numbers; those citations do not exist in this repo and
are not invented here.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import draft_sim as ds
from export_contract import CONTRACT_VERSION, EXPORT_DIR

# Derived from the supplied pick numbers, not assumed: in a 10-team snake,
# pick 19 -> round 2 slot 2, pick 20 -> round 2 slot 1, pick 21 -> round 3
# slot 1, pick 22 -> round 3 slot 2.
KNOWN_OPPONENTS = {
    "Shit Leopards": {
        "draft_slot_2026": 2,
        "known_picks_2026": [2, 19, 22, 39, 42],
        "behaviour_on_record": "Took a TE in round 3 in 2025 (pick number not supplied).",
    },
    "Cucked Commish": {
        "draft_slot_2026": 1,
        "known_picks_2026": [1, 20, 21, 40, 41],
        "behaviour_on_record": "Took a TE in round 3 in 2025 (pick number not supplied).",
    },
}

GLOSSARY = {
    "VBD": {
        "short_definition": "How many more points a player is expected to score than a "
                            "freely-available replacement at the same position.",
        "long_explanation": (
            "Value Based Drafting. Raw projected points are misleading across positions: a "
            "quarterback scoring 300 is not automatically better than a running back scoring "
            "220, because every team starts a quarterback and good ones are easy to find. VBD "
            "fixes this by subtracting the 'replacement level' — what you could get for free "
            "off waivers at that position. What is left is the part that actually wins you "
            "matchups. It is the number this board sorts by."
        ),
    },
    "replacement level": {
        "short_definition": "The last player at a position who is realistically startable in "
                            "this league.",
        "long_explanation": (
            "With 10 teams each starting 1 quarterback, roughly the 10th-best quarterback is "
            "the worst one anyone is forced to use — so QB10 is 'replacement level'. Our "
            "levels are RB30, WR40, TE10, QB10, measured against 26 seasons of who actually "
            "wins the flex slots in a league shaped like ours. Public rankings almost always "
            "assume a 12-team league with RB24 and "
            "WR36, which is simply a different league from ours. This is one of the few places "
            "we can be confidently more correct than a public board."
        ),
    },
    "consensus rank": {
        "short_definition": "Where a large group of fantasy analysts collectively ranks a "
                            "player.",
        "long_explanation": (
            "FantasyPros Expert Consensus Rank: many analysts submit rankings and these are "
            "averaged. It is expert opinion, NOT a record of where players actually get "
            "drafted (that would be ADP, which we could not obtain legally). It is a strong "
            "starting point and genuinely hard to beat, but it assumes a generic league, not "
            "ours."
        ),
    },
    "confidence interval": {
        "short_definition": "A range the true value probably sits in — wide means we are "
                            "guessing.",
        "long_explanation": (
            "Every number measured from data is uncertain. A 95% confidence interval is the "
            "range we would expect the real answer to fall in most of the time. The important "
            "habit: if an interval includes zero, we have NOT shown any effect exists. Many of "
            "ours are wide, because we only have a few seasons of comparable data, and we "
            "report that rather than hiding it."
        ),
    },
    "tier": {
        "short_definition": "A group of players close enough in value that which one you get "
                            "barely matters.",
        "long_explanation": (
            "Rankings imply precision that does not exist — the gap between WR4 and WR5 is "
            "usually noise. Tiers group players who are effectively interchangeable. The "
            "useful question during a draft is not 'is this the best player left' but 'is this "
            "the last player left in his tier', because that is when waiting actually costs "
            "you something."
        ),
    },
    "structural adjustment": {
        "short_definition": "Rank movement caused by our league's rules and size, not by any "
                            "opinion about the player.",
        "long_explanation": (
            "Our league is 10 teams, starts 3 wide receivers and 2 flex, has no kicker, and "
            "uses yardage bonuses. Those facts alone move players up and down relative to a "
            "generic public board — quarterbacks in particular fall sharply, because only 10 "
            "start each week so a replacement quarterback is unusually good. This is the "
            "part of our board we are most confident about: it is arithmetic about the rules, "
            "not a prediction about football."
        ),
    },
    "evaluative adjustment": {
        "short_definition": "Rank movement caused by disagreeing with the experts about a "
                            "player. Currently zero.",
        "long_explanation": (
            "This would be the part where our model says 'the experts are wrong about this "
            "specific player'. Our board contains none of it, and the field is deliberately "
            "empty rather than filled with a made-up number. Every player at the same "
            "positional rank gets the same projection, because no source of player-by-player "
            "component projections (passing yards, carries, targets) is available to us. All "
            "of our disagreement with consensus is structural."
        ),
    },
    "availability probability": {
        "short_definition": "The chance a player is still undrafted when your pick arrives.",
        "long_explanation": (
            "Computed by simulating thousands of drafts where the other nine teams follow "
            "consensus with some randomness. If a player shows 60% at pick 23, he was still "
            "on the board in 60 of every 100 simulated drafts. These are the most reliable "
            "numbers we produce, because they depend only on how people draft — not on "
            "predicting how many points anyone will score, which we do poorly."
        ),
    },
    "sigma": {
        "short_definition": "How far the other teams stray from consensus, measured in draft "
                            "picks.",
        "long_explanation": (
            "Sigma 5 is a disciplined room where everyone drafts close to the rankings. Sigma "
            "10, our default, means about a round of slippage in either direction. Sigma 20 "
            "is chaos — big reaches and big slides. We do not know which describes your "
            "league, because we have no record of past draft results, so every availability "
            "number is shown at all three. If a number barely changes across them, trust it. "
            "If it swings, the answer depends on your league's temperament."
        ),
    },
    "sign test": {
        "short_definition": "A simple check of whether a result points the same way every "
                            "season.",
        "long_explanation": (
            "With very few seasons, fancy statistics are misleading. The sign test just counts: "
            "did this strategy beat the baseline in 4 seasons out of 4, or 2 out of 4? Its "
            "virtue is honesty about limits — with 4 seasons, even a perfect 4-for-4 only "
            "reaches p=0.125, which is above the usual 0.05 bar. So we can see direction but "
            "cannot prove significance, and we say so instead of pretending otherwise."
        ),
    },
    "power floor": {
        "short_definition": "The best p-value our data could possibly produce. Ours is above "
                            "the usual threshold.",
        "long_explanation": (
            "A hard ceiling on what any test can show, set by how much data exists. With 4 "
            "seasons the floor is 0.125; the conventional significance bar is 0.05. So no "
            "strategy comparison in this project can be 'statistically significant', however "
            "large the real effect. This is why we report direction and size honestly rather "
            "than chasing significance we cannot reach."
        ),
    },
    "holdout": {
        "short_definition": "A season deliberately locked away so we cannot fool ourselves.",
        "long_explanation": (
            "2025 is sealed off. If you build and tweak a model against the same data you "
            "judge it on, you will always look brilliant and always be wrong. So 2025 is "
            "untouchable during development, and the code physically refuses to read it "
            "outside one logged, explicit path. It is the difference between testing an idea "
            "and confirming a hope."
        ),
    },
    "projected points": {
        "short_definition": "Our estimate of a player's season total under this league's exact "
                            "scoring — and it is a weak estimate.",
        "long_explanation": (
            "Built from what players at that consensus rank have historically scored under our "
            "rules. Be sceptical: consensus rank explains only about 16-27% of what actually "
            "happens, so these are rough guides, not forecasts. Availability probabilities on "
            "this board are far more trustworthy than projections."
        ),
    },
}

NULLS = [
    {
        "id": "PR-002",
        "claim_tested": "Spike-week ability is a persistent player trait (test-registry #38)",
        "method": (
            "For every player-season 1999-2024, measured how often a player cleared the 100 / "
            "150 / 200 yard bonus thresholds, subtracted how often his yardage alone implies "
            "he should have, and correlated that leftover across consecutive seasons. 36 "
            "correlations, confidence intervals bootstrapped by resampling players."
        ),
        "result": (
            "NULL. Receiving-100 for WR r=+0.041 (95% CI -0.018 to +0.099); rushing-100 for RB "
            "r=+0.063 (CI -0.001 to +0.124). Zero of 24 testable correlations survived "
            "multiple-comparisons correction."
        ),
        "plain_language_summary": (
            "This was supposed to be our biggest edge. The league's stacking yardage bonuses "
            "reward players who post occasional huge games, so we assumed some players are "
            "reliably 'boom' types and that public rankings miss it. They are not. Once you "
            "account for the fact that high-yardage players clear thresholds more often simply "
            "by being high-yardage, there is nothing left that carries from one year to the "
            "next. Practically: project the yards and the bonuses take care of themselves. "
            "There is no spike-week player to hunt for. This is the largest sample we have — "
            "26 seasons — so it is not a case of not looking hard enough."
        ),
    },
    {
        "id": "PR-003-hero-rb",
        "claim_tested": "Hero RB drafting beats taking the best player available (#44)",
        "method": (
            "43,200 simulated drafts across 4 seasons and 3 opponent-behaviour settings, "
            "scoring the resulting rosters against what players actually did."
        ),
        "result": (
            "NULL. Margin -13.3 points versus best-available (CI -98.1 to +65.0), better in "
            "only 2 of 4 seasons, at every opponent setting."
        ),
        "plain_language_summary": (
            "Taking a stud running back early and then loading up on receivers does not "
            "produce better rosters than simply taking the best player on the board. The "
            "season-by-season results swing from +93 to -133 points, which is the signature of "
            "noise rather than a real effect. Any single season would have told a confident "
            "and wrong story."
        ),
    },
    {
        "id": "PR-003-elite-te",
        "claim_tested": "Taking an elite tight end early is worth the pick (#45)",
        "method": "Same simulation, elite-TE-early arm versus best-available.",
        "result": (
            "Consistently NEGATIVE: -96.1 points at the default setting (seed-noise band "
            "+/-6; re-running across five fixed master seeds spans -100.7 to -85.2), worse "
            "in 4 of 4 seasons at all three opponent settings (12 of 12 cells). The sign "
            "never changes at any seed."
        ),
        "plain_language_summary": (
            "Reaching for a top tight end in the first three rounds cost roughly 3-5% of total "
            "roster points, every season we tested, under every assumption about how the room "
            "drafts. It cannot be called statistically significant — 4 seasons cannot prove "
            "anything — but nothing about it wavered. A separate measurement put the cost at "
            "-226 points. Two different methods, same direction."
        ),
    },
    {
        "id": "PR-003-qb-early",
        "claim_tested": "Securing an elite quarterback early is worth the pick",
        "method": "Same simulation, QB-early arm versus best-available.",
        "result": "Worst arm tested: -115.4 points, negative in 12 of 12 cells.",
        "plain_language_summary": (
            "Reaching for a quarterback in the first three rounds was the single most costly "
            "thing we tested. The reason is that quarterbacks bunch together — the gap between "
            "the best and the tenth-best is small — so waiting gets you nearly the same player, "
            "while the early pick you spent is gone for good. Notably this contradicts an "
            "earlier conclusion of our own, which reasoned from positional value alone and "
            "implied QB-early was the lesser evil. Measured directly, it is the greater one."
        ),
    },
    {
        "id": "ADR-025",
        "claim_tested": "Our re-scored board beats raw consensus",
        "method": (
            "Compared roster value produced by our board against unmodified consensus across "
            "2022-2025, per season."
        ),
        "result": (
            "Directionally positive but NOT statistically established: +176.0, -34.7, +113.4 "
            "in development seasons and +83.8 in the holdout. Mean +84.6, positive in 3 of 4 "
            "seasons, sign-test p=0.625 against a power floor of 0.125."
        ),
        "plain_language_summary": (
            "Our board looks better than plain consensus in three of four seasons, by around "
            "85 points on average. That is encouraging and it is NOT proof — with four seasons "
            "we could not prove it even if it were true. Worth recording honestly: an earlier "
            "version of our own notes claimed this result 'flipped sign' and failed. That was a "
            "bookkeeping error on our side, since corrected. The board has never actually "
            "looked worse than consensus on average; it has simply never been provable."
        ),
    },
]


def build_opponents() -> dict:
    profiles = []
    for name, info in KNOWN_OPPONENTS.items():
        profiles.append({
            "team_name": name,
            "draft_slot_2026": info["draft_slot_2026"],
            "draft_slot_2025": None,
            "known_picks_2026": info["known_picks_2026"],
            "positional_tendencies": None,
            "first_pick_by_position": None,
            "consensus_tracking_behaviour": None,
            "notes": info["behaviour_on_record"],
            "cited_2025_picks": [],
            "holds_picks_19_to_22": True,
            "data_status": (
                "PARTIAL. Draft slot is derived from supplied 2026 pick numbers. The only "
                "behavioural fact on record is a round-3 TE selection in 2025, supplied without "
                "a pick number, so no pick citation is possible."
            ),
        })
    for slot in range(1, ds.N_TEAMS + 1):
        if slot in (ds.USER_SLOT, 1, 2):
            continue
        profiles.append({
            "team_name": None,
            "draft_slot_2026": slot,
            "draft_slot_2025": None,
            "known_picks_2026": [i + 1 for i, t in enumerate(ds.pick_order())
                                 if t == slot - 1][:6],
            "positional_tendencies": None,
            "first_pick_by_position": None,
            "consensus_tracking_behaviour": None,
            "notes": None,
            "cited_2025_picks": [],
            "holds_picks_19_to_22": False,
            "data_status": (
                "NOT SUPPLIED. No team name, no 2025 draft record, no behavioural history "
                "exists in this repository for this slot. Nothing is inferred."
            ),
        })
    return {
        "contract_version": CONTRACT_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "user_draft_slot": ds.USER_SLOT,
        "coverage_warning": (
            "7 of 9 opponents have NO data. The simulator therefore models all opponents "
            "identically -- drafting to consensus with noise -- rather than with individual "
            "tendencies. To populate these profiles the 2025 draft board (pick number, team, "
            "player) must be supplied; it is not derivable from anything currently ingested."
        ),
        "opponents": profiles,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=EXPORT_DIR)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    payloads = {
        "glossary.json": {"contract_version": CONTRACT_VERSION, "generated_utc": stamp,
                          "terms": GLOSSARY},
        "nulls.json": {"contract_version": CONTRACT_VERSION, "generated_utc": stamp,
                       "preamble": (
                           "Findings we tested and did NOT confirm. Published draft guides "
                           "rarely show these, which is precisely why they are here: a claim "
                           "that has survived a real test is worth more than one that was "
                           "never tested."
                       ),
                       "findings": NULLS},
        "opponents.json": build_opponents(),
    }
    for name, payload in payloads.items():
        p = args.out / name
        # allow_nan=False -- see export_contract.write_all. Bare Infinity/NaN is
        # valid Python and invalid JSON; fail here, not in the browser.
        p.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
        print(f"wrote {p}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
