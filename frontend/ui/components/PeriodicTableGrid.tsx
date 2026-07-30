import { useMemo } from 'react';
import type { BoardRow } from '../data/board';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import type { DraftPickRecord } from '../data/draft';
import { computeLiveAvailability } from '../data/liveAvailability';
import { TEAM_COLOR, teamColorOf } from '../data/teamColors';

/**
 * The periodic-table draft board (FR-044, `docs/design/PERIODIC-TABLE-GRID.md`,
 * built together with `docs/design/PANE-LAYOUT-MODES.md` since both specify the
 * same Expand gesture -- see `ui/data/layoutModes.ts`).
 *
 * What a cell carries, per the spec: **identity, position as text, and
 * depletion. No VBD, no projection, no delta.** Design's own reasoning,
 * preserved rather than second-guessed: the grid answers pattern questions --
 * how much of a position is left, am I stacking one offence -- and a number in
 * every cell makes it "a table with worse alignment," when the real board
 * three inches to the left is already better at numbers.
 *
 * Colour rule (`POSITION-COLOUR-RESOLUTION.md`, STATUS: RESOLVED): position hue
 * tints the cell at ~13% and owns the left edge; the position code sits in a
 * filled (full-strength) pill around the letters, the FantasyPros idiom
 * design's own doc names as worth adopting. The semantic accents (--acc/--up/
 * --down) are banned from this file outright -- depletion is carried by
 * luminance, strikethrough and a neutral dot, never by a hue that elsewhere
 * means good/bad/delta.
 */

const GRID_POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
  DEF: 'var(--def)',
};

const MATRIX_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'DEF'] as const;

export type GridSortMode = 'draft-order' | 'position-by-team';

export interface GridCellDatum {
  row: BoardRow;
  gone: boolean;
  /** Only meaningful when `!gone`. True when computed availability at the
   *  next user pick is under 50% -- and only when it was actually computed;
   *  see `buildGridCellData`'s doc comment. */
  underHalf: boolean;
}

function rankOf(row: BoardRow): number {
  return row.overallRank.kind === 'present' ? row.overallRank.value : Number.MAX_SAFE_INTEGER;
}

/**
 * Never-fabricate rule applied to cells, per `CLAUDE.md` Principle #2 and this
 * round's explicit instruction: "a cell whose availability cannot be computed
 * says so -- it does not render as available." `gone` is always computable --
 * it is a direct read of `taken`, the same set the board list itself uses, so
 * it is never guessed. `underHalf` is the one derived signal that can go
 * uncomputed (no further picks for the user this draft); when it cannot be
 * computed, this returns `false` -- the cell falls back to its baseline
 * "available" full-text state rather than showing a dot that would claim a
 * threshold crossing that was never checked. Absence of the dot is not a
 * claim of 100% availability, only the absence of the one extra signal.
 */
export function buildGridCellData(params: {
  rows: BoardRow[];
  taken: Set<number>;
  data: Dataset;
  league: LeagueConfig;
  picks: DraftPickRecord[];
  rowsById: Map<number, BoardRow>;
  nextUserPick: number | null;
}): GridCellDatum[] {
  const { rows, taken, data, league, picks, rowsById, nextUserPick } = params;
  return rows.map((row) => {
    const gone = taken.has(row.id);
    let underHalf = false;
    if (!gone && nextUserPick !== null) {
      const avail = computeLiveAvailability({ data, league, row, targetPick: nextUserPick, picks, rowsById });
      const pct = avail.live ?? (avail.baseline.kind === 'present' ? avail.baseline.value : null);
      underHalf = pct !== null && pct < 0.5;
    }
    return { row, gone, underHalf };
  });
}

/** 32 real NFL team codes, from the same `TEAM_COLOR` table the identity chip
 *  already uses -- `POSITION-COLOUR-RESOLUTION.md`: "TEAM_COLOR stays out of
 *  the fill -- it is identity-only and belongs on an axis or a label," which
 *  is exactly its job here (the matrix's row axis), never a cell fill. */
const MATRIX_TEAMS = Object.keys(TEAM_COLOR).sort();

export function buildPositionByTeamMatrix(cells: GridCellDatum[]): Map<string, GridCellDatum[]> {
  const map = new Map<string, GridCellDatum[]>();
  for (const c of cells) {
    const key = `${c.row.raw.team}|${c.row.raw.position}`;
    const arr = map.get(key);
    if (arr) arr.push(c);
    else map.set(key, [c]);
  }
  for (const arr of map.values()) {
    arr.sort((a, b) => rankOf(a.row) - rankOf(b.row));
  }
  return map;
}

