import type { Position, RawPlayerDescription, RawPlayerDescriptions } from './types';

/**
 * Join + display helpers for `player_descriptions.json`'s `archetype` field (ADR-044,
 * FR-075, `docs/ranking/archetypes-proposal.md`).
 *
 * PlayerDetail.tsx used to render "Not computed: archetype. No backend field in this
 * build" unconditionally -- a wrong-not-absent claim, worse than a missing capability,
 * since it told the founder the field doesn't exist when it is loaded into
 * `Dataset.playerDescriptions` on every session (`ui/data/load.ts`) and already read by
 * the assistant (`ui/assistant/retrieval.ts`). This module makes the real join exist so
 * the card can show what the export actually says instead of a blanket denial.
 *
 * `docs/ranking/archetypes-proposal.md` SS1 measured the existing taxonomy as
 * degenerate in practice -- one catch-all bucket per position (RB_COMMITTEE 62.7% of
 * RBs, TE_SECONDARY_RECEIVER 51.0% of TEs, WR_ROTATIONAL 41.4% of WRs) and roughly a
 * third of eligible players meeting no criterion at all. Those are one-time, dated
 * figures from a researcher's snapshot of the committed artifact -- rendering them as
 * fixed UI text would violate Principle #1 the moment the export regenerates.
 * `archetypeShareOfPosition` below recomputes the same shape of number LIVE from
 * whatever `player_descriptions.json` the browser actually has loaded, so the
 * low-discrimination problem stays visible and never goes stale.
 */

/** Positions the archetype system covers today (`src/archetypes.py`, ADR-044). QB has
 *  no taxonomy at all yet -- `docs/ranking/archetypes-proposal.md` SS3.6 proposes one,
 *  unbuilt -- and DEF/K are out of scope permanently (no per-player DST/K data model
 *  exists at all, matching ADR-039's reasoning for the board itself). This is a
 *  coverage gap, a different claim from "we measured him and found no fit"
 *  (UNCLASSIFIED) -- the two must never share a message. */
export const ARCHETYPE_POSITIONS: readonly Position[] = ['RB', 'WR', 'TE'];

export function archetypeCovers(position: Position): boolean {
  return (ARCHETYPE_POSITIONS as readonly string[]).includes(position);
}

/** `undefined` covers two different real states the caller must distinguish itself:
 *  `pd === null` (this league has no player_descriptions.json at all -- primary only
 *  today) is not the same claim as `pd` present but this player has no row in it
 *  (UNCLASSIFIED, or the join simply has no gsis id to try). */
export function archetypeFor(
  pd: RawPlayerDescriptions | null,
  gsisId: string | null,
): RawPlayerDescription | undefined {
  if (!pd || !gsisId) return undefined;
  return pd.players.find((p) => p.player_id === gsisId);
}

/** `WR_ROTATIONAL` -> `Rotational` for a WR row -- the position prefix is dropped
 *  because the position already renders right next to this chip (identity strip),
 *  so repeating it is noise, not information. Falls back to the raw label, title-cased
 *  by underscore, if the archetype string doesn't carry this player's own position as
 *  a prefix (shouldn't happen given `src/archetypes.py`'s naming convention, but this
 *  must not throw on an unexpected export shape). */
export function archetypeLabel(archetype: string, position: string): string {
  const prefix = `${position}_`;
  const body = archetype.startsWith(prefix) ? archetype.slice(prefix.length) : archetype;
  return body
    .split('_')
    .filter(Boolean)
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

export interface ArchetypeShare {
  /** Classified players at this position sharing this exact archetype string. */
  n: number;
  /** Classified players at this position, total -- NOT every eligible player at the
   *  position (players who met no criterion are absent from the file entirely, so
   *  this denominator cannot speak to them; see the module doc comment). */
  ofClassified: number;
}

/** Computed live over whatever `player_descriptions.json` is actually loaded --
 *  never a cached research number. See module doc comment. */
export function archetypeShareOfPosition(
  pd: RawPlayerDescriptions,
  position: string,
  archetype: string,
): ArchetypeShare {
  const samePosition = pd.players.filter((p) => p.position === position);
  const sameLabel = samePosition.filter((p) => p.archetype === archetype);
  return { n: sameLabel.length, ofClassified: samePosition.length };
}
