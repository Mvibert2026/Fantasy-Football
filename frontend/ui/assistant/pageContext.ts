import type { BoardRow } from '../data/board';
import type { LiveAvailabilityResult } from '../data/liveAvailability';
import { playerAvailabilityAtPick } from '../data/availability';
import type { Dataset } from '../data/load';
import type { VbdOverride } from '../data/recommendation';
import type { PositionScarcity } from '../data/scarcity';
import { paceLabel, tierDepletionLine, under50Line } from '../data/scarcity';
import { decimal, integer, percent } from '../lib/format';
import type { ContextItem } from './reasoning';

/**
 * FR-076 ("the chatbot should have access to that data to synthesize it
 * intelligently"): a bounded, always-current snapshot of what the Draft Room
 * screen is showing right now, built into `ContextItem`s the same shape
 * `retrieval.ts` produces from the static exports -- so the reasoning lane
 * treats "what's on screen" and "what's in board.json" as one kind of thing,
 * not two.
 *
 * PRINCIPLE: every field here is a value `DraftRoom.tsx` has ALREADY computed
 * for its own render -- `recommendationDetail`, `recommendationDetailLookAhead`,
 * `referencePoint`, `scarcityList`, `rosterChips`, `unfilledPositions`, the
 * pick-clock numbers. This module only formats those into prose; it does not
 * re-derive a recommendation, a VBD gap, or an availability probability from
 * raw rows. "Pass live app state, do not recompute it" (FR-076's own
 * instruction) means the exact object DraftRoom is about to render is the
 * object handed in here, including which of the two recommendation shapes
 * (on-the-clock vs. look-ahead) is currently active -- that choice lives in
 * DraftRoom's `lookAheadActive`, not reconstructed from scratch here.
 *
 * BOUNDED: this never grows with the size of the board. Roughly 6-9 short
 * items regardless of how many players remain, each one naming the exact
 * on-screen panel it mirrors as its `source_path` (Principle #1 -- a client-
 * session value must still trace to something a person can go look at, even
 * though it isn't a `board.json:` field path). The final item always states
 * what was deliberately left out, per the founder's own "say what you
 * excluded" instruction.
 */

export interface RosterChip {
  label: string;
  filled: number;
  total: number;
}

export interface RecommendationSnapshot {
  playerName: string;
  position: string;
  reason: string;
  pointsRange: { low: number; high: number } | null;
}

export interface GiveUpSnapshot {
  text: string;
}

export interface ReferencePointSnapshot {
  consideringName: string;
  consideringPosition: string;
  pick: number;
  likelyThere: { name: string; position: string } | null;
}

export interface DraftPageContextInput {
  currentPick: number;
  currentRound: number;
  userOnClock: boolean;
  nextUserPick: number | null;
  picksUntilYou: number | null;
  followingUserPick: number | null;
  draftComplete: boolean;
  unfilledPositions: string[];
  rosterChips: RosterChip[];
  /**
   * Whichever recommendation DraftRoom is actually showing right now --
   * on-the-clock (`recommendationDetail`) when the user is on the clock and
   * hasn't toggled look-ahead, or the look-ahead one otherwise. Null only
   * when neither has a top pick (e.g. nothing left with a projection).
   */
  activeRecommendation: RecommendationSnapshot | null;
  /** Which pick `activeRecommendation` is for, and whether it's a look-ahead
   *  ("today's board," not a forecast) or the pick happening right now. */
  recommendationContext: { pick: number | null; isLookAhead: boolean };
  /** Only meaningful for the on-the-clock recommendation -- null under look-ahead. */
  giveUp: GiveUpSnapshot | null;
  vbdOverride: VbdOverride | null;
  referencePoint: ReferencePointSnapshot | null;
  scarcity: PositionScarcity[];
  data: Dataset;
}

function nameOf(row: BoardRow): string {
  return row.name.kind === 'present' ? row.name.value : 'an unnamed player';
}

function pctOf(a: LiveAvailabilityResult | null): number | null {
  return a ? (a.live ?? (a.baseline.kind === 'present' ? a.baseline.value : null)) : null;
}

