import { useEffect, useMemo, useState } from 'react';
import type { BoardRow } from '../data/board';
import { POSITIONS } from '../data/board';
import {
  buildAvailabilityMeta,
  playerAvailabilityAtPick,
  simulatedPlayerCount,
  tierAvailabilityAtPick,
  tiersForPosition,
  tierPositions,
  type SigmaCell,
} from '../data/availability';
import { dotsFilled, freqText } from '../data/liveAvailability';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { Value } from '../components/Value';
import { percent } from '../lib/format';

/**
 * Availability Explorer, ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html, lines 517-584): a pick
 * selector, a position-grouped list of players with an availability bar, and a
 * right-hand sidebar of three info boxes (tier spotlight, model inputs,
 * uncertainty).
 *
 * Two deliberate departures from the source markup, both because the prototype's
 * version described data that either never existed in this backend or has since
 * been retired:
 *
 *   - The prototype reads a single `availability.noise_band` scalar (line 579:
 *     "The width is availability.noise_band, measured by refitting the model 200
 *     times..."). The backend confirmed directly that no such field exists in any
 *     version of this project -- the real shape is a three-setting sigma sweep
 *     (5/10/20, `metadata.sigma_plain_english`). This screen reads that sweep and
 *     a sigma selector, never a fabricated band width.
 *   - The prototype gates the whole screen behind `simsInvalid` (settings differ
 *     from the real league -> everything greyed out). There is no settings editor
 *     in this app to ever put league config out of sync with the simulation, so
 *     that gate has nothing to trigger it -- same reasoning as TopBar's dropped
 *     "MODIFIED — COMPARISON" state.
 *
 * `metadata.marginals_note` is the single most important caveat this screen
 * carries: by_player/by_tier are unconditional marginals (averaged over every
 * possible draft), not conditioned on picks actually made. It is surfaced as a
 * standing banner, not a tooltip, the same treatment Board.tsx gives curve_caveat.
 *
 * FR-066 ("When slot selection happens on the availability, it doesn't change the
 * picks shown"): `availability.json:by_player`/`by_tier` are keyed to ONE slot's
 * pick numbers -- whichever slot the Python Monte Carlo simulation ran against
 * (`metadata.user_draft_slot`). Before this fix, the "YOUR PICKS" row here read
 * `meta.userPicks` (that export field, straight) -- so overriding the slot
 * elsewhere in the app (FR-034, `applyUserSlotOverride`) silently left this one
 * screen showing the *old* slot's pick numbers and real-looking data for them,
 * with nothing on screen saying so. That is exactly the "confidently wrong
 * number" failure this project treats as worst.
 *
 * The fix goes through the SAME seam every other overridden screen uses --
 * `league.pickSequence` (already recomputed by `applyUserSlotOverride` for
 * whatever slot is active) drives the pick selector here now, not
 * `meta.userPicks`. No second override path was added.
 *
 * This is deliberately NOT a browser-side re-simulation, even though that was
 * the founder-approved direction ("is the browser side fix faster... yeah we
 * probably should implement that"). Investigated and shelved this session --
 * see the FR-066 file's Resolution section for the full writeup, but the short
 * version: `simulate_availability`'s opponent AND user-strategy ranks
 * (`client_simulation_parameters.ranking_sources: [{name: "fantasypros_ecr"}]`)
 * come from a DIFFERENT, older ranking source than `board.json:consensus_rank`
 * (which is `fantasypros_csv_2026draft`, per `board.json:consensus_source_note`
 * -- the source that superseded fantasypros_ecr at thread 053/067). Measured
 * directly: 73 of the top 80 players are in a different order between the two
 * sources. The frontend has no honest access to the ranking the simulation
 * actually runs on, so a client-side re-simulation built on `board.json`'s
 * consensus_rank would silently produce a DIFFERENT, wrong opponent model --
 * not an approximation of the real one, a categorically different one. That is
 * the exact failure mode this fix exists to prevent, so it was not built.
 *
 * Instead: once the pick selector shows the overridden slot's real pick
 * numbers, `playerAvailabilityAtPick`/`tierAvailabilityAtPick` ALREADY return
 * an honest `absent` Cell for a pick number outside `by_player`'s keys (see
 * availability.ts) -- no new absence-handling code was needed there. This
 * screen adds one thing: a standing banner, active only while a slot override
 * is in effect, naming which slot the numbers below were actually simulated
 * for and that they have not been recomputed for the active selection. That
 * is the interim fix the FR itself proposed as correct-today-and-cheap while
 * the real recompute is blocked on a backend export change (see the FR file).
 */

const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
};

type SigmaKey = 'sigma5' | 'sigma10' | 'sigma20';
const SIGMA_KEYS: Array<{ key: SigmaKey; value: number }> = [
  { key: 'sigma5', value: 5 },
  { key: 'sigma10', value: 10 },
  { key: 'sigma20', value: 20 },
];

