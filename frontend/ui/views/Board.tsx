import { useMemo, useState } from 'react';
import type { BoardRow } from '../data/board';
import { isStartable, type LeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { useWatchlist } from '../data/useWatchlist';
import { Value } from '../components/Value';
import { PlayerDetail } from '../components/PlayerDetail';
import { decimal, integer, interval, signed } from '../lib/format';
import { RoundGrid } from './RoundGrid';

/**
 * The board.
 *
 * Header and control row are ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html, lines 405-461): title +
 * metadata line + export buttons, then a Table/Round-grid toggle, position tabs, a
 * "Delta view" toggle, and a player count. The ten-column table grid (430-459),
 * its Δ glyph convention, its per-column sort comparators and its tier-band
 * dividers (line 2319-2330) are ported the same way. Sticky headers and the
 * row-click detail panel were added on top, per explicit instruction.
 *
 * Departures from the source, each intentional and noted rather than silent:
 *   - Export CSV / Export PDF: the prototype's buttons are gone (design/
 *     INERT-CONTROLS.md, FR-037 -- "a control that cannot act is not a
 *     control"). Nothing in this app generates either file yet, so there is no
 *     affordance to click and discover that; the fact is folded into the
 *     provenance line above the table instead ("· export not built"), one line
 *     for both rather than two dead buttons.
 *   - "Round grade grid" switches to this app's own snake-order draft grid, not
 *     the prototype's VBD-tier-band grid grouped by round and position -- that is
 *     a content rebuild, not a shell/interaction change.
 *   - Tier bands only render when a single position is selected, not "ALL". The
 *     prototype computes a separate synthetic cross-position "global tier" from
 *     VBD gaps for its ALL view (a ~4.5-point-gap, max-9-per-tier heuristic that
 *     exists only in the prototype's own code, not in any export) -- reproducing
 *     it would mean inventing a threshold this app cannot source from data.
 *     board.json's real `tier_label` is assigned per position, not globally: in
 *     overall-rank order across every position it is not contiguous -- verified
 *     against the live export, the same "T1" label re-triggers 74 separate times
 *     across the full board, one cluster per position, versus a clean 5
 *     transitions (matching the 5 real tiers) within any single position. Bands
 *     from that field in the ALL view would render "TIER 1" over and over as
 *     positions interleave by rank, which is confusing rather than wrong -- worse
 *     than the prototype's synthetic field, not a faithful stand-in for it. Pick
 *     a position tab to see bands; the real, per-position field is coherent there.
 *   - `curve_caveat` ("R² is 0.16-0.27... treat projections as weak") has no line
 *     in the prototype's header but is a standing requirement in this project's
 *     data contract ("Surface this in the UI"). Kept as a third bar.
 *   - The sort indicator (▲/▼ beside the active column, direction flips on a
 *     second click of the same column) is an explicit addition beyond the
 *     prototype, which highlights the active column but has no direction glyph
 *     and no click-again-to-reverse behaviour.
 */

type ViewMode = 'table' | 'grid';
type PositionFilter = 'ALL' | 'QB' | 'RB' | 'WR' | 'TE' | 'DEF';
type SortKey =
  | 'rank'
  | 'name'
  | 'pos'
  | 'team'
  | 'bye'
  | 'proj'
  | 'cons'
  | 'adp'
  | 'delta'
  | 'vbd'
  | 'tier'
  | 'absdelta';

const POSITION_TABS: PositionFilter[] = ['ALL', 'QB', 'RB', 'WR', 'TE', 'DEF'];

/** Position accent colours, ported verbatim from the prototype's token set. */
const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
  DEF: 'var(--def)',
};

const GRID_TEMPLATE = '64px minmax(180px,1fr) 72px 54px 54px 168px 70px 70px 60px 72px 64px';