/** Re-exported so DraftRoom can hand this module a `pctOf`-shaped helper
 *  without duplicating the live-vs-baseline fallback rule anywhere else. */
export { pctOf as liveOrBaselinePct };

function draftStateItem(input: DraftPageContextInput): ContextItem {
  if (input.draftComplete) {
    return {
      id: 'page.draft_state',
      text: 'The draft is complete. There is no current pick and no further recommendation to show.',
      confidence: 'high',
      source_path: 'live draft session (this browser): pick clock',
    };
  }
  const clockText = input.userOnClock
    ? 'The user is on the clock right now.'
    : input.nextUserPick !== null && input.picksUntilYou !== null
      ? `The user is not on the clock. The user's next pick is overall pick ${integer(input.nextUserPick)}, ${integer(input.picksUntilYou)} pick${input.picksUntilYou === 1 ? '' : 's'} from now.`
      : "The user is not on the clock, and no further pick of the user's remains this draft.";
  return {
    id: 'page.draft_state',
    text: `The current overall pick is ${integer(input.currentPick)} (round ${integer(input.currentRound)}). ${clockText}`,
    confidence: 'high',
    source_path: 'live draft session (this browser): command bar pick clock',
  };
}

function rosterNeedsItem(input: DraftPageContextInput): ContextItem {
  const chips = input.rosterChips.map((c) => `${c.label} ${integer(c.filled)}/${integer(c.total)}`).join(', ');
  const unfilled = input.unfilledPositions.length ? input.unfilledPositions.join(', ') : 'none';
  return {
    id: 'page.roster_needs',
    text: `The user's roster slots filled so far: ${chips || 'none logged yet'}. Still-unfilled starting positions: ${unfilled}.`,
    confidence: 'high',
    source_path: 'live draft session (this browser): MY ROSTER slot chips',
  };
}

function recommendationItem(input: DraftPageContextInput): ContextItem | null {
  const rec = input.activeRecommendation;
  if (!rec) return null;
  const pick = input.recommendationContext.pick;
  const scope = input.recommendationContext.isLookAhead
    ? pick !== null
      ? `For the user's upcoming pick at overall ${integer(pick)}, evaluated against today's board (not a forecast of who will still be available then):`
      : 'Evaluated against today\'s board (not a forecast of who will still be available then):'
    : "For the pick happening right now:";
  const range = rec.pointsRange
    ? ` Honest points range ${decimal(rec.pointsRange.low)}–${decimal(rec.pointsRange.high)}.`
    : '';
  return {
    id: 'page.recommendation',
    text: `${scope} the app's top recommendation is ${rec.playerName} (${rec.position}). Stated reason: ${rec.reason}${range}`,
    confidence: 'high',
    source_path: 'live draft session (this browser): Draft Room > Recommend tab, top card',
  };
}

function giveUpItem(input: DraftPageContextInput): ContextItem | null {
  if (!input.giveUp) return null;
  return {
    id: 'page.recommendation_tradeoff',
    text: `The trade-off against the next-best option, as shown on screen: ${input.giveUp.text}`,
    confidence: 'high',
    source_path: 'live draft session (this browser): Draft Room > Recommend tab, WHAT YOU GIVE UP',
  };
}

function vbdOverrideItem(input: DraftPageContextInput): ContextItem | null {
  const o = input.vbdOverride;
  if (!o) return null;
  const displacedName = nameOf(o.displaced);
  const terms = o.firing
    .map(({ term, appliesTo }) =>
      appliesTo === 'top'
        ? `+${integer(term.points)} for the recommended pick because ${term.reason} (an unbacktested stopgap constant, not a finding)`
        : `${integer(term.points)} against ${displacedName} because ${term.reason} (an unbacktested stopgap constant, not a finding)`,
    )
    .join('; ');
  return {
    id: 'page.recommendation_override',
    text: `The recommendation does not follow the highest-VBD available player. ${displacedName} (${o.displaced.raw.position}) has ${integer(Math.round(o.vbdGap))} more VBD points but was not recommended. Why: ${terms}.`,
    confidence: 'high',
    source_path: 'live draft session (this browser): Draft Room > Recommend tab, WHY NOT HIGHEST VBD',
  };
}

