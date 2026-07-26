import type { BoardRow } from '../data/board';
import { Value } from './Value';
import { decimal, integer, signed } from '../lib/format';

/**
 * The player detail panel, ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html, lines 1040-1105): a
 * right-side drawer with a backdrop, opened by clicking a board row.
 *
 * Scoped narrowly, per the instruction that asked for this: "the detail panel with
 * the structural attribution breakdown" -- the header identity block and the "WHY
 * OUR RANK DIFFERS FROM THE MARKET" section, not the rest of the prototype's much
 * larger profile drawer. Specifically not ported, and why:
 *   - Headshot placeholder: no headshot data exists in any export.
 *   - The PROJECTION section, season stats table, weekly heat map, insights list,
 *     news: none of this app's exports carry that data (the prototype's own values
 *     there are sample data, not real). Porting the layout would mean building a
 *     section that always renders empty or invented.
 *   - Mark taken / watchlist / compare / ask-the-assistant action buttons: the
 *     first three assume draft-state tracking, which this read-only prep app does
 *     not have. "Ask the assistant" is replaced by the assistant dock picking up
 *     this player as context automatically while the panel is open (see App.tsx) --
 *     one fewer click to reach the same result.
 *   - The small proportional bar under FORMAT CORRECTION visualises where the
 *     correction sits against a midpoint. The prototype computes its position from
 *     a scale that isn't in any export; reproducing it would mean inventing that
 *     scale. The three numbers are shown without it.
 */

function nameOf(row: BoardRow): string {
  return row.name.kind === 'present' ? row.name.value : '';
}