/** Column id, label, and the direction a first click on it should sort in --
 *  ported from the prototype's `bcols` (line 2314), with "better first" as the
 *  default direction for proj/delta/vbd, matching its own comparator (line 2319).
 *
 *  ADP (contract 1.14.0, thread 082) sits beside CONS, not beside Δ. It is a
 *  separate market-vs-expert claim, deliberately not turned into a second
 *  delta column -- see the trace-fields.ts 1.14.0 changelog entry for the
 *  reasoning. Label reads "ADP (MFL)" rather than bare "ADP" so a glance
 *  cannot mistake a MyFantasyLeague proxy for this league's own draft. */
const COLUMNS: Array<{ key: SortKey; label: string; defaultDir: 1 | -1 }> = [
  { key: 'rank', label: 'RANK', defaultDir: 1 },
  { key: 'name', label: 'PLAYER', defaultDir: 1 },
  { key: 'pos', label: 'POS', defaultDir: 1 },
  { key: 'team', label: 'TM', defaultDir: 1 },
  { key: 'bye', label: 'BYE', defaultDir: 1 },
  { key: 'proj', label: 'PROJ (CI)', defaultDir: -1 },
  { key: 'cons', label: 'CONS', defaultDir: 1 },
  { key: 'adp', label: 'ADP (MFL)', defaultDir: 1 },
  { key: 'delta', label: 'Δ', defaultDir: -1 },
  { key: 'vbd', label: 'VBD', defaultDir: -1 },
  { key: 'tier', label: 'TIER', defaultDir: 1 },
];

/** Missing values sort to the bottom regardless of direction -- porting the
 *  prototype's `nz()` helper (line 2318). */
function numOrBottom(cell: { kind: string; value?: number }, dir: 1 | -1): number {
  if (cell.kind !== 'present') return dir === 1 ? Infinity : -Infinity;
  return cell.value as number;
}

function textOf(cell: { kind: string; value?: unknown }): string {
  return cell.kind === 'present' ? String(cell.value) : '';
}

function compareRows(a: BoardRow, b: BoardRow, key: SortKey): number {
  switch (key) {
    case 'absdelta': {
      const ad = a.deltaVsConsensus.kind === 'present' ? Math.abs(a.deltaVsConsensus.value) : -1;
      const bd = b.deltaVsConsensus.kind === 'present' ? Math.abs(b.deltaVsConsensus.value) : -1;
      return bd - ad;
    }
    case 'name':
      return textOf(a.name).localeCompare(textOf(b.name));
    case 'pos':
      return (a.raw.position + String(a.positionalRank).padStart(2, '0')).localeCompare(
        b.raw.position + String(b.positionalRank).padStart(2, '0'),
      );
    case 'team':
      return textOf(a.team).localeCompare(textOf(b.team));
    case 'bye':
      return numOrBottom(a.byeWeek, 1) - numOrBottom(b.byeWeek, 1);
    case 'proj':
      return numOrBottom(b.projectedPoints, -1) - numOrBottom(a.projectedPoints, -1);
    case 'cons':
      return numOrBottom(a.consensusRank, 1) - numOrBottom(b.consensusRank, 1);
    case 'adp':
      return numOrBottom(a.adp, 1) - numOrBottom(b.adp, 1);
    case 'delta':
      return numOrBottom(b.deltaVsConsensus, -1) - numOrBottom(a.deltaVsConsensus, -1);
    case 'vbd':
      return numOrBottom(b.vbd, -1) - numOrBottom(a.vbd, -1);
    case 'tier': {
      const ta = a.raw.tier;
      const tb = b.raw.tier;
      return ta - tb || numOrBottom(a.overallRank, 1) - numOrBottom(b.overallRank, 1);
    }
    case 'rank':
    default:
      return numOrBottom(a.overallRank, 1) - numOrBottom(b.overallRank, 1);
  }
}