function referencePointItem(input: DraftPageContextInput): ContextItem | null {
  const rp = input.referencePoint;
  if (!rp) return null;
  const likely = rp.likelyThere
    ? (() => {
        const range = survivalRangeText(input.data, rp);
        return `The player with the best odds of still being there is ${rp.likelyThere!.name} (${rp.likelyThere!.position})${range}.`;
      })()
    : `No available player has even odds (50%+) of still being there at pick ${integer(rp.pick)}.`;
  return {
    id: 'page.next_pick_reference',
    text: `Reference point for the user's next pick, overall ${integer(rp.pick)}: the player currently under consideration is ${rp.consideringName} (${rp.consideringPosition}). ${likely} Display only, this is not what the recommendation above is computed from.`,
    confidence: 'high',
    source_path: 'live draft session (this browser): Draft Room > Recommend tab, next-pick reference point',
  };
}

/** Mirrors `ReferenceSurvivalRange` in DraftRoom.tsx exactly (same
 *  `playerAvailabilityAtPick` call, same sigma5/10/20 min-max) so the text
 *  handed to the model never disagrees with what the card itself shows. */
function survivalRangeText(data: Dataset, rp: ReferencePointSnapshot): string {
  if (!rp.likelyThere) return '';
  const cell = playerAvailabilityAtPick(data, rp.likelyThere.name, rp.pick);
  const vals = [cell.sigma5, cell.sigma10, cell.sigma20].filter((c) => c.kind === 'present') as Array<{
    kind: 'present';
    value: number;
  }>;
  if (vals.length === 0) return ', survival range not computed';
  const lo = Math.min(...vals.map((v) => v.value));
  const hi = Math.max(...vals.map((v) => v.value));
  return `, ${percent(lo)}–${percent(hi)} likely to survive to that pick (range across sigma 5/10/20)`;
}

function scarcityItem(input: DraftPageContextInput): ContextItem | null {
  if (input.scarcity.length === 0) return null;
  const lines = input.scarcity.map((s) => {
    if (!s.dataAvailable) return `${s.pos}: no board data for this position`;
    const tier = tierDepletionLine(s) ?? 'tier data not computed';
    const pace = paceLabel(s.pace, s.paceSuppressedReason);
    const under50 = under50Line(s, input.nextUserPick);
    return `${s.pos} (${integer(s.remaining)} of ${integer(s.total)} left, ${pace}, ${tier}${under50 ? `, ${under50}` : ''})`;
  });
  return {
    id: 'page.scarcity',
    text: `Position scarcity right now: ${lines.join('; ')}.`,
    confidence: 'high',
    source_path: 'live draft session (this browser): Draft Room > Scarcity tab',
  };
}

function scopeNoteItem(): ContextItem {
  return {
    id: 'page.scope_note',
    text:
      'This page summary is scoped to the current pick and the user\'s immediate roster and scarcity picture. ' +
      'It does not include the full available-player board, the queue/watchlist, or every remaining player\'s ' +
      'individual availability. Ask a player-specific or board-wide question separately for that detail.',
    confidence: 'high',
    source_path: 'assistant page-context: scope note',
  };
}

/**
 * Builds the bounded page-context bundle from values `DraftRoom.tsx` has
 * already computed. Returns `[]` (not a placeholder item) when there is
 * nothing meaningfully on screen yet -- callers should treat an empty array
 * the same as "no page context," never fabricate a state.
 */
export function buildDraftPageContextItems(input: DraftPageContextInput): ContextItem[] {
  const items = [
    draftStateItem(input),
    rosterNeedsItem(input),
    recommendationItem(input),
    giveUpItem(input),
    vbdOverrideItem(input),
    referencePointItem(input),
    scarcityItem(input),
  ].filter((i): i is ContextItem => i !== null);
  if (items.length === 0) return [];
  items.push(scopeNoteItem());
  return items;
}
