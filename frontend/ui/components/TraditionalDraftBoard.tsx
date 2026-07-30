import { useEffect, useMemo, useState } from 'react';
import type { BoardRow } from '../data/board';
import {
  currentOverallPick,
  overallPickForRoundSlot,
  pickWithinRound,
  teamSlotAtPick,
  type DraftPickRecord,
  type DraftState,
} from '../data/draft';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { loadOpponentNames } from '../data/opponentNames';
import { buildRosterSlots, type RosterSlot } from '../data/rosterSlots';

/**
 * FR-135 -- the traditional draft board: "it's a grid (empty at first) that
 * fills with picks as they are made, across the top is teams and then you
 * have two views, one is the order of the picks, snaking, and one is ordered
 * by position." Built to `docs/design/research/draft-board/FINDINGS.md` §4,
 * a verified reference study across Sleeper, LiveDraftX and FanDraft --
 * every load-bearing decision below cites the FINDINGS section it follows.
 *
 * This is a different artifact from `PeriodicTableGrid.tsx` (kept, not
 * deleted -- FINDINGS §2.7 vindicates it as LiveDraftX's own fourth "NFL
 * Teams" view). That grid organises the whole player universe by NFL
 * franchise, fully populated from first render. This board organises PICKS
 * by manager and round, empty until they happen -- "a record of what has
 * happened, not a catalogue of what exists" (FR-135's own framing).
 *
 * The two views, per FINDINGS §4.5 and the founder's own divergence between
 * what he asked for and what he named as its purpose:
 *   - Pick order (snaking): manager columns, round rows -- the literal ask,
 *     and the one place positional runs are actually visible ("the RB room
 *     emptied in the third round"), via a per-round positional tally in the
 *     gutter (§4.5's cheap addition) since colour alone doesn't scan as
 *     count. Default view, per §4.1.
 *   - By roster slot: same manager columns, rows become roster slots
 *     (QB/RB/RB/WR.../FLEX/BN/IR) -- the category's actual "position view"
 *     (§4.5, §2.6). Answers "what has each team built," not the RB-room
 *     question -- it discards the round axis, and does not claim to answer it.
 *
 * Cell content ladder (§4.3), width-tiered rather than viewport-breakpointed
 * in the CSS sense (this app has no @media anywhere -- see `useViewportWidth`
 * below): surname + position colour always: NEVER hidden at any tier, since
 * "the surname is the last thing to go" is the one thing FINDINGS states
 * flatly this project already violated once (RANKINGS-PANE.md, 1180w).
 * First initial + pick number add at the `wide` tier; NFL team + bye at
 * `wider`. No projection, VBD or delta in any cell (§4.3, unanimous).
 *
 * Current pick marked three ways (§4.4): the on-clock column header, the
 * specific cell, and a persistent bar above the grid.
 *
 * Never-fabricate (CLAUDE.md Principle #2, and FR-135's own "never
 * fabricate" instruction): an unmade pick's cell shows its own `round.pick`
 * address, nothing else -- never a projected/likely player. A pick entered
 * without a board match (`playerId === null` -- free text, or the auto-fill
 * placeholder) renders the typed text, never a position colour it cannot
 * honestly carry.
 */

const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
  DEF: 'var(--def)',
};

/** Matches `DraftRoom.tsx`'s own `AUTO_FILL_PLACEHOLDER` string exactly (not
 *  imported -- that constant is private to DraftRoom.tsx; duplicated here the
 *  same way `POSITION_COLOR` is duplicated across every view in this app). A
 *  pick carrying this exact text is a synthetic "auto-filled to reach my
 *  pick" placeholder, never a real name -- worth its own label rather than
 *  rendering as an ordinary unmatched typed pick. */
const AUTO_FILL_PLACEHOLDER = '(auto-filled — unknown pick)';

export type BoardView = 'pick-order' | 'roster-slot';