export function Board({
  data,
  rows,
  league,
  onFocusPlayer,
}: {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
  onFocusPlayer?: (name: string | null) => void;
}) {
  const [view, setView] = useState<ViewMode>('table');
  const [position, setPosition] = useState<PositionFilter>('ALL');
  const [sort, setSort] = useState<{ key: SortKey; dir: 1 | -1 }>({ key: 'rank', dir: 1 });
  const [selected, setSelected] = useState<number | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [watchlist, toggleWatch] = useWatchlist();

  const deltaView = sort.key === 'absdelta';

  const filtered = useMemo(() => {
    const byPosition = position === 'ALL' ? rows : rows.filter((r) => r.raw.position === position);
    const dir = sort.key === 'absdelta' ? 1 : sort.dir;
    return [...byPosition].sort((a, b) => dir * compareRows(a, b, sort.key));
  }, [rows, position, sort]);

  const selectedRow = filtered.find((r) => r.id === selected) ?? null;

  function selectRow(id: number | null) {
    setSelected(id);
    const row = id === null ? null : (filtered.find((r) => r.id === id) ?? null);
    onFocusPlayer?.(row && row.name.kind === 'present' ? row.name.value : null);
  }

  function toggleDelta() {
    setSort((s) => (s.key === 'absdelta' ? { key: 'rank', dir: 1 } : { key: 'absdelta', dir: 1 }));
  }

  function clickColumn(key: SortKey, defaultDir: 1 | -1) {
    setSort((s) => (s.key === key ? { key, dir: (s.dir * -1) as 1 | -1 } : { key, dir: defaultDir }));
  }

  // The prototype's own provenance-line shape (line 2409): source, state, generated
  // timestamp, and a real count -- every piece a sourced value, nothing invented.
  // Thread 069: the scoring format sits beside the source it was confirmed for.
  // board.json:scoring_format is null (or absent, pre-1.11.0) when the source
  // rows carry no confirmed format -- say so instead of guessing one.
  const scoringFormat =
    data.board.scoring_format != null
      ? data.board.scoring_format.replace(/_/g, ' ')
      : 'scoring format unconfirmed';
  // design/INERT-CONTROLS.md: Export CSV and Export PDF were both dead buttons
  // ("not built" -- nothing in this app generates either file yet). One rule
  // covers both: remove the buttons, put the fact where they were -- one line,
  // folded into the provenance line that already sits here, since "two dead
  // buttons is not twice the information."
  const provenance =
    `${data.board.consensus_source} · ${scoringFormat} · ` +
    `${data.board.consensus_state.replace(/_/g, ' ')} · ` +
    `generated ${data.board.generated_utc} · ${rows.length} players loaded · export not built`;

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          flex: 'none',
          padding: '11px 20px',
          borderBottom: '1px solid var(--line)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          background: 'var(--panel)',
        }}
      >
        <h2 style={{ fontSize: 16, fontWeight: 600 }}>Board</h2>
        <div style={{ fontFamily: 'var(--font-num)', fontSize: 12, color: 'var(--dim2)' }}>{provenance}</div>
        <div style={{ flex: 1 }} />
      </div>

      <div
        style={{
          flex: 'none',
          padding: '11px 20px',
          borderBottom: '1px solid var(--line)',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}
      >
        <div style={{ display: 'flex', border: '1px solid var(--line2)' }}>
          <button
            aria-pressed={view === 'table'}
            onClick={() => setView('table')}
            style={{
              padding: '6px 15px',
              background: view === 'table' ? 'var(--panel2)' : 'transparent',
              border: 0,
              color: view === 'table' ? 'var(--txt)' : 'var(--dim2)',
              fontSize: 12.5,
              fontWeight: 600,
            }}
          >
            Table
          </button>
          <button
            aria-pressed={view === 'grid'}
            onClick={() => setView('grid')}
            style={{
              padding: '6px 15px',
              background: view === 'grid' ? 'var(--panel2)' : 'transparent',
              border: 0,
              color: view === 'grid' ? 'var(--txt)' : 'var(--dim2)',
              fontSize: 12.5,
              fontWeight: 600,
            }}
          >
            Round grade grid
          </button>
        </div>

        <div style={{ display: 'flex', gap: 4 }}>
          {POSITION_TABS.map((t) => {
            const active = position === t;
            return (
              <button
                key={t}
                aria-pressed={active}
                onClick={() => setPosition(t)}
                style={{
                  padding: '5px 14px',
                  background: active ? 'var(--panel2)' : 'transparent',
                  border: `1px solid ${active ? 'var(--line2)' : 'var(--line)'}`,
                  color: active ? (POSITION_COLOR[t] ?? 'var(--txt)') : 'var(--dim2)',
                  letterSpacing: '.045em',
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                {t}
              </button>
            );
          })}
        </div>

        <button
          aria-pressed={deltaView}
          onClick={toggleDelta}
          style={{
            padding: '5px 14px',
            background: deltaView ? 'var(--panel2)' : 'transparent',
            border: `1px solid ${deltaView ? 'var(--up)' : 'var(--line)'}`,
            color: deltaView ? 'var(--up)' : 'var(--dim2)',
            fontSize: 12.5,
          }}
        >
          Delta view — biggest disagreements
        </button>

        <div style={{ flex: 1 }} />
        <span style={{ fontFamily: 'var(--font-num)', fontSize: 12, color: 'var(--dim2)' }}>
          {filtered.length} players
        </span>
      </div>

      <div
        style={{
          flex: 'none',
          padding: '8px 20px',
          borderBottom: '1px solid var(--line)',
          fontSize: 12.5,
          color: 'var(--dim)',
        }}
      >
        {data.board.curve_caveat}
      </div>

      {view === 'table' ? (
        <BoardTable
          rows={filtered}
          league={league}
          selected={selected}
          onSelect={selectRow}
          sort={sort}
          onClickColumn={clickColumn}
          bandsEnabled={sort.key === 'rank' && sort.dir === 1 && position !== 'ALL'}
          expandedId={expandedId}
          onToggleExpand={(id) => setExpandedId((cur) => (cur === id ? null : id))}
          adpHeaderTitle={computeAdpHeaderTitle(data.board.adp_source_note, data.board.adp_as_of_date)}
        />
      ) : (
        <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '15px 20px' }}>
          <RoundGrid league={league} rows={rows} />
        </div>
      )}

      {selectedRow ? (
        <PlayerDetail
          row={selectedRow}
          rows={rows}
          data={data}
          league={league}
          picks={[]}
          watchlist={watchlist}
          onToggleWatch={toggleWatch}
          onClose={() => selectRow(null)}
        />
      ) : null}
    </div>
  );
}

