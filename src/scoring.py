"""
Scoring engine for 10-team, 0.5 PPR with stacking yardage bonuses.
Replacement level is tunable and must stay explicit.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# League scoring configuration — exact league settings
LEAGUE = {
    "offense": {
        "passing_yards": {"per": 25, "bonuses": [(300, 1.0), (350, 1.5), (400, 2.0)]},
        "passing_td": 4,
        "interception": -2,
        "rushing_yards": {"per": 10, "bonuses": [(100, 1.0), (150, 1.5), (200, 2.0)]},
        "rushing_td": 6,
        "receptions": 0.5,
        "receiving_yards": {"per": 10, "bonuses": [(100, 1.0), (150, 1.5), (200, 2.0)]},
        "receiving_td": 6,
        "return_td": 6,
        "two_point_conversion": 2,
        "fumbles_lost": -2,
        "offensive_fumble_return_td": 6,
    },
    "defense": {
        "sacks": 1,
        "interceptions": 2,
        "fumble_recoveries": 2,
        "touchdowns": 6,
        "safeties": 2,
        "blocked_kicks": 1,
        "return_tds": 6,
        "extra_point_returned": 2,
        "points_allowed": [
            (0, 10),
            (7, 7),
            (14, 4),
            (21, 1),
            (28, 0),
            (35, -1),
            (float("inf"), -4),
        ],
    },
}


def score_offensive_game(stats: Dict, cfg=None) -> float:
    """
    Score an offensive player-game from raw stats.
    stats: dict with keys like 'passing_yards', 'rushing_tds', etc.
    Returns fantasy points.
    """
    cfg = cfg or LEAGUE
    off = cfg["offense"]
    score = 0.0

    # Passing
    py = stats.get("passing_yards", 0) or 0
    score += (py / off["passing_yards"]["per"]) * 1.0
    for threshold, bonus in off["passing_yards"]["bonuses"]:
        if py >= threshold:
            score += bonus
    score += stats.get("passing_tds", 0) * off["passing_td"]
    score += stats.get("interceptions", 0) * off["interception"]

    # Rushing
    ry = stats.get("rushing_yards", 0) or 0
    score += (ry / off["rushing_yards"]["per"]) * 1.0
    for threshold, bonus in off["rushing_yards"]["bonuses"]:
        if ry >= threshold:
            score += bonus
    score += stats.get("rushing_tds", 0) * off["rushing_td"]

    # Receiving
    rec = stats.get("receptions", 0) or 0
    score += rec * off["receptions"]
    rcy = stats.get("receiving_yards", 0) or 0
    score += (rcy / off["receiving_yards"]["per"]) * 1.0
    for threshold, bonus in off["receiving_yards"]["bonuses"]:
        if rcy >= threshold:
            score += bonus
    score += stats.get("receiving_tds", 0) * off["receiving_td"]

    # Other
    score += stats.get("return_tds", 0) * off["return_td"]
    score += stats.get("two_point_conversions", 0) * off["two_point_conversion"]
    score += stats.get("fumbles_lost", 0) * off["fumbles_lost"]
    score += (
        stats.get("offensive_fumble_return_tds", 0) * off["offensive_fumble_return_td"]
    )

    # No floor: Yahoo permits negative player scores (e.g. a fumble lost with no
    # offsetting production, or a QB with interceptions and minimal yardage).
    # Clamping at zero silently inflates poor performances and biases season
    # totals upward, which in turn understates the cost of a bust.
    return score


def score_defense_game(stats: Dict, cfg=None) -> float:
    """Score a defense for a game. Requires points_allowed."""
    d = (cfg or LEAGUE)["defense"]
    g = lambda k: stats.get(k, 0) or 0

    pts = 0.0
    for key in (
        "sacks",
        "interceptions",
        "fumble_recoveries",
        "touchdowns",
        "safeties",
        "blocked_kicks",
        "return_tds",
        "extra_point_returned",
    ):
        pts += g(key) * d[key]

    pa = g("points_allowed")
    for ceiling, bonus in d["points_allowed"]:
        if pa <= ceiling:
            pts += bonus
            break

    return pts


@dataclass
class ReplacementLevels:
    """
    Replacement level depends on how flex slots get filled league-wide.
    This is NOT knowable a priori; hence flex_split is an explicit assumption.
    """

    teams: int = 10
    starters: Dict[str, int] = field(
        default_factory=lambda: {"QB": 1, "RB": 2, "WR": 3, "TE": 1}
    )
    flex_slots: int = 2
    # MEASURED, not assumed (2026-07-25). Previously {RB 0.40, WR 0.55, TE 0.05},
    # which was a judgement call. Measured over 26 seasons of actual outcomes
    # scored under THIS league's rules: rank all flex-eligible players, remove
    # the mandated starters (RB20/WR30/TE10), and count who wins the 20 flex
    # slots. Mean RB 10.4 / WR 9.5 / TE 0.1 -> shares 0.52 / 0.48 / 0.00,
    # giving RB30 / WR40 / TE10.
    #
    # TWO CAVEATS THAT MATTER:
    #  - Season-to-season variance is large: RB flex ranges 5 to 17, sd 3.0. The
    #    mean is stable; any single season is not.
    #  - The answer moves +/-1 rank by window (1999-2011 -> RB31/WR39;
    #    2012-2019 -> RB29/WR41; post-2019 -> RB31/WR39). RB30/WR40 is the
    #    midpoint, not a precise estimate.
    # RB28 vs RB30 is INSIDE that noise. Adopted for consistency with the
    # measurement, NOT as a claimed improvement.
    #
    # TE is the one robust result: 0 flex slots in every window tested. A tight
    # end won a flex slot in 2 of 26 seasons, one slot each.
    flex_split: Dict[str, float] = field(
        default_factory=lambda: {"RB": 0.52, "WR": 0.48, "TE": 0.00}
    )

    def baselines(self) -> Dict[str, int]:
        """Positional rank that counts as 'freely available'."""
        out = {}
        total_flex = self.teams * self.flex_slots
        for pos, n in self.starters.items():
            base = self.teams * n
            base += round(total_flex * self.flex_split.get(pos, 0.0))
            out[pos] = int(base)
        return out

    # ----------------------------------------------------------- multi-league
    SCOREABLE_POSITIONS = ("QB", "RB", "WR", "TE")

    @classmethod
    def from_league_config(cls, cfg) -> Tuple["ReplacementLevels", bool]:
        """Build a ReplacementLevels from a league_config.LeagueConfig.

        Returns (levels, flex_split_is_measured). `cfg.starters` may include
        positions this scoring engine cannot compute (K, DEF -- no kicker or
        DST scoring exists, ADR-039); those are filtered out here rather than
        producing a replacement level with nothing behind it, the same
        principle ADR-039 already established for DEF specifically.

        `cfg.flex_split` is a MEASURED quantity for the primary league
        (ADR-029, 26 seasons under its exact rules). A new league's true split
        has not been measured. If `cfg.flex_split` is None, the primary
        league's measured split is used as an EXPLICITLY FLAGGED placeholder
        (the second return value is False) -- never silently, so a caller can
        surface the caveat rather than presenting a borrowed number as this
        league's own measurement.
        """
        starters = {
            p: n for p, n in cfg.starters.items() if p in cls.SCOREABLE_POSITIONS
        }
        flex_eligible = tuple(p for p in cfg.flex_eligible if p in cls.SCOREABLE_POSITIONS)
        if cfg.flex_split is not None:
            flex_split = dict(cfg.flex_split)
            measured = True
        else:
            # Placeholder: the primary league's measured split, restricted to
            # this league's actual flex-eligible positions.
            fallback = {"RB": 0.52, "WR": 0.48, "TE": 0.00}
            flex_split = {p: fallback.get(p, 0.0) for p in flex_eligible}
            measured = False
        return (
            cls(teams=cfg.teams, starters=starters, flex_slots=cfg.flex_slots,
                flex_split=flex_split),
            measured,
        )


def compute_vbd(
    season_points: Dict[str, List[Tuple[str, float]]], levels: ReplacementLevels = None
) -> Dict[str, float]:
    """
    season_points: {position: [(player, points), ...]}
    Returns {player: value_over_replacement}
    """
    levels = levels or ReplacementLevels()
    baselines = levels.baselines()
    vbd = {}
    for pos, players in season_points.items():
        ranked = sorted(players, key=lambda x: -x[1])
        idx = min(baselines.get(pos, len(ranked)) - 1, len(ranked) - 1)
        replacement = ranked[idx][1] if ranked else 0.0
        for name, pts in ranked:
            vbd[name] = pts - replacement
    return vbd


def _test():
    """Self-tests for scoring engine."""
    cases = []

    # QB: 320 pass yds, 2 pass TD, 1 INT, 30 rush yds, 1 rush TD
    # 320/25=12.8, +1.0 (300 bonus), 2*4=8, 1*-2=-2, 30/10=3.0, 1*6=6
    cases.append(
        (
            "QB line",
            {
                "passing_yards": 320,
                "passing_tds": 2,
                "interceptions": 1,
                "rushing_yards": 30,
                "rushing_tds": 1,
            },
            28.8,
        )
    )

    # RB: 105 rush yds, 1 rush TD, 4 rec, 35 rec yds
    # 10.5 +1.0 (100 bonus) +6 +2.0 (4 rec) +3.5
    cases.append(
        (
            "RB line",
            {
                "rushing_yards": 105,
                "rushing_tds": 1,
                "receptions": 4,
                "receiving_yards": 35,
            },
            23.0,
        )
    )

    # WR monster: 200 rec yds, 2 TD, 10 rec — all three bonuses stack
    # 20 + (1.0+1.5+2.0) + 12 + 5.0
    cases.append(
        (
            "WR 200-yd game (stacked bonuses)",
            {
                "receiving_yards": 200,
                "receiving_tds": 2,
                "receptions": 10,
            },
            41.5,
        )
    )

    # Elite passing game: 410 yds, 3 TD, 0 INT — all pass bonuses stack
    # 16.4 + (1.0+1.5+2.0) + 12
    cases.append(
        (
            "QB 410-yd game",
            {
                "passing_yards": 410,
                "passing_tds": 3,
            },
            32.9,
        )
    )

    # Nets to exactly zero: 40 rush yds (+4.0), 2 fumbles lost (-4.0).
    # NOTE: this case lands on 0.0 by arithmetic, so it does NOT exercise the
    # absence of a floor -- it passed identically when max(0.0, score) existed.
    # The genuinely-negative case below is the one that tests the clamp removal.
    cases.append(
        (
            "Nets to zero (40 rush yds, 2 fumbles lost)",
            {
                "rushing_yards": 40,
                "fumbles_lost": 2,
            },
            0.0,
        )
    )

    # Genuinely negative: no production, 1 fumble lost. Yahoo permits negative
    # player scores; a floor here would silently report this as 0.0.
    cases.append(
        (
            "Genuinely negative (0 rush yds, 1 fumble lost)",
            {
                "rushing_yards": 0,
                "fumbles_lost": 1,
            },
            -2.0,
        )
    )

    # Negative QB line: 2 INTs, 30 pass yds (1.2) -> 1.2 - 4.0 = -2.8
    cases.append(
        (
            "Negative QB line (30 pass yds, 2 INT)",
            {
                "passing_yards": 30,
                "interceptions": 2,
            },
            -2.8,
        )
    )

    passed = True
    for label, stats, expected in cases:
        got = score_offensive_game(stats)
        ok = abs(got - expected) < 1e-9
        passed &= ok
        print(
            f"  [{'PASS' if ok else 'FAIL'}] {label}: got {got:.2f}, expected {expected:.2f}"
        )

    # Defense: shutout with 4 sacks, 2 INT, 1 TD
    # 4*1 + 2*2 + 6 + 10 (0 pts allowed)
    d_got = score_defense_game(
        {"sacks": 4, "interceptions": 2, "touchdowns": 1, "points_allowed": 0}
    )
    d_ok = abs(d_got - 24.0) < 1e-9
    passed &= d_ok
    print(f"  [{'PASS' if d_ok else 'FAIL'}] DEF shutout: got {d_got:.2f}, expected 24.00")

    # Defense blowup: 38 allowed, 1 sack
    d2 = score_defense_game({"sacks": 1, "points_allowed": 38})
    d2_ok = abs(d2 - (-3.0)) < 1e-9
    passed &= d2_ok
    print(
        f"  [{'PASS' if d2_ok else 'FAIL'}] DEF blowup: got {d2:.2f}, expected -3.00"
    )

    print("\n  Replacement levels (10 teams, 3WR/2RB/TE, 2 flex):")
    for pos, base in ReplacementLevels().baselines().items():
        print(f"    {pos}: {pos}{base}")

    print(f"\n  {'ALL TESTS PASSED' if passed else 'FAILURES PRESENT'}")
    return passed


if __name__ == "__main__":
    print("Scoring engine self-test\n")
    _test()