/** Below this window width, the two-axis grid is abandoned outright rather
 *  than squeezed (FINDINGS §4.6, LiveDraftX's own verified rule -- "no
 *  product was found doing" a frozen-column/scroll compromise). Chosen well
 *  below 1180 -- one of this dispatch's two required screenshot widths is
 *  1180px, and it must still show the real grid, not the mobile fallback. */
const MOBILE_BREAKPOINT = 880;

/** Column-width tiers for the cell-content ladder (§4.3), keyed to window
 *  width since this board is mounted as its own full-width hub tab (no
 *  competing side rail) -- window width is therefore a reasonably honest
 *  proxy for the grid's own rendered width, labelled as such rather than
 *  measured pixel-for-pixel. At 1180px (this dispatch's required narrow
 *  screenshot) this resolves to `compact`: surname + position colour only,
 *  matching FINDINGS' own arithmetic ("~107px per column... something must
 *  be designed out deliberately"). */
type CellTier = 'compact' | 'wide' | 'wider';
function tierFor(width: number): CellTier {
  if (width >= 1650) return 'wider';
  if (width >= 1300) return 'wide';
  return 'compact';
}

/** Window width, updated on resize. Not a per-column pixel measurement --
 *  see the module doc above -- but it is the one live signal this app's
 *  existing width-sensitive work (`RANKINGS-PANE.md`'s own "at 1180w")
 *  already reasons in terms of. SSR-safe default only matters for the
 *  initial render before the effect attaches; this app has no server
 *  render path today, so 1280 (comfortably `wide`) is a reasonable fallback
 *  rather than a load-bearing guess. */
export function useViewportWidth(): number {
  const [width, setWidth] = useState(() => (typeof window !== 'undefined' ? window.innerWidth : 1280));
  useEffect(() => {
    function onResize() {
      setWidth(window.innerWidth);
    }
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);
  return width;
}

/** Last whitespace-separated token of a full name. Not aware of suffixes
 *  ("Jr.", "III") or multi-word surnames with a lowercase participle -- the
 *  same simplification every verified reference board's own "surname,
 *  largest text" convention implies (FINDINGS §2.4); good enough for display,
 *  never used as a lookup key. */
export function surnameOf(name: string): string {
  const parts = name.trim().split(/\s+/);
  return parts[parts.length - 1] ?? name;
}

function firstInitialOf(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0];
  return first ? `${first[0]}.` : '';
}

interface TeamLabel {
  name: string;
  isUser: boolean;
  isSourced: boolean;
}

function teamLabelFor(
  slot: number,
  teamNameBySlot: Map<number, string | null>,
  typedNames: Record<number, string>,
  userSlot: number,
): TeamLabel {
  const sourced = teamNameBySlot.get(slot) ?? null;
  const typed = typedNames[slot];
  const name = typed ?? sourced ?? `Team ${slot}`;
  return { name, isUser: slot === userSlot, isSourced: typed !== undefined || sourced !== null };
}

/** Per-round positional tally for the pick-order gutter (§4.5's "cheap
 *  addition" that answers the founder's stated purpose -- "the RB room
 *  emptied in round 3" -- on the view that still has the round axis).
 *  Counts only picks resolved to a real board row; a free-text/off-board
 *  pick (`playerId === null`) cannot be honestly attributed a position, so
 *  it is silently excluded from the count rather than guessed -- this is a
 *  tally of what is known, not an estimate. */
function positionTally(picks: DraftPickRecord[], rowsById: Map<number, BoardRow>): Array<[string, number]> {
  const counts = new Map<string, number>();
  for (const p of picks) {
    if (p.playerId === null) continue;
    const row = rowsById.get(p.playerId);
    if (!row) continue;
    const pos = row.raw.position;
    counts.set(pos, (counts.get(pos) ?? 0) + 1);
  }
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
}

/** One filled or empty cell's content, shared by the pick-order grid, the
 *  roster-slot grid, and both mobile lists -- one rendering path, so the
 *  cell-content ladder rule can never drift between views. */