/** Hover text for the ADP column header -- the export's own `adp_source_note`
 *  verbatim, so the reachable-caveat requirement (thread 082) is met without
 *  a permanent extra bar eating vertical space on every row (Principle #4:
 *  density is the product). Null-safe: a pre-1.14.0 export still renders the
 *  column, just without this detail. */
export function computeAdpHeaderTitle(note: string | null | undefined, asOfDate: string | null | undefined): string {
  const parts = [note ?? 'MyFantasyLeague ADP proxy -- not this league\'s own draft history.'];
  if (asOfDate) parts.push(`Snapshot as of ${asOfDate}.`);
  return parts.join(' ');
}

function BoardTable({
  rows,
  league,
  selected,
  onSelect,
  sort,
  onClickColumn,
  bandsEnabled,
  expandedId,
  onToggleExpand,
  adpHeaderTitle,
}: {
  rows: BoardRow[];
  league: LeagueConfig;
  selected: number | null;
  onSelect: (id: number | null) => void;
  sort: { key: SortKey; dir: 1 | -1 };
  onClickColumn: (key: SortKey, defaultDir: 1 | -1) => void;
  bandsEnabled: boolean;
  expandedId: number | null;
  onToggleExpand: (id: number) => void;
  adpHeaderTitle: string;
}) {
  if (rows.length === 0) {
    return (
      <div style={{ padding: 20 }}>
        <div className="empty">
          <strong>Nothing matches these filters.</strong> Choose a different position tab to see
          more of the board.
        </div>
      </div>
    );
  }

  // Tier band dividers, ported from the prototype's brows builder (line
  // 2320-2330): a divider row inserted whenever the tier changes, only while the
  // table is in its natural rank order -- sorting by anything else (a column
  // click, or Delta view) breaks the grouping a band implies, so bands only show
  // in the one order where consecutive rows really do share a tier.
  const items: Array<{ kind: 'band'; tier: string; count: number } | { kind: 'row'; row: BoardRow }> = [];
  if (bandsEnabled) {
    let lastTier: string | null = null;
    for (const row of rows) {
      const tier = row.tierLabel.kind === 'present' ? row.tierLabel.value : null;
      if (tier !== null && tier !== lastTier) {
        lastTier = tier;
        const count = rows.filter((r) => r.tierLabel.kind === 'present' && r.tierLabel.value === tier).length;
        items.push({ kind: 'band', tier, count });
      }
      items.push({ kind: 'row', row });
    }
  } else {
    for (const row of rows) items.push({ kind: 'row', row });
  }

  return (
    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 2,
          display: 'grid',
          gridTemplateColumns: GRID_TEMPLATE,
          padding: '9px 20px',
          borderBottom: '1px solid var(--line2)',
          background: 'var(--panel)',
        }}
      >
        {COLUMNS.map((col) => {
          const active = sort.key === col.key || (col.key === 'delta' && sort.key === 'absdelta');
          return (
            <span
              key={col.key}
              onClick={() => onClickColumn(col.key, col.defaultDir)}
              title={col.key === 'adp' ? adpHeaderTitle : undefined}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                fontSize: 12,
                letterSpacing: '.08em',
                color: active ? 'var(--txt)' : 'var(--dim2)',
                cursor: 'pointer',
              }}
            >
              {col.label}
              {sort.key === col.key ? <span>{sort.dir === 1 ? '▲' : '▼'}</span> : null}
            </span>
          );
        })}
      </div>

      {(() => {
        // Row index, counting rows only (band dividers don't consume a slot) --
        // drives the alternating row tint that replaces the old per-row hairline
        // in light mode (docs/design/LIGHT-THEME-SHADING.md). See BoardRowLine:
        // undefined in dark mode, --row-alt/--row-line fall back to today's
        // transparent/var(--line) exactly, so dark is unaffected.
        let rowIndex = 0;
        return items.map((item) =>
          item.kind === 'band' ? (
            <div
              key={`band-${item.tier}`}
              style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '13px 20px 6px' }}
            >
              <span style={{ fontSize: 12, letterSpacing: '.1em', color: 'var(--dim)' }}>
                TIER {item.tier.replace('T', '')}
              </span>
              <span style={{ flex: 1, height: 1, background: 'var(--line2)' }} />
              <span style={{ fontFamily: 'var(--font-num)', fontSize: 12, color: 'var(--dim2)' }}>
                {item.count} players
              </span>
            </div>
          ) : (
            <BoardRowLine
              key={item.row.id}
              row={item.row}
              league={league}
              selected={item.row.id === selected}
              alt={rowIndex++ % 2 === 1}
              onSelect={onSelect}
              expanded={item.row.id === expandedId}
              onToggleExpand={onToggleExpand}
            />
          ),
        );
      })()}
    </div>
  );
}