export function PlayerDetail({ row, onClose }: { row: BoardRow; onClose: () => void }) {
  const consensus = row.consensusRank.kind === 'present' ? integer(row.consensusRank.value) : '—';
  const delta = row.deltaVsConsensus.kind === 'present' ? row.deltaVsConsensus.value : null;
  const deltaColor = delta === null ? 'var(--dim2)' : delta > 0 ? 'var(--up)' : delta < 0 ? 'var(--down)' : 'var(--dim2)';

  return (
    <>
      <div
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', zIndex: 80 }}
      />
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 520,
          zIndex: 90,
          background: 'var(--panel)',
          borderLeft: '1px solid var(--line2)',
          overflowY: 'auto',
          boxShadow: '-30px 0 60px rgba(0,0,0,.45)',
        }}
      >
        <div
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 3,
            background: 'var(--panel)',
            borderBottom: '1px solid var(--line)',
            padding: '14px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 9 }}>
              <span style={{ fontSize: 21, fontWeight: 700 }}>
                <Value cell={row.name} render={(v) => v} />
              </span>
              <span style={{ fontFamily: 'var(--font-num)', fontSize: 14, fontWeight: 600, color: 'var(--txt)' }}>
                <Value cell={row.position} render={(v) => v} />
              </span>
            </div>
            <div style={{ marginTop: 4, fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)' }}>
              <Value cell={row.team} render={(v) => v} /> · BYE <Value cell={row.byeWeek} render={integer} /> ·
              OUR RANK <Value cell={row.overallRank} render={integer} /> · TIER{' '}
              <Value cell={row.tierLabel} render={(v) => v.replace('T', '')} />
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid var(--line2)',
              color: 'var(--dim)',
              padding: '2px 8px',
              fontSize: 12,
            }}
          >
            esc
          </button>
        </div>

        <div style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
              WHY OUR RANK DIFFERS FROM THE MARKET
            </span>
            <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
          </div>

          <div style={{ marginTop: 10, fontSize: 14, lineHeight: 1.5, fontWeight: 600 }}>
            {delta === null
              ? `Consensus has ${nameOf(row)} at ${consensus}; no format correction is available.`
              : delta === 0
                ? `Consensus and our board agree on ${nameOf(row)} -- no format correction moved him.`
                : `${nameOf(row)} moved ${signed(delta)} slots against consensus, all of it format correction.`}
          </div>

          <div style={{ marginTop: 12, display: 'flex', alignItems: 'stretch', border: '1px solid var(--line)' }}>
            <div style={{ flex: 1, padding: '11px 13px', borderRight: '1px solid var(--line)' }}>
              <div style={{ fontFamily: 'var(--font-num)', fontSize: 9.5, letterSpacing: '.08em', color: 'var(--dim2)' }}>
                CONSENSUS
              </div>
              <div style={{ marginTop: 5, fontFamily: 'var(--font-num)', fontSize: 22, color: 'var(--dim)' }}>
                {consensus}
              </div>
            </div>
            <div
              style={{
                flex: 1.2,
                padding: '11px 13px',
                borderRight: '1px solid var(--line)',
                background: 'var(--panel2)',
              }}
            >
              <div style={{ fontFamily: 'var(--font-num)', fontSize: 9.5, letterSpacing: '.08em', color: 'var(--dim2)' }}>
                FORMAT CORRECTION
              </div>
              <div style={{ marginTop: 5, display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-num)', fontSize: 22, color: deltaColor }}>
                  {delta === null ? '—' : signed(delta)}
                </span>
                <span style={{ fontSize: 11, color: 'var(--dim2)' }}>slots</span>
              </div>
            </div>
            <div style={{ flex: 1, padding: '11px 13px' }}>
              <div style={{ fontFamily: 'var(--font-num)', fontSize: 9.5, letterSpacing: '.08em', color: 'var(--acc)' }}>
                OUR RANK
              </div>
              <div style={{ marginTop: 5, fontFamily: 'var(--font-num)', fontSize: 22, fontWeight: 600, color: 'var(--acc)' }}>
                <Value cell={row.overallRank} render={integer} />
              </div>
            </div>
          </div>

          <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 1 }}>
            {row.replacementLevelsComponent.kind === 'present' ? (
              <CorrPart
                label="Replacement levels"
                value={signed(row.replacementLevelsComponent.value)}
                note="Movement from this league's replacement levels versus the published 12-team convention."
                field={row.replacementLevelsComponent.path}
              />
            ) : null}
            {row.scoringAndVbdComponent.kind === 'present' ? (
              <CorrPart
                label="Scoring and VBD method"
                value={signed(row.scoringAndVbdComponent.value)}
                note="The remainder: this league's scoring rules and the VBD method itself."
                field={row.scoringAndVbdComponent.path}
              />
            ) : null}
          </div>
          <p className="notice" style={{ marginTop: 9 }}>
            {row.evaluativeNote}
          </p>

          {row.projectedPoints.kind === 'present' ? (
            <>
              <div style={{ marginTop: 18, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span
                  style={{ fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}
                >
                  PROJECTION
                </span>
                <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
              </div>
              <div style={{ marginTop: 10, display: 'flex', alignItems: 'baseline', gap: 10 }}>
                <span style={{ fontFamily: 'var(--font-num)', fontSize: 26, fontWeight: 600 }}>
                  {decimal(row.projectedPoints.value)}
                </span>
                {row.interval.kind === 'present' ? (
                  <span style={{ fontFamily: 'var(--font-num)', fontSize: 13, color: 'var(--dim2)' }}>
                    {decimal(row.interval.value.low)} – {decimal(row.interval.value.high)}
                  </span>
                ) : null}
              </div>
            </>
          ) : (
            <p className="notice" style={{ marginTop: 18 }}>
              {row.projectedPoints.reason}
            </p>
          )}
        </div>
      </div>
    </>
  );
}

function CorrPart({ label, value, note, field }: { label: string; value: string; note: string; field: string }) {
  return (
    <div style={{ padding: '9px 12px', background: 'var(--panel2)' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <span style={{ flex: 1, fontSize: 12.5 }}>{label}</span>
        <span style={{ fontFamily: 'var(--font-num)', fontSize: 13, color: 'var(--te)' }}>{value}</span>
      </div>
      <div style={{ marginTop: 4, fontSize: 12, lineHeight: 1.55, color: 'var(--dim)' }}>{note}</div>
      <div style={{ marginTop: 5, fontFamily: 'var(--font-num)', fontSize: 9, color: 'var(--dim2)' }}>{field}</div>
    </div>
  );
}
