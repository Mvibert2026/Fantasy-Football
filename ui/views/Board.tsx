import { useMemo, useState } from 'react';
import { applyFilters, NO_FILTERS, POSITIONS, tierLabels, type BoardFilters, type BoardRow } from '../data/board';
import { isStartable, type LeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { NumCell, Value } from '../components/Value';
import { decimal, integer, interval, signed } from '../lib/format';
import { RoundGrid } from './RoundGrid';

/**
 * The board.
 *
 * Built sparse-first: 233 of 378 rows carry no displayable projection and no interval.
 * Those rows are not dimmed, collapsed, or pushed to the bottom -- they are the common
 * case, they keep full-weight type, and each suppressed value explains itself on hover.
 * A row with a name, a rank, a tier and a delta is still a useful row at a draft table.
 */

/** Empty or non-numeric input means "no bound", never NaN. */
function parseBound(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed === '' || trimmed === '-') return null;
  const n = Number(trimmed);
  return Number.isFinite(n) ? n : null;
}

export function Board({
  data,
  rows,
  league,
}: {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
}) {
  const [filters, setFilters] = useState<BoardFilters>(NO_FILTERS);
  const [selected, setSelected] = useState<number | null>(null);

  const tiers = useMemo(() => tierLabels(rows), [rows]);
  const visible = useMemo(() => applyFilters(rows, filters), [rows, filters]);
  const selectedRow = visible.find((r) => r.id === selected) ?? null;

  const sparseCount = rows.filter((r) => r.isSparse).length;

  function toggle<K extends 'positions' | 'tiers'>(key: K, value: string) {
    setFilters((f) => {
      const list = f[key] as string[];
      const next = list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
      return { ...f, [key]: next } as BoardFilters;
    });
  }

  return (
    <div className="stack">
      <section>
        <h2>Board</h2>
        <p className="notice">{data.board.curve_caveat}</p>
      </section>

      <section>
        <h3>Filters</h3>
        <div className="templates" style={{ marginBottom: 'var(--gap)' }}>
          {POSITIONS.map((p) => (
            <button
              key={p}
              aria-pressed={filters.positions.includes(p)}
              onClick={() => toggle('positions', p)}
            >
              {p}
            </button>
          ))}
          {tiers.map((t) => (
            <button key={t} aria-pressed={filters.tiers.includes(t)} onClick={() => toggle('tiers', t)}>
              {t}
            </button>
          ))}
          <button
            aria-pressed={filters.sparseOnly}
            onClick={() => setFilters((f) => ({ ...f, sparseOnly: !f.sparseOnly }))}
            title="Players whose projection the contract says not to display"
          >
            No projection
          </button>
          <input
            aria-label="Search player or team"
            placeholder="Search player or team"
            value={filters.search}
            onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          />
          {/*
            Controlled, so Reset actually empties them. Left uncontrolled these kept
            their typed text after a reset while the filter behind them had cleared --
            the table would show everything while the box still read "10".
            A non-numeric entry is treated as no bound rather than as NaN.
          */}
          <input
            aria-label="Minimum delta vs consensus"
            placeholder="Delta ≥"
            inputMode="numeric"
            value={filters.minDelta === null ? '' : String(filters.minDelta)}
            onChange={(e) => setFilters((f) => ({ ...f, minDelta: parseBound(e.target.value) }))}
          />
          <input
            aria-label="Maximum delta vs consensus"
            placeholder="Delta ≤"
            inputMode="numeric"
            value={filters.maxDelta === null ? '' : String(filters.maxDelta)}
            onChange={(e) => setFilters((f) => ({ ...f, maxDelta: parseBound(e.target.value) }))}
          />
          <button onClick={() => setFilters(NO_FILTERS)}>Reset</button>
        </div>

        <p className="num" style={{ fontSize: 'var(--fs-xs)', color: 'var(--fg-faint)' }}>
          {`${integer(visible.length)} of ${integer(rows.length)} shown · ${integer(sparseCount)} of ${integer(rows.length)} players carry no displayable projection`}
        </p>

        {visible.length === 0 ? (
          <div className="empty">
            <strong>Nothing matches these filters.</strong> The board holds{' '}
            {integer(rows.length)} players; loosen a filter to see them.
          </div>
        ) : (
          <div className="table-wrap">
            <table className="board">
              <thead>
                <tr>
                  <th className="n">#</th>
                  <th>Player</th>
                  <th>Pos</th>
                  <th>Team</th>
                  <th>Tier</th>
                  <th className="n">Bye</th>
                  <th className="n">Proj</th>
                  <th className="n">Interval (VBD)</th>
                  <th className="n">VBD</th>
                  <th className="n">ECR</th>
                  <th className="n">Δ</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((row) => {
                  const startable = isStartable(league, row.raw.position, row.positionalRank);
                  return (
                    <tr
                      key={row.id}
                      className={row.isSparse ? 'sparse' : undefined}
                      aria-selected={row.id === selected}
                      onClick={() => setSelected(row.id === selected ? null : row.id)}
                    >
                      <NumCell cell={row.overallRank} render={integer} />
                      <td className={startable === false ? 'startable-off' : undefined}>
                        <Value cell={row.name} render={(v) => v} />
                      </td>
                      <td>
                        <Value cell={row.positionalLabel} render={(v) => v} />
                      </td>
                      <td>
                        <Value cell={row.team} render={(v) => v} />
                      </td>
                      <td>
                        <Value cell={row.tierLabel} render={(v) => v} />
                      </td>
                      <NumCell cell={row.byeWeek} render={integer} />
                      <NumCell cell={row.projectedPoints} render={decimal} />
                      <NumCell cell={row.interval} render={(v) => interval(v.low, v.high)} />
                      <NumCell cell={row.vbd} render={decimal} />
                      <NumCell cell={row.consensusRank} render={integer} />
                      <NumCell
                        cell={row.deltaVsConsensus}
                        render={signed}
                        className={
                          row.deltaVsConsensus.kind === 'present' && row.deltaVsConsensus.value > 0
                            ? 'pos'
                            : row.deltaVsConsensus.kind === 'present' && row.deltaVsConsensus.value < 0
                              ? 'neg'
                              : undefined
                        }
                      />
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedRow ? <Attribution row={selectedRow} /> : <AttributionEmpty />}

      <RoundGrid league={league} rows={rows} />
    </div>
  );
}

/**
 * The attribution panel. Structural only -- one honest claim.
 *
 * There is no "we disagree with the experts about this player" row here, suppressed or
 * otherwise, because the board holds no such opinion: it assigns every player at the
 * same positional consensus rank an identical projection. Showing a zeroed-out
 * evaluative row would imply a measurement was taken and came back nil. None was taken.
 */
function Attribution({ row }: { row: BoardRow }) {
  return (
    <section>
      <h3>Why this player moved</h3>
      <h2>
        <Value cell={row.name} render={(v) => v} />
      </h2>
      <dl className="defs">
        <dt>Against consensus</dt>
        <dd className="num">
          <Value cell={row.deltaVsConsensus} render={signed} /> places
        </dd>

        <dt>This league’s replacement levels</dt>
        <dd className="num">
          <Value cell={row.replacementLevelsComponent} render={signed} />
        </dd>

        <dt>Our scoring and VBD method</dt>
        <dd className="num">
          <Value cell={row.scoringAndVbdComponent} render={signed} />
        </dd>
      </dl>
      <p className="notice">{row.evaluativeNote}</p>
      {row.isSparse && row.projectedPoints.kind === 'absent' ? (
        <p className="notice">{row.projectedPoints.reason}</p>
      ) : null}
    </section>
  );
}

function AttributionEmpty() {
  return (
    <section>
      <h3>Why this player moved</h3>
      <div className="empty">
        <strong>No player selected.</strong> Pick a row to see how much of its distance from
        consensus comes from this league’s replacement levels and how much from our scoring and
        VBD method. That split is the whole of the attribution — the board holds no player-level
        opinion to show beside it.
      </div>
    </section>
  );
}