function GridChip({ cell, dense }: { cell: GridCellDatum; dense?: boolean }) {
  const { row, gone, underHalf } = cell;
  const position = row.raw.position;
  const color = GRID_POSITION_COLOR[position] ?? 'var(--dim2)';
  const name = row.name.kind === 'present' ? row.name.value : '(unnamed)';
  return (
    <div
      title={`${name} -- ${position}${gone ? ', gone' : underHalf ? ', under 50% likely available at your next pick' : ', available'}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 5,
        minWidth: 0,
        padding: dense ? '3px 6px 3px 5px' : '4px 7px 4px 5px',
        // Position hue tints the cell at ~13% and owns the left edge --
        // POSITION-COLOUR-RESOLUTION.md's exact language. color-mix so the
        // same rule works unmodified against both themes' own hue values.
        background: `color-mix(in srgb, ${color} 13%, transparent)`,
        borderLeft: `3px solid ${color}`,
        opacity: gone ? 0.5 : 1,
      }}
    >
      <span
        style={{
          flex: 'none',
          fontFamily: 'var(--font-ui)',
          fontSize: 10,
          fontWeight: 600,
          lineHeight: 1,
          color: '#fff',
          background: color,
          borderRadius: 999,
          padding: '2px 5px',
          letterSpacing: '.02em',
        }}
      >
        {position}
      </span>
      <span
        style={{
          flex: 1,
          minWidth: 0,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          fontSize: dense ? 11 : 11.5,
          textDecoration: gone ? 'line-through' : 'none',
          color: gone ? 'var(--dim2)' : 'var(--txt)',
        }}
      >
        {name}
      </span>
      {!gone && underHalf ? (
        <span
          aria-label="under 50% likely available at your next pick"
          style={{ flex: 'none', width: 5, height: 5, borderRadius: '50%', background: 'var(--dim2)' }}
        />
      ) : null}
    </div>
  );
}

/** Draft-order sort: the default. Cells flow left to right, top to bottom by
 *  the board's own overall rank -- taken players stay in place (dimmed,
 *  struck) rather than disappearing, so the grid still answers "where did
 *  this run happen" a few picks later. */
function DraftOrderGrid({ cells, dense }: { cells: GridCellDatum[]; dense?: boolean }) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(auto-fill, minmax(${dense ? 108 : 150}px, 1fr))`,
        gap: 2,
        alignContent: 'start',
      }}
    >
      {cells.map((c) => (
        <GridChip key={c.row.id} cell={c} dense={dense} />
      ))}
    </div>
  );
}

/** Position-by-team: the reason Expand exists. 32 NFL teams by 5 positions --
 *  "cannot be squeezed into the pane at all," per the design doc, so this
 *  branch is only ever mounted inside the expanded sheet. */
function PositionByTeamGrid({ cells, defNote }: { cells: GridCellDatum[]; defNote: string }) {
  const matrix = useMemo(() => buildPositionByTeamMatrix(cells), [cells]);
  const hasDefData = MATRIX_TEAMS.some((t) => (matrix.get(`${t}|DEF`)?.length ?? 0) > 0);
  return (
    <div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `56px repeat(${MATRIX_POSITIONS.length}, minmax(150px, 1fr))`,
          gap: 3,
        }}
      >
        <div />
        {MATRIX_POSITIONS.map((p) => (
          <div
            key={p}
            data-testid={`grid-header-${p}`}
            style={{
              fontFamily: 'var(--font-ui)',
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: '.06em',
              color: GRID_POSITION_COLOR[p],
              padding: '2px 4px',
              position: 'sticky',
              top: 0,
              background: 'var(--panel)',
            }}
          >
            {p}
          </div>
        ))}
        {MATRIX_TEAMS.map((team) => (
          <div key={team} style={{ display: 'contents' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                fontFamily: 'var(--font-num)',
                fontSize: 10.5,
                fontWeight: 600,
                color: 'var(--dim)',
                padding: '3px 4px',
              }}
            >
              <span style={{ width: 6, height: 6, borderRadius: 2, background: teamColorOf(team), flex: 'none' }} />
              {team}
            </div>
            {MATRIX_POSITIONS.map((pos) => {
              const bucket = matrix.get(`${team}|${pos}`) ?? [];
              if (pos === 'DEF' && !hasDefData) {
                return (
                  <div key={pos} title={defNote} style={{ fontSize: 10, color: 'var(--dim2)', padding: '3px 4px' }}>
                    —
                  </div>
                );
              }
              return (
                <div key={pos} style={{ display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0, padding: '1px 0' }}>
                  {bucket.length === 0 ? (
                    <span style={{ fontSize: 10, color: 'var(--dim2)', padding: '2px 4px' }}>—</span>
                  ) : (
                    bucket.map((c) => <GridChip key={c.row.id} cell={c} dense />)
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      {!hasDefData ? (
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--dim2)' }}>{defNote}</div>
      ) : null}
    </div>
  );
}

export function PeriodicTableGrid({
  cells,
  sortMode,
  defNote,
  dense,
}: {
  cells: GridCellDatum[];
  sortMode: GridSortMode;
  defNote: string;
  /** Preview (in-pane) rendering uses smaller chips; the expanded sheet does not. */
  dense?: boolean;
}) {
  if (sortMode === 'position-by-team') {
    return <PositionByTeamGrid cells={cells} defNote={defNote} />;
  }
  return <DraftOrderGrid cells={cells} dense={dense} />;
}