function CellContent({
  row,
  offBoardName,
  tier,
  addressLabel,
  isCurrent,
}: {
  /** The resolved board row, when the pick matched one. */
  row: BoardRow | null;
  /** The raw typed name, only meaningful when `row` is null and a pick
   *  genuinely exists (free text / auto-fill placeholder). */
  offBoardName: string | null;
  tier: CellTier;
  /** `round.pick` address -- shown for an unmade cell, and (at `wide`+) next
   *  to a made pick too, per FINDINGS §2.4 ("pick number, top-right"). */
  addressLabel: string;
  isCurrent: boolean;
}) {
  if (row === null && offBoardName === null) {
    // Unmade pick: FINDINGS §4.2 -- never blank, always at least its own
    // address, filled or not.
    return (
      <span
        className="num"
        style={{ fontSize: 10, color: isCurrent ? 'var(--acc)' : 'var(--dim2)', fontWeight: isCurrent ? 600 : 400 }}
      >
        {addressLabel}
      </span>
    );
  }
  if (row === null) {
    // A pick was entered but never matched a board player -- typed text or
    // the auto-fill placeholder. Never fabricate a position colour for it.
    const isPlaceholder = offBoardName === AUTO_FILL_PLACEHOLDER;
    return (
      <span
        title={isPlaceholder ? 'Auto-filled placeholder pick -- no real player logged.' : 'Typed pick, not matched to a board player.'}
        style={{
          fontSize: 11,
          fontStyle: 'italic',
          color: 'var(--dim2)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          display: 'block',
        }}
      >
        {isPlaceholder ? '(auto-filled)' : surnameOf(offBoardName ?? '')}
      </span>
    );
  }
  const position = row.raw.position;
  const color = POSITION_COLOR[position] ?? 'var(--dim2)';
  const name = row.name.kind === 'present' ? row.name.value : offBoardName ?? '(unnamed)';
  const bye = row.byeWeek.kind === 'present' ? row.byeWeek.value : null;
  return (
    <div
      title={`${name} -- ${row.raw.position} ${row.raw.team}`}
      style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0, borderLeft: `2px solid ${color}`, paddingLeft: 4 }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 4, minWidth: 0 }}>
        <span
          style={{
            fontSize: 11.5,
            fontWeight: 600,
            color: 'var(--txt)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            minWidth: 0,
          }}
        >
          {surnameOf(name)}
        </span>
        <span style={{ fontSize: 9, fontWeight: 600, color, flex: 'none' }}>{position}</span>
      </div>
      {tier !== 'compact' ? (
        <div className="num" style={{ fontSize: 9, color: 'var(--dim2)', display: 'flex', gap: 5 }}>
          <span>{firstInitialOf(name)}</span>
          <span>{addressLabel}</span>
        </div>
      ) : null}
      {tier === 'wider' ? (
        <div className="num" style={{ fontSize: 9, color: 'var(--dim2)' }}>
          {row.raw.team}
          {bye !== null ? ` · BYE ${bye}` : ''}
        </div>
      ) : null}
    </div>
  );
}

function OnClockBar({
  draftComplete,
  teams,
  currentPick,
  currentRound,
  posInRound,
  teamLabel,
}: {
  draftComplete: boolean;
  teams: number;
  currentPick: number;
  currentRound: number;
  posInRound: number;
  teamLabel: TeamLabel | null;
}) {
  if (teams === 0) return null;
  return (
    <div
      data-testid="tdb-onclock-bar"
      style={{
        flex: 'none',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '7px 12px',
        border: `1px solid ${draftComplete ? 'var(--line)' : 'var(--acc)'}`,
        background: 'var(--panel2)',
        fontSize: 12,
      }}
    >
      {draftComplete ? (
        <strong style={{ color: 'var(--dim2)' }}>Draft complete.</strong>
      ) : (
        <>
          <span style={{ fontSize: 10, letterSpacing: '.08em', color: 'var(--acc)', border: '1px solid var(--acc)', padding: '1px 6px', flex: 'none' }}>
            ON THE CLOCK
          </span>
          <strong style={{ color: 'var(--txt)' }}>{teamLabel?.name ?? '—'}</strong>
          {teamLabel?.isUser ? <span style={{ color: 'var(--acc)' }}>(you)</span> : null}
          <span className="num" style={{ color: 'var(--dim2)' }}>
            Round {currentRound}, pick {posInRound} of {teams} — overall #{currentPick}
          </span>
        </>
      )}
    </div>
  );
}

