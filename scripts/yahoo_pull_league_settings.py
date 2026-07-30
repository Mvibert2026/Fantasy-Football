"""
Fetch-on-demand Yahoo league settings/draft-results report -- FR-062.

WHY THIS SCRIPT DOES NOT WRITE TO data/nfl.db OR data/leagues/*.json BY
DEFAULT. Yahoo's developer terms reportedly require deleting Yahoo user data
not explicitly listed as storable indefinitely within 24 hours
(docs/research/yahoo-espn-league-connection-2026-07-30.md SS6, [SNIPPET],
never independently re-verified against legal.yahoo.com). Until that is
resolved, this script prints its report and exits -- fetch, display,
discard. `--out` writes a report file only if you pass it explicitly; that
is a derived, human-authored analysis artifact (like any other doc in this
repo), not a raw Yahoo payload cache, but it is still your call to make, not
this script's default.

USAGE
    python scripts/yahoo_connect.py                      # one-time, first
    python scripts/yahoo_pull_league_settings.py --discover
    python scripts/yahoo_pull_league_settings.py --league-key 461.l.154693
    python scripts/yahoo_pull_league_settings.py --league-key 461.l.154693 --draft-results
    python scripts/yahoo_pull_league_settings.py --league-key 461.l.154693 --live-draft

`--live-draft` reads the same endpoint as `--draft-results` but is labeled
as a possibly-in-progress read; see DraftResult.caveat and
src/providers/mapping.py's module docstring. It does not place picks --
nothing in this connector can.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from providers.base import ProviderUnavailable  # noqa: E402
from providers.mapping import diff_against_claude_md_westwood  # noqa: E402
from providers.yahoo import YahooProvider  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--league-key", help="e.g. 461.l.154693 (game_key.l.league_id)")
    parser.add_argument("--discover", action="store_true", help="list your Yahoo leagues")
    parser.add_argument("--draft-results", action="store_true", help="fetch completed draft results")
    parser.add_argument("--live-draft", action="store_true", help="fetch draft results, caveated as possibly in-progress")
    parser.add_argument("--out", help="optional path to also write the report to (opt-in; see module docstring)")
    args = parser.parse_args()

    try:
        provider = YahooProvider.from_env()
    except ProviderUnavailable as exc:
        print(f"Yahoo unavailable: {exc}")
        return 1

    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    if args.discover:
        raw = provider.discover_leagues()
        emit("=== Discovered leagues (raw) ===")
        emit(json.dumps(raw, indent=2))
        emit("Look for 'league_key' values above (format game_key.l.league_id).")

    if args.league_key:
        settings = provider.get_league_settings(args.league_key)
        emit(f"=== Settings: {args.league_key} ===")
        emit(f"name: {settings.name}")
        emit(f"max_teams: {settings.max_teams}")
        emit(f"scoring_type: {settings.scoring_type}")
        emit(f"num_playoff_teams: {settings.num_playoff_teams}")
        emit(f"playoff_start_week: {settings.playoff_start_week}")
        emit(f"uses_playoff_reseeding: {settings.uses_playoff_reseeding}")
        emit(f"roster_positions ({len(settings.roster_positions)}):")
        for rp in settings.roster_positions:
            emit(f"  {rp.position}: {rp.count} (bench={rp.is_bench})")
        emit(f"stat_modifiers ({len(settings.stat_modifiers)}):")
        for sm in settings.stat_modifiers:
            bonus_str = ", ".join(f"{b.points}pt@{b.target}" for b in sm.bonuses)
            emit(f"  stat_id={sm.stat_id} {sm.name}: {sm.value}" + (f" bonuses[{bonus_str}]" if bonus_str else ""))
        if settings.parse_warnings:
            emit("PARSE WARNINGS (mapping.py's extraction did not find or coerce these -- inspect raw JSON):")
            for w in settings.parse_warnings:
                emit(f"  - {w}")
        diffs = diff_against_claude_md_westwood(settings)
        emit("=== Diff vs CLAUDE.md SS7 (Westwood) ===")
        if diffs:
            for d in diffs:
                emit(f"  MISMATCH: {d}")
        else:
            emit("  no mismatches on checked fields (or nothing to compare -- see warnings above)")

        if args.draft_results or args.live_draft:
            if args.live_draft:
                result = provider.get_live_draft_picks(args.league_key)
            else:
                result = provider.get_draft_results(args.league_key)
            emit(f"=== Draft results ({'live estimate' if result.is_live_estimate else 'final'}) ===")
            if result.caveat:
                emit(f"CAVEAT: {result.caveat}")
            emit(f"{len(result.picks)} picks")
            for p in result.picks[:10]:
                emit(f"  pick {p.pick} (rd {p.round}): {p.team_key} <- {p.player_key}")
            if len(result.picks) > 10:
                emit(f"  ... and {len(result.picks) - 10} more")

    if not args.discover and not args.league_key:
        parser.print_help()
        return 1

    if args.out:
        Path(args.out).write_text("\n".join(lines) + "\n")
        print(f"\nAlso wrote report to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
