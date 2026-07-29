import { absent, present, type Cell } from './cell';
import { pickNumbersForSlot } from './draft';
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
  /** The value every computation in the app reads: the FR-034 override when one is set
   *  for this league, else the same as `userSlotSourced`. Never render this through
   *  `<Value>` when `userSlotOverridden` is true -- it does not trace to a backend field
   *  in that case, and Principle #1/#2 require that to stay visible, not folded into the
   *  same rendering path as a real export value. See `applyUserSlotOverride` below. */
  userSlot: Cell<number>;
  /** league.json:user_draft_slot, always -- untouched by any override. What "clear
   *  override" falls back to, and what a screen shows as "sourced: N" alongside the
   *  effective slot when the two differ. */
  userSlotSourced: Cell<number>;
  /** True exactly when `userSlot` is a local FR-034 override rather than
   *  `userSlotSourced`'s own value. */
  userSlotOverridden: boolean;
  pickSequence: Cell<number[]>;
  /** league.json:platform (thread 058 section C3) -- e.g. "sleeper". Absent on
   *  an export that predates the field, never fabricated. */
  platform: Cell<string>;
  /** league.json:draft_type (thread 058 section C3) -- e.g. "snake". */
  draftType: Cell<string>;
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
        `adjusted to compensate. Regenerate the export to resolve it.`;

  const sourcedUserSlot = present(L.user_draft_slot, 'league.json:user_draft_slot', runId);

  return {
    teams: present(L.teams, 'league.json:teams', runId),
    rounds: present(L.rounds, 'league.json:rounds', runId),
    userSlot: sourcedUserSlot,
    userSlotSourced: sourcedUserSlot,
    userSlotOverridden: false,
    pickSequence: present(L.pick_sequence, 'league.json:pick_sequence', runId),
    platform:
      L.platform === undefined
        ? absent('league.json:platform', runId, 'This export predates league.json:platform.')
        : present(L.platform, 'league.json:platform', runId),
    draftType:
      L.draft_type === undefined
        ? absent('league.json:draft_type', runId, 'This export predates league.json:draft_type.')
        : present(L.draft_type, 'league.json:draft_type', runId),
    thresholds,
    replacementLevelsNote: L.replacement_levels_note,
    flexSplitNote: L.flex_split_note,
    playoffTeams: present(L.playoff.teams, 'league.json:playoff.teams', runId),
    playoffReseeding: L.playoff.reseeding,
    thresholdDrift,
  };
}

/**
 * FR-034: applies a local draft-slot override on top of an already-built LeagueConfig.
 * The single seam every downstream consumer goes through -- DraftRoom, PlayerDetail,
 * Predictions, RoundGrid all read `league.userSlot`/`league.pickSequence` directly and
 * none of them need to change, because they get the overridden values for free.
 *
 * `pickSequence` MUST be recomputed here, not left as `league.json:pick_sequence` --
 * that field is the real backend value for the *sourced* slot only. Leaving it alone
 * under an override would be exactly the "changes a label but not the math" failure
 * the request explicitly warns about: DraftRoom's "MY PICKS" panel and RoundGrid's
 * "mine" highlighting both read `pickSequence` straight, so a stale sequence there
 * would silently point at someone else's picks. The recomputation uses the identical
 * snake-order formula (`pickNumbersForSlot`, ui/data/draft.ts) the backend itself
 * would apply for that slot -- same arithmetic, just evaluated for a slot the backend
 * export was not built for -- so the values are exactly what league.json would say if
 * it had been regenerated for this slot, not a client-side approximation.
 *
 * A no-op (returns `config` unchanged) when `override` is `null` or `teams` isn't a
 * present Cell -- there is no valid slot range without a real team count, so an
 * override can never be applied against a guessed range (FR-034's explicit rule).
 */
export function applyUserSlotOverride(config: LeagueConfig, override: number | null): LeagueConfig {
  if (override === null) return config;
  if (config.teams.kind !== 'present') return config;
  const teams = config.teams.value;
  if (!Number.isInteger(override) || override < 1 || override > teams) return config;
  if (config.userSlotSourced.kind === 'present' && config.userSlotSourced.value === override) {
    // Overriding to the same value as the sourced one isn't really an override --
    // keep userSlotOverridden false so the UI doesn't claim a divergence that isn't real.
    return config;
  }

  const runId = config.userSlot.kind === 'present' ? config.userSlot.runId : config.userSlotSourced.runId;
  const rounds = config.rounds.kind === 'present' ? config.rounds.value : 0;

  return {
    ...config,
    userSlot: present(override, 'local draft-slot override (FR-034, not from league.json)', runId),
    userSlotOverridden: true,
    pickSequence:
      rounds > 0
        ? present(
            pickNumbersForSlot(teams, override, rounds),
            'derived: snake-order arithmetic for the overridden slot (FR-034; league.json:pick_sequence is for the sourced slot only)',
            runId,
          )
        : config.pickSequence,
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
