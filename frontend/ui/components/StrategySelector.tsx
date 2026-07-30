import {
  orderedStrategiesFor,
  rosterShapeSummary,
  strategyRuleText,
  type StrategyDisplayRow,
  type StrategyKey,
} from '../data/strategySelector';
import type { Dataset } from '../data/load';
import { useTraceMode } from '../data/traceMode';
import { decimal, integer } from '../lib/format';

/**
 * FR-061 / `docs/design/STRATEGY-SELECTOR.md`. Sits at the head of the Recommend
 * tab. "Rankings do not move; recommendations do, and they explain why" -- this
 * control only ever changes what Recommend suggests, never the board.
 *
 * Two rules enforced structurally, not by convention:
 *  - The two caveats (`power_floor.plain_english`, `lineup_assumption`) always
 *    render in full, never collapsed into one line -- the design spec explicitly
 *    forbids the "results are indicative" shortcut.
 *  - A season-dot meter fills `--acc` for a genuinely positive season and
 *    `--down` for a genuinely negative one, never the same colour regardless of
 *    direction (the FantasyPros bug this spec calls out by name).
 */

const DOT_TITLE =
  'One segment per simulated season, filled by that season\'s own sign at sigma 10 -- never green ' +
  'regardless of direction. The margin figure beside it already covers all three sigma settings.';

function SeasonDots({ seasonSigns, nSeasons }: { seasonSigns: Array<'up' | 'down' | null> | null; nSeasons: number }) {
  if (!seasonSigns) {
    return (
      <span className="num" style={{ color: 'var(--dim2)' }}>
        —
      </span>
    );
  }
  return (
    <span title={DOT_TITLE} style={{ display: 'inline-flex', gap: 3 }}>
      {Array.from({ length: nSeasons }, (_, i) => seasonSigns[i] ?? null).map((sign, i) => (
        <span
          key={i}
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            display: 'inline-block',
            background: sign === 'up' ? 'var(--acc)' : sign === 'down' ? 'var(--down)' : 'transparent',
            border: sign ? 'none' : '1px solid var(--line2)',
          }}
        />
      ))}
    </span>
  );
}

function StrategyRow({
  row,
  active,
  onSelect,
}: {
  row: StrategyDisplayRow;
  active: boolean;
  onSelect: () => void;
}) {
  const { on: showSources } = useTraceMode();
  return (
    <button
      onClick={onSelect}
      aria-pressed={active}
      title={strategyRuleText(row.key as StrategyKey, showSources)}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        width: '100%',
        textAlign: 'left',
        padding: '7px 10px',
        background: active ? 'var(--panel2)' : 'transparent',
        border: `1px solid ${active ? 'var(--acc)' : 'var(--line)'}`,
        color: 'var(--txt)',
        cursor: 'pointer',
      }}
    >
      <span style={{ flex: '0 0 150px', fontSize: 12.5, fontWeight: active ? 700 : 500 }}>
        {row.label}
        {row.isBaseline ? <span style={{ color: 'var(--dim2)', fontWeight: 400 }}> · default</span> : null}
      </span>
      <span style={{ flex: '0 0 60px' }}>
        <SeasonDots seasonSigns={row.seasonSigns} nSeasons={row.nSeasons} />
      </span>
      <span className="num" style={{ flex: '0 0 120px', fontSize: 11.5, color: 'var(--dim2)' }}>
        {row.marginRange
          ? `${row.marginRange.low >= 0 ? '+' : ''}${decimal(row.marginRange.low)} to ${row.marginRange.high >= 0 ? '+' : ''}${decimal(row.marginRange.high)}`
          : 'baseline'}
      </span>
      <span style={{ flex: 1, fontSize: 11, color: 'var(--dim2)', lineHeight: 1.4 }}>{row.verdict}</span>
    </button>
  );
}

export function StrategySelector({
  data,
  active,
  onSelect,
}: {
  data: Dataset;
  active: StrategyKey;
  onSelect: (key: StrategyKey) => void;
}) {
  const s = data.strategies;
  const { on: showSources } = useTraceMode();

  if (s === null) {
    const isPrimary = data.league.league_id === 'primary';
    const shape = rosterShapeSummary(data.league.roster);
    return (
      <div style={{ border: '1px solid var(--line2)', padding: 10, marginBottom: 12 }}>
        <div style={{ fontSize: 10, letterSpacing: '.1em', color: 'var(--dim2)' }}>STRATEGY</div>
        <p className="notice" style={{ marginTop: 6, fontSize: 11.5 }}>
          {isPrimary
            ? 'Not available. Strategy simulations have not been run for the primary league yet.'
            : `Not simulated for this league's roster shape -- ${shape}. The strategies below are still ` +
              'selectable; only their measured costs are unknown here. The primary league\'s figures are ' +
              'not shown because they were measured on a different roster.'}
        </p>
        {!isPrimary ? (
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
            {['bpa_consensus', 'balanced', 'zero_rb', 'hero_rb', 'elite_te_early', 'qb_early'].map((key) => (
              <button
                key={key}
                aria-pressed={active === key}
                onClick={() => onSelect(key as StrategyKey)}
                title={strategyRuleText(key as StrategyKey, showSources)}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '6px 10px',
                  background: active === key ? 'var(--panel2)' : 'transparent',
                  border: `1px solid ${active === key ? 'var(--acc)' : 'var(--line)'}`,
                  color: 'var(--txt)',
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                <span>{key === 'bpa_consensus' ? 'Best player available (default)' : key.replace(/_/g, ' ')}</span>
                <span className="num" style={{ color: 'var(--dim2)' }}>
                  — —
                </span>
              </button>
            ))}
          </div>
        ) : null}
      </div>
    );
  }

  const rows = orderedStrategiesFor(s);

  return (
    <div style={{ border: '1px solid var(--line2)', padding: 10, marginBottom: 12 }}>
      <div style={{ fontSize: 10, letterSpacing: '.1em', color: 'var(--dim2)' }}>STRATEGY</div>
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {rows.map((row) => (
          <StrategyRow key={row.key} row={row} active={row.key === active} onSelect={() => onSelect(row.key as StrategyKey)} />
        ))}
      </div>
      <p className="notice" style={{ marginTop: 9, fontSize: 11 }}>
        <strong>What can and cannot be concluded here.</strong> {s.power_floor.plain_english}
      </p>
      <p className="notice" style={{ marginTop: 6, fontSize: 11 }}>
        <strong>Lineup assumption.</strong> {s.lineup_assumption}
      </p>
      <div className="num" style={{ marginTop: 6, fontSize: 9, color: 'var(--dim2)' }}>
        strategies.json · baseline {s.baseline} · seasons {s.seasons.map(integer).join(', ')} ·{' '}
        {integer(s.simulations_per_cell)} sims/cell
      </div>
    </div>
  );
}
