import { absent, present, type Cell } from './cell';
import type { Dataset } from './load';
import { runIdOf } from './load';

/**
 * League configuration, including the startable thresholds.
 *
 * The thresholds are read from `league.json:replacement_levels` and are never
 * hardcoded. That has already paid for itself: they moved from RB28/WR41/TE11 to
 * RB30/WR40/TE10 at contract 1.3.0, and the app picked the new values up on the next
 * sync with no front-end change. Anything hardcoded then would be wrong now.
 *
 * `thresholdDrift` reports a version mismatch rather than compensating for one. The
 * app always renders what the export says.
 */

import { EXPECTED_CONTRACT } from './contract';

export { EXPECTED_CONTRACT };

export interface Threshold {
  position: string;
  /**
   * Absent when the position is startable in this league but carries no replacement
   * level in config. That is DEF's situation: the roster starts one, but no DST data
   * is ingested, so no level exists and no player on the board can be measured against it.
   */
  level: Cell<number>;
  /** Number of this position in the starting lineup, from roster.starters. */
  starters: Cell<number>;
}

export interface LeagueConfig {
  teams: Cell<number>;
  rounds: Cell<number>;
  userSlot: Cell<number>;
  pickSequence: Cell<number[]>;
  thresholds: Threshold[];
  replacementLevelsNote: string;
  flexSplitNote: string;
  playoffTeams: Cell<number>;
  playoffReseeding: boolean;
  /** Non-null while league.json predates the expected threshold contract version. */
  thresholdDrift: string | null;
}

/**
 * Why a startable position has no replacement level. Each case is a different fact
 * about the data, and collapsing them into one message would lose that.
 *
 * ---------------------------------------------------------------------------
 * DO NOT COMPUTE A DEF REPLACEMENT LEVEL HERE. (ADR-039)
 *
 * DEF10 is genuinely derivable from league structure alone -- 10 teams x 1 DEF
 * starter, the identical arithmetic that yields QB10 -- so its absence looks like an
 * oversight. It is not. The backend implemented it that way first and reverted it
 * deliberately.
 *
 * The reason: publishing a DEF *rank* invites a downstream VBD, and the *points* half
 * of that calculation does not exist. No DST data is ingested, so there is no DEF
 * points projection for a replacement level to be measured against. A rank with no
 * points behind it is a number that looks computed and is not.
 *
 * The exclusion is permanent, not pending. Read ADR-039 before changing anything here.
 * ---------------------------------------------------------------------------
 */
function reasonForMissingLevel(
  pos: string,
  excludedPositions: readonly string[],
  exclusionNote: string | undefined,
  defNote: string,
): string {
  if (pos === 'FLEX') {
    // FLEX is a lineup slot filled from other positions, not a position of its own, so
    // it has no replacement level by definition rather than by omission.
    return (
      'FLEX is a lineup slot filled from RB, WR and TE rather than a position in its own ' +
      'right, so it has no replacement level of its own. How flex slots get filled ' +
      'league-wide is measured separately.'
    );
  }
  // The export names its own deliberate exclusions as of contract 1.5.0, so this reads
  // the decision rather than restating it. Falls back to the board's def_note on an
  // older export that predates the field.
  if (excludedPositions.includes(pos)) {
    return exclusionNote ?? defNote;
  }
  return `No replacement level is published for ${pos} in league.json:replacement_levels.`;
}

export function buildLeagueConfig(data: Dataset): LeagueConfig {
  const runId = runIdOf(data.manifest, 'league');
  const L = data.league;
  const levels = L.replacement_levels;
  const starters = L.roster.starters;

  // Every position the league actually starts, in roster order -- so a position with
  // no replacement level (DEF) still appears, rather than vanishing from the list.
  const positions = Object.keys(starters);

  // Positions the contract says are excluded on purpose, as opposed to merely missing.
  const excluded = L.positions_without_replacement_levels ?? [];

  const thresholds: Threshold[] = positions.map((pos) => {
    const level = levels[pos];
    return {
      position: pos,
      level:
        level === undefined
          ? absent(
              `league.json:replacement_levels.${pos}`,
              runId,
              reasonForMissingLevel(
                pos,
                excluded,
                L.positions_without_replacement_levels_note,
                data.board.def_note,
              ),
            )
          : present(level, `league.json:replacement_levels.${pos}`, runId),
      starters: present(starters[pos] as number, `league.json:roster.starters.${pos}`, runId),
    };
  });

  const version = L.contract_version;
  const thresholdDrift =
    version === EXPECTED_CONTRACT
      ? null
      : `league.json declares contract ${version}; this app is written against ${EXPECTED_CONTRACT}. ` +
        `The thresholds shown are whatever league.json currently publishes — nothing here is ` +
        `adjusted to compensate. Use Refresh data to re-check, or regenerate the export.`;

  return {
    teams: present(L.teams, 'league.json:teams', runId),
    rounds: present(L.rounds, 'league.json:rounds', runId),
    userSlot: present(L.user_draft_slot, 'league.json:user_draft_slot', runId),
    pickSequence: present(L.pick_sequence, 'league.json:pick_sequence', runId),
    thresholds,
    replacementLevelsNote: L.replacement_levels_note,
    flexSplitNote: L.flex_split_note,
    playoffTeams: present(L.playoff.teams, 'league.json:playoff.teams', runId),
    playoffReseeding: L.playoff.reseeding,
    thresholdDrift,
  };
}

/**
 * True when a player's positional rank is at or above the startable threshold for
 * their position -- i.e. they project as a starter in a league this size. Undefined
 * when no threshold exists for the position, which is not the same as false.
 */
export function isStartable(
  config: LeagueConfig,
  position: string,
  positionalRank: number,
): boolean | undefined {
  const t = config.thresholds.find((x) => x.position === position);
  if (!t || t.level.kind !== 'present') return undefined;
  return positionalRank <= t.level.value;
}