export function Availability({ data, rows, league }: { data: Dataset; rows: BoardRow[]; league: LeagueConfig }) {
  const meta = useMemo(() => buildAvailabilityMeta(data), [data]);

  // FR-066: the pick selector reads league.pickSequence (already recomputed by
  // applyUserSlotOverride for whatever slot is active), never meta.userPicks
  // directly -- meta.userPicks is availability.json:metadata.user_picks, which
  // is fixed to whichever slot the Python simulation ran against and does not
  // move when the user overrides the slot elsewhere in the app. Falls back to
  // meta.userPicks only if pickSequence itself is absent (no teams Cell to
  // build a sequence from -- applyUserSlotOverride's own no-op condition).
  const overridden = league.userSlotOverridden;
  const sourcedSlot = league.userSlotSourced.kind === 'present' ? league.userSlotSourced.value : null;
  const activeSlot = league.userSlot.kind === 'present' ? league.userSlot.value : null;
  const effectivePicks = league.pickSequence.kind === 'present' ? league.pickSequence.value : meta.userPicks;

  const [pick, setPick] = useState<number>(effectivePicks[0] ?? 0);
  // Atomic swap, not a partial one (Principle #3): when the active slot changes,
  // every affected piece of state on this screen -- the pick buttons AND the
  // selected pick they drive -- moves together in one render, driven by the
  // same `league` prop every other overridden screen reacts to. There is no
  // async recompute here to tear across renders.
  useEffect(() => {
    setPick(effectivePicks[0] ?? 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectivePicks.join(',')]);

  const [sigma, setSigma] = useState<SigmaKey>('sigma10');

  const positions = useMemo(() => tierPositions(data), [data]);
  const [spotlightPos, setSpotlightPos] = useState<string>(() => (positions.includes('TE') ? 'TE' : positions[0] ?? ''));
  const tiers = useMemo(() => tiersForPosition(data, spotlightPos), [data, spotlightPos]);
  const [spotlightTier, setSpotlightTier] = useState<string>(() => (tiers.includes('T1') ? 'T1' : tiers[0] ?? ''));
  const effectiveTier = tiers.includes(spotlightTier) ? spotlightTier : (tiers[0] ?? '');

  const simulatedCount = simulatedPlayerCount(data);

  const spotlight = effectiveTier
    ? tierAvailabilityAtPick(data, spotlightPos, effectiveTier, pick)
    : null;

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          flex: 'none',
          padding: '18px 23px',
          borderBottom: '1px solid var(--line)',
          background: 'var(--panel)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Availability Explorer</h2>
          <div style={{ fontSize: 13, color: 'var(--dim2)' }}>Who is still on the board when your turn comes</div>
        </div>

        <div
          role="group"
          aria-label="Your picks"
          style={{ marginTop: 13, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}
        >
          <span
            style={{
              fontFamily: 'var(--font-num)',
              fontSize: 12,
              color: 'var(--dim2)',
              marginRight: 4,
            }}
          >
            YOUR PICKS
          </span>
          {effectivePicks.map((p) => {
            const active = p === pick;
            return (
              <button
                key={p}
                aria-pressed={active}
                onClick={() => setPick(p)}
                style={{
                  padding: '6px 18px',
                  background: active ? 'var(--acc)' : 'transparent',
                  border: `1px solid ${active ? 'var(--acc)' : 'var(--line2)'}`,
                  color: active ? '#0a0d12' : 'var(--dim)',
                  fontFamily: 'var(--font-num)',
                  fontSize: 14,
                  fontWeight: 600,
                }}
              >
                {p}
              </button>
            );
          })}
        </div>

        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontFamily: 'var(--font-num)', fontSize: 12, color: 'var(--dim2)', marginRight: 4 }}>
            SIGMA
          </span>
          {SIGMA_KEYS.map((s) => {
            const active = s.key === sigma;
            return (
              <button
                key={s.key}
                aria-pressed={active}
                onClick={() => setSigma(s.key)}
                style={{
                  padding: '4px 12px',
                  background: active ? 'var(--panel2)' : 'transparent',
                  border: `1px solid ${active ? 'var(--line2)' : 'var(--line)'}`,
                  color: active ? 'var(--txt)' : 'var(--dim2)',
                  fontFamily: 'var(--font-num)',
                  fontSize: 12,
                }}
              >
                {s.value}
              </button>
            );
          })}
        </div>
      </div>

      <div
        style={{
          flex: 'none',
          margin: '16px 18px 0',
          padding: '14px 18px',
          border: '1px dashed var(--down)',
          color: 'var(--down)',
          fontSize: 13.5,
          lineHeight: 1.55,
        }}
      >
        {meta.marginalsNote}
      </div>

      {overridden ? (
        <div
          style={{
            flex: 'none',
            margin: '10px 18px 0',
            padding: '14px 18px',
            border: '1px solid var(--acc)',
            background: 'var(--panel2)',
            color: 'var(--txt)',
            fontSize: 13.5,
            lineHeight: 1.55,
          }}
        >
          <strong>
            Showing slot {sourcedSlot ?? '?'}&apos;s simulation, not slot {activeSlot ?? '?'}&apos;s.
          </strong>{' '}
          You set draft slot {activeSlot ?? '?'} in the top bar (FR-034). availability.json was
          generated for slot {sourcedSlot ?? '?'} only and has not been recomputed for your
          selection -- every figure below reads &quot;no availability figure recorded for pick N&quot;
          for a pick number that belongs to slot {activeSlot ?? '?'} rather than a real probability
          (FR-066). Clear the slot override, or wait for a browser-side recompute -- see the FR-066
          file's Resolution section for why that isn't built yet.
        </div>
      ) : null}

      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        <div style={{ padding: '20px 23px', display: 'grid', gridTemplateColumns: 'minmax(0,1fr) 330px', gap: 18 }}>
          <div>
            <div style={{ marginBottom: 10, fontSize: 12.5, color: 'var(--dim2)' }}>
              {simulatedCount} players simulated · {meta.sigmaPlainEnglish}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${POSITIONS.length}, minmax(0,1fr))`, gap: 12 }}>
              {POSITIONS.map((pos) => (
                <PositionColumn key={pos} position={pos} data={data} rows={rows} pick={pick} sigma={sigma} />
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ padding: 20, border: '1px solid var(--acc)', background: 'var(--panel2)' }}>
              <div
                style={{
                  fontFamily: 'var(--font-num)',
                  fontSize: 12,
                  letterSpacing: '.12em',
                  color: 'var(--dim2)',
                }}
              >
                TIER AVAILABILITY
              </div>
              <div style={{ marginTop: 10, display: 'flex', gap: 6 }}>
                {positions.map((p) => (
                  <button
                    key={p}
                    aria-pressed={p === spotlightPos}
                    onClick={() => setSpotlightPos(p)}
                    style={{
                      padding: '3px 9px',
                      background: p === spotlightPos ? 'var(--panel)' : 'transparent',
                      border: `1px solid ${p === spotlightPos ? 'var(--line2)' : 'var(--line)'}`,
                      color: p === spotlightPos ? (POSITION_COLOR[p] ?? 'var(--txt)') : 'var(--dim2)',
                      fontFamily: 'var(--font-num)',
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    {p}
                  </button>
                ))}
                {tiers.map((t) => (
                  <button
                    key={t}
                    aria-pressed={t === effectiveTier}
                    onClick={() => setSpotlightTier(t)}
                    style={{
                      padding: '3px 9px',
                      background: t === effectiveTier ? 'var(--panel)' : 'transparent',
                      border: `1px solid ${t === effectiveTier ? 'var(--line2)' : 'var(--line)'}`,
                      color: t === effectiveTier ? 'var(--txt)' : 'var(--dim2)',
                      fontFamily: 'var(--font-num)',
                      fontSize: 11,
                      fontWeight: 600,
                    }}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <div style={{ marginTop: 12, fontSize: 14, color: 'var(--dim)' }}>
                {spotlightPos} {effectiveTier} available at pick {pick}
              </div>
              {spotlight ? (
                <div
                  style={{
                    marginTop: 5,
                    fontFamily: 'var(--font-num)',
                    fontSize: 30,
                    fontWeight: 600,
                    color: 'var(--acc)',
                    lineHeight: 1.1,
                  }}
                >
                  <SigmaSpread cell={spotlight} />
                </div>
              ) : (
                <div style={{ marginTop: 5, fontSize: 13, color: 'var(--dim2)' }}>No data for this combination.</div>
              )}
              {spotlight && spotlight[sigma].kind === 'present' ? (
                <div style={{ marginTop: 8 }}>
                  <SpotlightDots value={(spotlight[sigma] as { kind: 'present'; value: number }).value} />
                </div>
              ) : null}
              <div style={{ marginTop: 6, fontFamily: 'var(--font-num)', fontSize: 12, color: 'var(--dim2)' }}>
                sigma {sigma.replace('sigma', '')} shown large · range across all three settings above
              </div>
              <div style={{ marginTop: 12, fontSize: 13.5, lineHeight: 1.55, color: 'var(--dim)' }}>
                The range is the number. Read the spread across sigma 5/10/20, not one setting in isolation.
              </div>
            </div>

            <div style={{ padding: 18, border: '1px solid var(--line)', background: 'var(--panel)' }}>
              <div
                style={{
                  fontFamily: 'var(--font-num)',
                  fontSize: 12,
                  letterSpacing: '.12em',
                  color: 'var(--dim2)',
                }}
              >
                WHAT THE MODEL USES
              </div>
              <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 9, fontSize: 13, lineHeight: 1.6, color: 'var(--dim)' }}>
                <div>{meta.algorithmNote}</div>
                <div>{meta.roomNoiseNote}</div>
              </div>
            </div>

            <div style={{ padding: 18, borderLeft: '2px solid var(--down)', background: 'var(--panel2)' }}>
              <div
                style={{
                  fontFamily: 'var(--font-num)',
                  fontSize: 12,
                  letterSpacing: '.12em',
                  color: 'var(--down)',
                }}
              >
                UNCERTAINTY
              </div>
              <div style={{ marginTop: 10, fontSize: 13.5, lineHeight: 1.6, color: 'var(--dim)' }}>
                {meta.sigmaPlainEnglish}
              </div>
              <div style={{ marginTop: 10, fontSize: 13.5, lineHeight: 1.6, color: 'var(--dim)' }}>
                {meta.reliabilityNote}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/** §5.3's dot array: a bare percentage reads as more decisive than this model
 *  supports, so the headline spotlight number always carries "N in 10 drafts"
 *  alongside it, not instead of it. */
function SpotlightDots({ value }: { value: number }) {
  const filled = dotsFilled(value);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ display: 'flex', gap: 3 }}>
        {Array.from({ length: 10 }, (_, i) => (
          <span
            key={i}
            style={{ width: 7, height: 7, borderRadius: '50%', background: i < filled ? 'var(--acc)' : 'var(--line2)' }}
          />
        ))}
      </div>
      <span style={{ fontSize: 11, color: 'var(--dim2)' }}>{freqText(value)}</span>
    </div>
  );
}

/** Three real sigma readings shown as a range (low–high across 5/10/20), never
 *  collapsed to a midpoint plus an invented margin. */
function SigmaSpread({ cell }: { cell: SigmaCell }) {
  if (cell.sigma5.kind === 'absent' && cell.sigma10.kind === 'absent' && cell.sigma20.kind === 'absent') {
    return <Value cell={cell.sigma10} render={percent} />;
  }
  const vals = [cell.sigma5, cell.sigma10, cell.sigma20].filter((c) => c.kind === 'present') as Array<{
    kind: 'present';
    value: number;
  }>;
  if (vals.length === 0) return <span className="val-absent">—</span>;
  const lo = Math.min(...vals.map((v) => v.value));
  const hi = Math.max(...vals.map((v) => v.value));
  return (
    <span title="Range across sigma 5, 10 and 20">
      {percent(lo)}–{percent(hi)}
    </span>
  );
}

function PositionColumn({
  position,
  data,
  rows,
  pick,
  sigma,
}: {
  position: string;
  data: Dataset;
  rows: BoardRow[];
  pick: number;
  sigma: SigmaKey;
}) {
  const players = useMemo(() => {
    return rows
      .filter((r) => r.raw.position === position && r.name.kind === 'present')
      .map((r) => ({ row: r, name: (r.name as { kind: 'present'; value: string }).value }))
      .filter(({ name }) => data.availability.by_player[name] !== undefined)
      .sort((a, b) => a.row.positionalRank - b.row.positionalRank);
  }, [rows, position, data]);

  return (
    <div>
      <div
        style={{
          fontFamily: 'var(--font-num)',
          fontSize: 12,
          fontWeight: 600,
          color: POSITION_COLOR[position] ?? 'var(--txt)',
          paddingBottom: 5,
          borderBottom: '1px solid var(--line)',
        }}
      >
        {position}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {players.length === 0 ? (
          <div style={{ padding: '10px 0', fontSize: 12.5, color: 'var(--dim2)' }}>Nobody at this position simulated.</div>
        ) : (
          players.map(({ row, name }) => {
            const cell = playerAvailabilityAtPick(data, name, pick);
            const c = cell[sigma];
            const pct = c.kind === 'present' ? c.value : null;
            const barColor = pct === null ? 'var(--line2)' : pct >= 0.5 ? 'var(--up)' : pct >= 0.15 ? 'var(--dim2)' : 'var(--down)';
            return (
              <div key={row.id} style={{ padding: '6px 0', borderBottom: '1px solid var(--line)' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                  <span style={{ flex: 1, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {name}
                  </span>
                  <span style={{ fontFamily: 'var(--font-num)', fontSize: 12, color: barColor }}>
                    <Value cell={c} render={percent} />
                  </span>
                </div>
                <div style={{ marginTop: 4, height: 4, background: 'var(--line)' }}>
                  <div
                    style={{
                      height: 4,
                      width: pct === null ? '0%' : `${Math.round(pct * 100)}%`,
                      background: barColor,
                    }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