function BoardRowLine({
  row,
  league,
  selected,
  alt,
  onSelect,
  expanded,
  onToggleExpand,
}: {
  row: BoardRow;
  league: LeagueConfig;
  selected: boolean;
  alt: boolean;
  onSelect: (id: number | null) => void;
  expanded: boolean;
  onToggleExpand: (id: number) => void;
}) {
  const startable = isStartable(league, row.raw.position, row.positionalRank);
  // Row background/border: selected uses --panel2 (raised in light, the row
  // you are on and only that -- unchanged in dark). Unselected rows alternate
  // with --row-alt, which only exists in light mode (docs/design/
  // LIGHT-THEME-SHADING.md's "alternating row tint replaces row borders");
  // undefined in dark, so it falls back to today's transparent there. The
  // hairline itself falls back the same way via --row-line.
  const rowBg = selected ? 'var(--panel2)' : alt ? 'var(--row-alt, transparent)' : 'transparent';
  const rowBorder = expanded ? 'none' : '1px solid var(--row-line, var(--line))';
  return (
    <div>
      <div
        onClick={() => onSelect(selected ? null : row.id)}
        style={{
          display: 'grid',
          gridTemplateColumns: GRID_TEMPLATE,
          alignItems: 'center',
          padding: '8px 20px',
          borderBottom: rowBorder,
          cursor: 'pointer',
          background: rowBg,
          fontFamily: 'var(--font-ui)',
          fontSize: 13,
          color: 'var(--txt)',
        }}
      >
        <span className="num" style={{ color: 'var(--dim2)' }}>
          <Value cell={row.overallRank} render={integer} />
        </span>
        <span
          style={{
            fontWeight: 600,
            fontSize: 14,
            color: startable === false ? 'var(--dim2)' : 'var(--txt)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          <Value cell={row.name} render={(v) => v} />
          {row.raw.suspension_flag ? <SuspBadge row={row} /> : null}
        </span>
        <span style={{ letterSpacing: '.045em', color: POSITION_COLOR[row.raw.position] ?? 'var(--txt)', fontWeight: 600 }}>
          <Value cell={row.position} render={(v) => v} />
        </span>
        <span style={{ letterSpacing: '.045em', color: 'var(--dim2)' }}>
          <Value cell={row.team} render={(v) => v} />
        </span>
        <span className="num" style={{ color: 'var(--dim2)' }}>
          <Value cell={row.byeWeek} render={integer} />
        </span>
        <ProjCell row={row} />
        <span className="num" style={{ color: 'var(--dim2)' }}>
          <Value cell={row.consensusRank} render={integer} />
        </span>
        <AdpCell row={row} />
        <span
          onClick={(e) => {
            e.stopPropagation();
            onToggleExpand(row.id);
          }}
          title="Why this rank -- click to expand"
          style={{ cursor: 'pointer' }}
        >
          <DeltaCell row={row} />
        </span>
        <span className="num">
          <Value cell={row.vbd} render={decimal} />
        </span>
        <span style={{ letterSpacing: '.045em', color: 'var(--dim2)' }}>
          <Value cell={row.tierLabel} render={(v) => v} />
        </span>
      </div>
      {expanded ? (
        <div
          style={{
            padding: '4px 20px 12px 84px',
            borderBottom: '1px solid var(--row-line, var(--line))',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            background: 'var(--panel2)',
          }}
        >
          {row.replacementLevelsComponent.kind === 'present' ? (
            <div style={{ fontSize: 12, color: 'var(--dim)' }}>
              Replacement levels: <span className="num">{signed(row.replacementLevelsComponent.value)}</span>{' '}
              <span className="num" style={{ color: 'var(--dim2)' }}>
                ({row.replacementLevelsComponent.path})
              </span>
            </div>
          ) : null}
          {row.scoringAndVbdComponent.kind === 'present' ? (
            <div style={{ fontSize: 12, color: 'var(--dim)' }}>
              Scoring and VBD method: <span className="num">{signed(row.scoringAndVbdComponent.value)}</span>{' '}
              <span className="num" style={{ color: 'var(--dim2)' }}>
                ({row.scoringAndVbdComponent.path})
              </span>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/**
 * Contract 1.12.0 (thread 073): a confirmed suspension on file gets a badge on
 * the row itself, not only inside the detail sheet -- the pre-mortem's #3
 * failure mode is a suspended player sitting unflagged in the top 60. Rendered
 * only when board.json:suspension_flag is true; every live row is false today
 * (the curated list is empty), so the badge's absence everywhere is the
 * correct current state, not a dead branch.
 */
function SuspBadge({ row }: { row: BoardRow }) {
  const note = row.raw.suspension_adjustment_note;
  const games = row.raw.suspension_games;
  const title =
    note === 'not_adjusted_pending_appeal'
      ? 'Suspension on file — appeal pending, projection deliberately not adjusted · board.json:suspension_flag'
      : note === 'games_adjusted' && games != null
        ? `Suspended ${games} games — projection adjusted · board.json:suspension_flag`
        : 'Suspension on file · board.json:suspension_flag';
  return (
    <span
      title={title}
      style={{
        marginLeft: 6,
        fontSize: 9,
        fontWeight: 600,
        letterSpacing: '.08em',
        color: 'var(--down)',
        border: '1px solid var(--down)',
        padding: '0 4px',
        verticalAlign: 'middle',
      }}
    >
      SUSP
    </span>
  );
}

/** PROJ (CI): a projection and its interval are one column in the prototype, since
 *  an interval is never meaningful without the number it brackets. Absence renders
 *  as the em-dash used everywhere else in this app plus "no projection" in dim
 *  text, matching the prototype's own wording for the same state. */
function ProjCell({ row }: { row: BoardRow }) {
  if (row.projectedPoints.kind === 'absent') {
    return (
      <span>
        <span className="val-absent" title={row.projectedPoints.reason}>
          —
        </span>{' '}
        <span style={{ color: 'var(--dim2)', fontSize: 12 }}>no projection</span>
      </span>
    );
  }
  const ci = row.interval.kind === 'present' ? `(${interval(row.interval.value.low, row.interval.value.high)})` : '';
  return (
    <span className="num">
      <span style={{ fontWeight: 600 }}>{decimal(row.projectedPoints.value)}</span>{' '}
      <span style={{ color: 'var(--dim2)', fontSize: 12 }}>{ci}</span>
    </span>
  );
}

/**
 * ADP (contract 1.14.0, thread 082): MyFantasyLeague public-aggregate proxy,
 * NOT this league's own draft history. The column header ("ADP (MFL)") is
 * the glance-level label so this can never be mistaken for the league's own
 * ADP; the tooltip carries the rest of `adp_source` traveling with the value
 * (full-PPR-vs-half-PPR caveat, sample range, selection rate) so it is never
 * displayed bare. Absent renders through the same em-dash convention as
 * every other column, with the reason (thin MFL coverage past ~top 230) in
 * the title -- a real null, never a fabricated 0.
 */
function AdpCell({ row }: { row: BoardRow }) {
  if (row.adp.kind === 'absent') {
    return (
      <span className="val-absent" title={row.adp.reason} aria-label={row.adp.reason}>
        —
      </span>
    );
  }
  const source =
    row.adpSource === 'mfl_proxy' ? 'MyFantasyLeague proxy, full PPR (not this league\'s ADP)' : (row.adpSource ?? 'unlabelled ADP source');
  const range =
    row.adpMinPick.kind === 'present' && row.adpMaxPick.kind === 'present'
      ? ` · range ${integer(row.adpMinPick.value)}–${integer(row.adpMaxPick.value)}`
      : '';
  const selected =
    row.adpSelectedPct.kind === 'present'
      ? ` · taken in ${row.adpSelectedPct.value > 0 && row.adpSelectedPct.value < 1 ? '<1' : integer(row.adpSelectedPct.value)}% of sampled drafts`
      : '';
  const title = `${source}${range}${selected}\nboard.json:players[].adp`;
  return (
    <span className="num" style={{ color: 'var(--dim2)' }} title={title}>
      {decimal(row.adp.value)}
    </span>
  );
}

/** Δ glyph convention ported verbatim (prototype line 2326-2327): ▲/▼ past a
 *  2-slot deadband either side of zero, "·" inside it -- color carries the same
 *  meaning as the glyph, never alone. */
function DeltaCell({ row }: { row: BoardRow }) {
  if (row.deltaVsConsensus.kind === 'absent') {
    return (
      <span className="val-absent" title={row.deltaVsConsensus.reason}>
        —
      </span>
    );
  }
  const d = row.deltaVsConsensus.value;
  const text = d > 2 ? `▲${integer(d)}` : d < -2 ? `▼${integer(Math.abs(d))}` : '·';
  const color = d > 2 ? 'var(--up)' : d < -2 ? 'var(--down)' : 'var(--dim2)';
  return (
    <span className="num" style={{ color, fontWeight: 600 }}>
      {text}
    </span>
  );
}