function ViewToggle({ view, setView }: { view: BoardView; setView: (v: BoardView) => void }) {
  const options: Array<{ key: BoardView; label: string; testid: string }> = [
    { key: 'pick-order', label: 'Pick order (snaking)', testid: 'tdb-view-toggle-pick-order' },
    { key: 'roster-slot', label: 'By roster slot', testid: 'tdb-view-toggle-roster-slot' },
  ];
  return (
    <div style={{ flex: 'none', display: 'flex', gap: 2 }}>
      {options.map((o) => (
        <button
          key={o.key}
          data-testid={o.testid}
          aria-pressed={view === o.key}
          onClick={() => setView(o.key)}
          style={{
            padding: '5px 10px',
            fontSize: 11.5,
            fontWeight: view === o.key ? 600 : 400,
            color: view === o.key ? 'var(--txt)' : 'var(--dim2)',
            background: view === o.key ? 'var(--panel2)' : 'transparent',
            border: `1px solid ${view === o.key ? 'var(--line2)' : 'var(--line)'}`,
          }}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

/** Desktop pick-order grid: manager columns, round rows, one CSS grid (not
 *  nested per-row grids) so header and body columns can never drift apart --
 *  the same structural guarantee `Board.tsx`'s `GRID_TEMPLATE` and the
 *  rankings-pane fix (`DRAFT_LIST_GRID_TEMPLATE`) already rely on. */
function PickOrderGrid({
  teams,
  rounds,
  teamSlots,
  picksByOverall,
  rowsById,
  teamLabels,
  onClockSlot,
  currentRound,
  draftComplete,
  tier,
}: {
  teams: number;
  rounds: number;
  teamSlots: number[];
  picksByOverall: Map<number, DraftPickRecord>;
  rowsById: Map<number, BoardRow>;
  teamLabels: TeamLabel[];
  onClockSlot: number;
  currentRound: number;
  draftComplete: boolean;
  tier: CellTier;
}) {
  const GUTTER = 78;
  const template = `${GUTTER}px repeat(${teams}, minmax(${tier === 'compact' ? 80 : tier === 'wide' ? 96 : 118}px, 1fr))`;
  const roundsArr = Array.from({ length: rounds }, (_, i) => i + 1);
  return (
    <div data-testid="tdb-pick-order-grid" style={{ display: 'grid', gridTemplateColumns: template, gap: 1, alignContent: 'start' }}>
      <div style={{ position: 'sticky', top: 0, background: 'var(--panel)', zIndex: 1, fontSize: 9.5, color: 'var(--dim2)', padding: '4px 2px' }}>RD</div>
      {teamSlots.map((slot) => {
        const label = teamLabels[slot - 1];
        const isOnClock = slot === onClockSlot && !draftComplete;
        return (
          <div
            key={slot}
            data-testid={`tdb-header-team-${slot}`}
            style={{
              position: 'sticky',
              top: 0,
              zIndex: 1,
              background: isOnClock ? 'var(--acc)' : 'var(--panel)',
              color: isOnClock ? 'var(--bg)' : label?.isUser ? 'var(--acc)' : 'var(--txt)',
              fontSize: 10.5,
              fontWeight: 600,
              padding: '4px 5px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={label?.name}
          >
            {label?.name}
            {label?.isUser ? ' (you)' : ''}
          </div>
        );
      })}
      {roundsArr.map((round) => {
        const roundPicks = teamSlots
          .map((slot) => picksByOverall.get(overallPickForRoundSlot(round, slot, teams)))
          .filter((p): p is DraftPickRecord => p !== undefined);
        const tally = positionTally(roundPicks, rowsById);
        const tallyText = tally
          .slice(0, 2)
          .map(([pos, n]) => `${n} ${pos}`)
          .join(' · ');
        const tallyTitle = tally.map(([pos, n]) => `${n} ${pos}`).join(', ');
        return (
          <div key={`round-${round}`} style={{ display: 'contents' }}>
            <div
              data-testid={`tdb-gutter-round-${round}`}
              title={tallyTitle || undefined}
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                padding: '3px 2px',
                borderTop: '1px solid var(--line)',
                background: round === currentRound && !draftComplete ? 'color-mix(in srgb, var(--acc) 10%, transparent)' : 'transparent',
              }}
            >
              <span className="num" style={{ fontSize: 11, fontWeight: 600, color: 'var(--txt)' }}>
                {round}
              </span>
              {tallyText ? (
                <span className="num" style={{ fontSize: 8.5, color: 'var(--dim2)' }}>
                  {tallyText}
                </span>
              ) : null}
            </div>
            {teamSlots.map((slot) => {
              const overallPick = overallPickForRoundSlot(round, slot, teams);
              const pick = picksByOverall.get(overallPick);
              const posInRound = pickWithinRound(overallPick, teams);
              const addressLabel = `${round}.${String(posInRound).padStart(2, '0')}`;
              const row = pick?.playerId !== null && pick?.playerId !== undefined ? rowsById.get(pick.playerId) ?? null : null;
              const isCurrent = !draftComplete && slot === onClockSlot && round === currentRound;
              return (
                <div
                  key={`${round}-${slot}`}
                  data-testid={`tdb-cell-${round}-${slot}`}
                  style={{
                    minWidth: 0,
                    padding: '3px 4px',
                    borderTop: '1px solid var(--line)',
                    background: isCurrent ? 'color-mix(in srgb, var(--acc) 14%, transparent)' : 'transparent',
                    outline: isCurrent ? '1px solid var(--acc)' : 'none',
                    outlineOffset: -1,
                  }}
                >
                  <CellContent
                    row={row}
                    offBoardName={pick && pick.playerId === null ? pick.playerName : null}
                    tier={tier}
                    addressLabel={addressLabel}
                    isCurrent={isCurrent}
                  />
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

/** Desktop roster-slot grid: same manager columns, rows become roster slots
 *  (FINDINGS §4.5, "two independent implementations to copy"). The row
 *  template (slot labels/order) is computed once from league config alone
 *  (`buildRosterSlots` called with an empty pick list), independent of any
 *  team's actual fills, so every column's rows line up at the same index. See
 *  the `buildRosterSlots` call below for a known, pre-existing gap this view
 *  inherits rather than papers over: an off-board pick occupies no slot at
 *  all here, same as on every other screen that already calls this function. */
function RosterSlotGrid({
  teams,
  teamSlots,
  league,
  data,
  rowsById,
  draft,
  teamLabels,
  onClockSlot,
  draftComplete,
  tier,
}: {
  teams: number;
  teamSlots: number[];
  league: LeagueConfig;
  data: Dataset;
  rowsById: Map<number, BoardRow>;
  draft: DraftState;
  teamLabels: TeamLabel[];
  onClockSlot: number;
  draftComplete: boolean;
  tier: CellTier;
}) {
  // Known, pre-existing gap in `buildRosterSlots` itself (ui/data/rosterSlots.ts),
  // shared by every consumer of it including `LiveOpponents.tsx`'s MY ROSTER/
  // opponent cards, not introduced here: a pick with `playerId === null` (typed/
  // off-board, or the auto-fill placeholder) is skipped by that function's own
  // fill loop and never occupies a slot at all -- so a team with such a pick
  // shows one fewer filled roster slot than picks actually made, on every
  // screen that uses this function, not just this one. Left as-is rather than
  // patched here, out of scope for FR-135 (a board-layout dispatch, not a
  // roster-arithmetic fix to a function three other screens already depend on)
  // -- logged to docs/ideas-inbox.md.
  const template = buildRosterSlots([], league, data, rowsById);
  const perTeam: RosterSlot[][] = teamSlots.map((slot) =>
    buildRosterSlots(
      draft.picks.filter((p) => p.teamSlot === slot),
      league,
      data,
      rowsById,
    ),
  );
  const GUTTER = 62;
  const gridTemplate = `${GUTTER}px repeat(${teams}, minmax(${tier === 'compact' ? 80 : tier === 'wide' ? 96 : 118}px, 1fr))`;
  return (
    <div data-testid="tdb-roster-slot-grid" style={{ display: 'grid', gridTemplateColumns: gridTemplate, gap: 1, alignContent: 'start' }}>
      <div style={{ position: 'sticky', top: 0, background: 'var(--panel)', zIndex: 1, fontSize: 9.5, color: 'var(--dim2)', padding: '4px 2px' }}>SLOT</div>
      {teamSlots.map((slot) => {
        const label = teamLabels[slot - 1];
        const isOnClock = slot === onClockSlot && !draftComplete;
        return (
          <div
            key={slot}
            data-testid={`tdb-roster-header-team-${slot}`}
            style={{
              position: 'sticky',
              top: 0,
              zIndex: 1,
              background: isOnClock ? 'var(--acc)' : 'var(--panel)',
              color: isOnClock ? 'var(--bg)' : label?.isUser ? 'var(--acc)' : 'var(--txt)',
              fontSize: 10.5,
              fontWeight: 600,
              padding: '4px 5px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={label?.name}
          >
            {label?.name}
            {label?.isUser ? ' (you)' : ''}
          </div>
        );
      })}
      {template.map((slotDef, i) => (
        <div key={`slot-${i}`} style={{ display: 'contents' }}>
          <div
            data-testid={`tdb-roster-gutter-${i}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '3px 2px',
              borderTop: '1px solid var(--line)',
              fontSize: 9.5,
              fontWeight: 600,
              color: 'var(--dim2)',
            }}
          >
            {slotDef.position ?? slotDef.slot}
          </div>
          {teamSlots.map((slot, teamIdx) => {
            const cell = perTeam[teamIdx]?.[i];
            const row = cell?.row ?? null;
            return (
              <div
                key={`${i}-${slot}`}
                data-testid={`tdb-roster-cell-${slot}-${i}`}
                style={{ minWidth: 0, padding: '3px 4px', borderTop: '1px solid var(--line)' }}
              >
                {row === null ? (
                  <span style={{ fontSize: 11, color: 'var(--dim2)' }}>—</span>
                ) : (
                  <CellContent row={row} offBoardName={null} tier={tier} addressLabel="" isCurrent={false} />
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

/** Below `MOBILE_BREAKPOINT`: the two-axis grid is abandoned, per FINDINGS
 *  §4.6. Whichever axis isn't the list becomes a horizontally-scrollable
 *  chip row -- rounds for pick-order, teams for roster-slot -- so the same
 *  two views survive narrow width without a frozen-column compromise no
 *  product researched was found using. */
function MobileBoard({
  view,
  teams,
  rounds,
  teamSlots,
  picksByOverall,
  rowsById,
  teamLabels,
  onClockSlot,
  currentRound,
  draftComplete,
  league,
  data,
  draft,
}: {
  view: BoardView;
  teams: number;
  rounds: number;
  teamSlots: number[];
  picksByOverall: Map<number, DraftPickRecord>;
  rowsById: Map<number, BoardRow>;
  teamLabels: TeamLabel[];
  onClockSlot: number;
  currentRound: number;
  draftComplete: boolean;
  league: LeagueConfig;
  data: Dataset;
  draft: DraftState;
}) {
  const [round, setRound] = useState(() => Math.min(Math.max(currentRound, 1), rounds));
  const [teamSlot, setTeamSlot] = useState(() => teamSlots[0] ?? 1);
  useEffect(() => {
    if (!draftComplete) setRound(Math.min(Math.max(currentRound, 1), rounds));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentRound]);

  if (view === 'pick-order') {
    return (
      <div data-testid="tdb-mobile-round" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 4 }}>
          {Array.from({ length: rounds }, (_, i) => i + 1).map((r) => (
            <button
              key={r}
              data-testid={`tdb-mobile-round-chip-${r}`}
              aria-pressed={r === round}
              onClick={() => setRound(r)}
              style={{
                flex: 'none',
                padding: '4px 9px',
                fontSize: 11,
                fontWeight: r === round ? 600 : 400,
                color: r === round ? 'var(--txt)' : 'var(--dim2)',
                background: r === round ? 'var(--panel2)' : 'transparent',
                border: `1px solid ${r === currentRound && !draftComplete ? 'var(--acc)' : 'var(--line)'}`,
              }}
            >
              R{r}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {teamSlots.map((slot) => {
            const overallPick = overallPickForRoundSlot(round, slot, teams);
            const pick = picksByOverall.get(overallPick);
            const posInRound = pickWithinRound(overallPick, teams);
            const addressLabel = `${round}.${String(posInRound).padStart(2, '0')}`;
            const row = pick?.playerId !== null && pick?.playerId !== undefined ? rowsById.get(pick.playerId) ?? null : null;
            const label = teamLabels[slot - 1];
            const isCurrent = !draftComplete && slot === onClockSlot && round === currentRound;
            return (
              <div
                key={slot}
                data-testid={`tdb-mobile-round-row-${slot}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 8px',
                  border: `1px solid ${isCurrent ? 'var(--acc)' : 'var(--line)'}`,
                  background: isCurrent ? 'color-mix(in srgb, var(--acc) 10%, transparent)' : 'var(--panel)',
                }}
              >
                <span className="num" style={{ fontSize: 10, color: 'var(--dim2)', width: 34, flex: 'none' }}>
                  {addressLabel}
                </span>
                <span style={{ fontSize: 11.5, color: label?.isUser ? 'var(--acc)' : 'var(--txt)', width: 92, flex: 'none', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {label?.name}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <CellContent row={row} offBoardName={pick && pick.playerId === null ? pick.playerName : null} tier="wide" addressLabel={addressLabel} isCurrent={isCurrent} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  const rosterSlots = buildRosterSlots(
    draft.picks.filter((p) => p.teamSlot === teamSlot),
    league,
    data,
    rowsById,
  );
  return (
    <div data-testid="tdb-mobile-teams" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', gap: 4, overflowX: 'auto', paddingBottom: 4 }}>
        {teamSlots.map((slot) => (
          <button
            key={slot}
            data-testid={`tdb-mobile-team-chip-${slot}`}
            aria-pressed={slot === teamSlot}
            onClick={() => setTeamSlot(slot)}
            style={{
              flex: 'none',
              padding: '4px 9px',
              fontSize: 11,
              fontWeight: slot === teamSlot ? 600 : 400,
              color: slot === teamSlot ? 'var(--txt)' : 'var(--dim2)',
              background: slot === teamSlot ? 'var(--panel2)' : 'transparent',
              border: `1px solid ${slot === onClockSlot && !draftComplete ? 'var(--acc)' : 'var(--line)'}`,
            }}
          >
            {teamLabels[slot - 1]?.name ?? `Team ${slot}`}
          </button>
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {rosterSlots.map((s, i) => (
          <div
            key={i}
            data-testid={`tdb-mobile-team-row-${i}`}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 8px', border: '1px solid var(--line)', background: 'var(--panel)' }}
          >
            <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--dim2)', width: 40, flex: 'none' }}>{s.position ?? s.slot}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              {s.row === null ? (
                <span style={{ fontSize: 11, color: 'var(--dim2)' }}>—</span>
              ) : (
                <CellContent row={s.row} offBoardName={null} tier="wide" addressLabel="" isCurrent={false} />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function TraditionalDraftBoard({
  data,
  league,
  draft,
  rowsById,
  leagueId,
}: {
  data: Dataset;
  league: LeagueConfig;
  draft: DraftState;
  rowsById: Map<number, BoardRow>;
  leagueId: string;
}) {
  const [view, setView] = useState<BoardView>('pick-order');
  const width = useViewportWidth();
  const teams = league.teams.kind === 'present' ? league.teams.value : 0;
  const rounds = league.rounds.kind === 'present' ? league.rounds.value : 0;
  const userSlot = league.userSlot.kind === 'present' ? league.userSlot.value : 0;

  const teamNameBySlot = useMemo(() => new Map(data.opponents.opponents.map((o) => [o.draft_slot_2026, o.team_name])), [data.opponents]);
  const typedNames = useMemo(() => loadOpponentNames(leagueId), [leagueId]);

  if (teams === 0 || rounds === 0) {
    return (
      <div style={{ padding: 20 }}>
        <div className="empty">
          <strong>Draft board needs league.json:teams and rounds.</strong> One or more is missing
          for this league.
        </div>
      </div>
    );
  }

  const teamSlots = Array.from({ length: teams }, (_, i) => i + 1);
  const teamLabels = teamSlots.map((slot) => teamLabelFor(slot, teamNameBySlot, typedNames, userSlot));
  const picksByOverall = new Map(draft.picks.map((p) => [p.overallPick, p]));
  const currentPick = currentOverallPick(draft.picks);
  const draftComplete = currentPick > teams * rounds;
  const onClockSlot = draftComplete ? 0 : teamSlotAtPick(currentPick, teams);
  const currentRound = draftComplete ? rounds : Math.ceil(currentPick / teams);
  const posInRound = draftComplete ? teams : pickWithinRound(currentPick, teams);
  const tier = tierFor(width);
  const isMobile = width < MOBILE_BREAKPOINT;

  return (
    <div data-testid="tdb-root" data-tier={tier} data-mobile={isMobile} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <ViewToggle view={view} setView={setView} />
        <span style={{ fontSize: 10.5, color: 'var(--dim2)' }}>{draft.picks.length} of {teams * rounds} picks made</span>
      </div>
      <OnClockBar
        draftComplete={draftComplete}
        teams={teams}
        currentPick={currentPick}
        currentRound={currentRound}
        posInRound={posInRound}
        teamLabel={onClockSlot ? teamLabels[onClockSlot - 1] ?? null : null}
      />
      <div style={{ overflowX: 'auto' }}>
        {isMobile ? (
          <MobileBoard
            view={view}
            teams={teams}
            rounds={rounds}
            teamSlots={teamSlots}
            picksByOverall={picksByOverall}
            rowsById={rowsById}
            teamLabels={teamLabels}
            onClockSlot={onClockSlot}
            currentRound={currentRound}
            draftComplete={draftComplete}
            league={league}
            data={data}
            draft={draft}
          />
        ) : view === 'pick-order' ? (
          <PickOrderGrid
            teams={teams}
            rounds={rounds}
            teamSlots={teamSlots}
            picksByOverall={picksByOverall}
            rowsById={rowsById}
            teamLabels={teamLabels}
            onClockSlot={onClockSlot}
            currentRound={currentRound}
            draftComplete={draftComplete}
            tier={tier}
          />
        ) : (
          <RosterSlotGrid
            teams={teams}
            teamSlots={teamSlots}
            league={league}
            data={data}
            rowsById={rowsById}
            draft={draft}
            teamLabels={teamLabels}
            onClockSlot={onClockSlot}
            draftComplete={draftComplete}
            tier={tier}
          />
        )}
      </div>
    </div>
  );
}
