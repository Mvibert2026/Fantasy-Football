import { useMemo } from 'react';
import type { BoardRow } from '../data/board';
import type { DraftPickRecord } from '../data/draft';
import { currentOverallPick, nextPickForSlot, pickNumbersForSlot } from '../data/draft';
import { isPresent } from '../data/cell';
import { computeLiveAvailability, dotsFilled, freqText, type LiveAvailabilityResult } from '../data/liveAvailability';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { initialsOf, teamColorOf } from '../data/teamColors';
import { verdictLine } from '../data/verdict';
import { Value } from './Value';
import { decimal, integer, percent, signed } from '../lib/format';

/**
 * Player side sheet, rebuilt to FRONTEND-SPEC.md §7.2's fixed 10-section order,
 * superseding the narrower panel this project shipped earlier (identity + why-
 * rank-differs only). Geometry per §3.3: fixed right sheet, 440px (min 420,
 * max-width 96vw), z-index 90, a TRANSPARENT click-catcher at z-index 80 -- no
 * dark scrim, so the board and the pick clock stay visible while it's open.
 *
 * Sections 6-9 (archetype, weekly finishes, three-season table, bullet
 * takeaways) collapse into one line per §8's rule for multiple empty sections on
 * one player ("one collapsed line naming everything missing at once, never three
 * stacked empty headers"): none of the four has a real field anywhere in this
 * app's exports, for any player, ever -- not a per-player gap, a permanent one.
 * Headshot: same story, §6.9's own admission -- no player in any real export has
 * an ESPN id, so every card renders initials on the team colour, always.
 *
 * `picks` is the live draft's pick log when opened from Draft mode, or `[]` in
 * Prep mode -- either way it feeds the same computeLiveAvailability call, so
 * Prep mode honestly shows signal:'none' (no draft in progress to log picks
 * against) rather than a special-cased Prep-only availability path.
 *
 * `stale` is always false: this app has no settings-editor and so no
 * settings-hash system that could ever mark a league's simulation stale (§5.1
 * needs live, editable league settings to compare hashes against; none exist
 * here). Threaded as a real prop rather than deleted, so wiring it up later (if
 * a settings editor is ever built) is additive, not a rewrite.
 */

export function PlayerDetail({
  row,
  rows,
  data,
  league,
  picks,
  watchlist,
  onToggleWatch,
  queue,
  onToggleQueue,
  onMarkTaken,
  stale = false,
  onClose,
}: {
  row: BoardRow;
  rows: BoardRow[];
  data: Dataset;
  league: LeagueConfig;
  /** [] in Prep mode; the real draft log when opened from Draft mode. */
  picks: DraftPickRecord[];
  watchlist: string[];
  onToggleWatch: (name: string) => void;
  /** Undefined outside Draft mode -- the queue is draft-scoped (§6.10). */
  queue?: number[];
  onToggleQueue?: (id: number) => void;
  onMarkTaken?: (id: number | null, name: string) => void;
  stale?: boolean;
  onClose: () => void;
}) {
  const name = row.name.kind === 'present' ? row.name.value : '';
  const teams = league.teams.kind === 'present' ? league.teams.value : 0;
  const rounds = league.rounds.kind === 'present' ? league.rounds.value : 0;
  const userSlot = league.userSlot.kind === 'present' ? league.userSlot.value : 0;

  const rowsById = useMemo(() => new Map(rows.map((r) => [r.id, r])), [rows]);

  const upcomingUserPicks = useMemo(() => {
    if (teams === 0 || rounds === 0 || userSlot === 0) return [];
    const cur = currentOverallPick(picks);
    return pickNumbersForSlot(teams, userSlot, rounds)
      .filter((p) => p >= cur)
      .slice(0, 5);
  }, [teams, rounds, userSlot, picks]);

  const nextUserPick = teams > 0 ? nextPickForSlot(picks, teams, userSlot, rounds) : null;

  const availAtNext: LiveAvailabilityResult | null =
    nextUserPick === null
      ? null
      : computeLiveAvailability({ data, league, row, targetPick: nextUserPick, picks, rowsById });

  const perPickStrip = upcomingUserPicks.map((pick) => ({
    pick,
    result: computeLiveAvailability({ data, league, row, targetPick: pick, picks, rowsById }),
  }));

  const inWatchlist = watchlist.includes(name);
  const inQueue = queue?.includes(row.id) ?? false;

  const consensus = row.consensusRank.kind === 'present' ? integer(row.consensusRank.value) : '—';
  const delta = row.deltaVsConsensus.kind === 'present' ? row.deltaVsConsensus.value : null;
  const deltaColor = delta === null ? 'var(--dim2)' : delta > 0 ? 'var(--up)' : delta < 0 ? 'var(--down)' : 'var(--dim2)';

  return (
    <>
      {/* Transparent click-catcher, not a scrim (§3.3) -- the board and the pick
          clock must stay visible while this panel is open. */}
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, zIndex: 80, background: 'transparent' }} />
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 440,
          minWidth: 420,
          maxWidth: '96vw',
          zIndex: 90,
          background: 'var(--panel)',
          borderLeft: '1px solid var(--line2)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: 'var(--sh)',
        }}
      >
        <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
          {/* 1. Identity strip -- sticky at the top of the sheet. */}
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
            <div
              style={{
                flex: 'none',
                width: 40,
                height: 40,
                borderRadius: 'var(--r-c)',
                background: teamColorOf(row.raw.team),
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: 14,
              }}
              title="No headshot: no player in this board has a real ESPN id yet"
            >
              {initialsOf(name)}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 9 }}>
                <span style={{ fontSize: 21, fontWeight: 700 }}>
                  <Value cell={row.name} render={(v) => v} />
                </span>
                <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: '.045em', color: 'var(--txt)' }}>
                  <Value cell={row.positionalLabel} render={(v) => v} />
                </span>
              </div>
              <div style={{ marginTop: 4, fontSize: 11, letterSpacing: '.045em', color: 'var(--dim2)' }}>
                <Value cell={row.team} render={(v) => v} /> · BYE{' '}
                <span className="num">
                  <Value cell={row.byeWeek} render={integer} />
                </span>{' '}
                · OUR RANK{' '}
                <span className="num">
                  <Value cell={row.overallRank} render={integer} />
                </span>{' '}
                · TIER <Value cell={row.tierLabel} render={(v) => v.replace('T', '')} />
              </div>
            </div>
            <button
              onClick={onClose}
              style={{ background: 'transparent', border: '1px solid var(--line2)', color: 'var(--dim)', padding: '2px 8px', fontSize: 12 }}
            >
              esc
            </button>
          </div>

          <div style={{ padding: 16 }}>
            {/* 2. Verdict line -- generated, never written; §5.6. */}
            <div style={{ borderLeft: '2px solid var(--acc)', paddingLeft: 10, fontSize: 14.5, lineHeight: 1.5 }}>
              {verdictLine(row, rows, availAtNext, nextUserPick, stale)}
            </div>
            <div style={{ marginTop: 4, fontSize: 9, letterSpacing: '.02em', color: 'var(--dim2)' }}>
              board.json:tier_label · availability.json:by_player · board.json:vbd
            </div>

            {/* 3. Projection -- point estimate, honest range as a bar, VBD, gloss. */}
            <SectionHeader label="PROJECTION" />
            {row.projectedPoints.kind === 'present' ? (
              <>
                <div style={{ marginTop: 10, display: 'flex', alignItems: 'baseline', gap: 10 }}>
                  <span className="num" style={{ fontSize: 26, fontWeight: 600 }}>
                    {decimal(row.projectedPoints.value)}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--dim)' }}>projected pts</span>
                  <span style={{ flex: 1 }} />
                  <span className="num" style={{ fontSize: 13, color: 'var(--dim2)' }}>
                    VBD <Value cell={row.vbd} render={decimal} />
                  </span>
                </div>
                {row.interval.kind === 'present' ? (
                  <RangeBar low={row.interval.value.low} high={row.interval.value.high} mid={row.projectedPoints.value} />
                ) : null}
                <p className="notice" style={{ marginTop: 9, fontSize: 12 }}>
                  {data.board.curve_caveat}
                </p>
              </>
            ) : (
              <p className="notice" style={{ marginTop: 10 }}>
                {row.projectedPoints.reason}
              </p>
            )}

            {/* 4. Availability at your picks. */}
            <SectionHeader label="AVAILABILITY AT YOUR PICKS" />
            {nextUserPick === null ? (
              <p className="notice" style={{ marginTop: 10 }}>
                No further picks for this team in this league's format.
              </p>
            ) : (
              <AvailabilitySection avail={availAtNext!} targetPick={nextUserPick} />
            )}
            {perPickStrip.length > 0 ? (
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {perPickStrip.map(({ pick, result }) => (
                  <div key={pick} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                    <span className="num" style={{ width: 34, color: 'var(--dim2)' }}>
                      #{pick}
                    </span>
                    <span style={{ flex: 1, height: 6, background: 'var(--line)', position: 'relative' }}>
                      <span
                        style={{
                          position: 'absolute',
                          inset: 0,
                          width:
                            result.live !== null
                              ? `${Math.round(result.live * 100)}%`
                              : result.baseline.kind === 'present'
                                ? `${Math.round(result.baseline.value * 100)}%`
                                : '0%',
                          background: 'var(--acc)',
                        }}
                      />
                    </span>
                    <span className="num" style={{ width: 40, textAlign: 'right', color: 'var(--dim)' }}>
                      {result.live !== null
                        ? percent(result.live)
                        : result.baseline.kind === 'present'
                          ? percent(result.baseline.value)
                          : '—'}
                    </span>
                  </div>
                ))}
              </div>
            ) : null}

            {/* 5. Why our rank differs from the market. */}
            <SectionHeader label="WHY OUR RANK DIFFERS FROM THE MARKET" />
            <div style={{ marginTop: 10, fontSize: 14, lineHeight: 1.5, fontWeight: 600 }}>
              {delta === null
                ? `Consensus has ${name} at ${consensus}; no format correction is available.`
                : delta === 0
                  ? `Consensus and our board agree on ${name} -- no format correction moved him.`
                  : `${name} moved ${signed(delta)} slots against consensus, all of it format correction.`}
            </div>
            <div style={{ marginTop: 12, display: 'flex', alignItems: 'stretch', border: '1px solid var(--line)' }}>
              <div style={{ flex: 1, padding: '11px 13px', borderRight: '1px solid var(--line)' }}>
                <div style={{ fontSize: 9.5, letterSpacing: '.08em', color: 'var(--dim2)' }}>CONSENSUS</div>
                <div className="num" style={{ marginTop: 5, fontSize: 22, color: 'var(--dim)' }}>
                  {consensus}
                </div>
              </div>
              <div style={{ flex: 1.2, padding: '11px 13px', borderRight: '1px solid var(--line)', background: 'var(--panel2)' }}>
                <div style={{ fontSize: 9.5, letterSpacing: '.08em', color: 'var(--dim2)' }}>FORMAT CORRECTION</div>
                <div style={{ marginTop: 5, display: 'flex', alignItems: 'baseline', gap: 8 }}>
                  <span className="num" style={{ fontSize: 22, color: deltaColor }}>
                    {delta === null ? '—' : signed(delta)}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--dim2)' }}>slots</span>
                </div>
              </div>
              <div style={{ flex: 1, padding: '11px 13px' }}>
                <div style={{ fontSize: 9.5, letterSpacing: '.08em', color: 'var(--acc)' }}>OUR RANK</div>
                <div className="num" style={{ marginTop: 5, fontSize: 22, fontWeight: 600, color: 'var(--acc)' }}>
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

            {/* 6-9. Archetype, weekly finishes, three-season table, bullet
                takeaways -- collapsed to one line per §8's multi-empty-section
                rule. None of the four has ever had a real field in any export. */}
            <p className="notice" style={{ marginTop: 18, fontSize: 12 }}>
              Not computed: archetype, weekly finishes, season-by-season stats, and takeaways.
              None of the four has a backend field in this build.
            </p>
          </div>
        </div>

        {/* 10. Sticky action bar. */}
        <div
          style={{
            flex: 'none',
            position: 'sticky',
            bottom: 0,
            display: 'flex',
            gap: 8,
            padding: '10px 16px',
            borderTop: '1px solid var(--line)',
            background: 'var(--panel)',
            boxShadow: '0 -8px 20px rgba(0,0,0,.2)',
          }}
        >
          {onMarkTaken ? (
            <button
              onClick={() => onMarkTaken(row.id, name)}
              style={{ padding: '8px 14px', background: 'var(--acc)', border: 0, color: '#08120c', fontWeight: 700, fontSize: 12.5 }}
            >
              Mark taken
            </button>
          ) : null}
          {onToggleQueue ? (
            <button
              aria-pressed={inQueue}
              onClick={() => onToggleQueue(row.id)}
              style={{
                padding: '8px 12px',
                background: inQueue ? 'var(--panel2)' : 'transparent',
                border: `1px solid ${inQueue ? 'var(--line2)' : 'var(--line)'}`,
                color: 'var(--txt)',
                fontSize: 12.5,
              }}
            >
              {inQueue ? 'Queued' : 'Add to queue'}
            </button>
          ) : null}
          <button
            aria-pressed={inWatchlist}
            onClick={() => onToggleWatch(name)}
            style={{
              padding: '8px 12px',
              background: inWatchlist ? 'var(--panel2)' : 'transparent',
              border: `1px solid ${inWatchlist ? 'var(--down)' : 'var(--line)'}`,
              color: inWatchlist ? 'var(--down)' : 'var(--txt)',
              fontSize: 12.5,
            }}
          >
            {inWatchlist ? '★ Watching' : '☆ Watchlist'}
          </button>
          <button aria-disabled="true" style={{ padding: '8px 12px', background: 'transparent', border: '1px solid var(--line)', color: 'var(--dim2)', fontSize: 12.5 }}>
            Compare
          </button>
          <button aria-disabled="true" style={{ padding: '8px 12px', background: 'transparent', border: '1px solid var(--line)', color: 'var(--dim2)', fontSize: 12.5 }}>
            Ask
          </button>
        </div>
      </div>
    </>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div style={{ marginTop: 18, display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={{ fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>{label}</span>
      <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
    </div>
  );
}

/** Honest range bar, mid tick at the point estimate -- CI weight sits below the
 *  point estimate, never above (§7.2 item 3). */
function RangeBar({ low, high, mid }: { low: number; high: number; mid: number }) {
  const span = Math.max(1, high - low);
  const midPct = Math.min(100, Math.max(0, ((mid - low) / span) * 100));
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ height: 4, background: 'var(--line)', position: 'relative' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'var(--line2)' }} />
        <div style={{ position: 'absolute', top: -3, width: 2, height: 10, left: `${midPct}%`, background: 'var(--acc)' }} />
      </div>
      <div className="num" style={{ marginTop: 4, fontSize: 11, color: 'var(--dim2)' }}>
        {decimal(low)} – {decimal(high)}
      </div>
    </div>
  );
}

/** Baseline -> live pair, dots, frequency, band, and need/run shown separately --
 *  never combined into one delta (§5.2's explicit display contract). */
function AvailabilitySection({ avail, targetPick }: { avail: LiveAvailabilityResult; targetPick: number }) {
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 14 }}>
        <div>
          <div style={{ fontSize: 10, letterSpacing: '.08em', color: 'var(--dim2)' }}>BASELINE</div>
          <div className="num" style={{ marginTop: 3, fontSize: 20, fontWeight: 600 }}>
            <Value cell={avail.baseline} render={percent} />
          </div>
        </div>
        <div>
          <div style={{ fontSize: 10, letterSpacing: '.08em', color: 'var(--dim2)' }}>LIVE</div>
          <div className="num" style={{ marginTop: 3, fontSize: 20, fontWeight: 600, color: avail.live !== null ? 'var(--acc)' : 'var(--dim2)' }}>
            {avail.live !== null ? percent(avail.live) : 'not yet'}
          </div>
        </div>
        {avail.signal === 'thin' ? (
          <span style={{ fontSize: 10, letterSpacing: '.08em', color: 'var(--down)', border: '1px solid var(--down)', padding: '1px 6px' }}>
            THIN
          </span>
        ) : null}
      </div>

      {avail.live !== null ? (
        <div style={{ marginTop: 6, fontSize: 12, color: 'var(--dim)' }}>
          {freqText(avail.live)}
          {avail.band ? (
            <span className="num" style={{ color: 'var(--dim2)' }}>
              {' '}
              · range {percent(avail.band.lo)}–{percent(avail.band.hi)}
            </span>
          ) : null}
        </div>
      ) : (
        <div style={{ marginTop: 6, fontSize: 12, color: 'var(--dim2)' }}>
          {avail.picksLogged} of {avail.picksRequired} picks logged before a live adjustment is computed.
        </div>
      )}

      {/* HON-02 (docs/frontend-audit-2026-07.md): the dot array must never fall back
          to 0 when there is genuinely no value -- a zero-filled array is visually
          indistinguishable from a real 0%. Render it only when live or baseline is
          an actual number; when neither is, there's nothing honest to plot. */}
      {avail.live !== null || isPresent(avail.baseline) ? (
        <div style={{ marginTop: 8, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <Dots value={avail.live ?? (isPresent(avail.baseline) ? avail.baseline.value : 0)} />
        </div>
      ) : null}

      {avail.adjustment ? (
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <div style={{ fontSize: 11.5, color: 'var(--dim)' }}>
            Need adjustment: <span className="num">{signed(Math.round(avail.adjustment.need * 100))}</span> log-odds --
            roster gaps among teams picking before pick {integer(targetPick)}.
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--dim)' }}>
            Run adjustment: <span className="num">{signed(Math.round(avail.adjustment.run * 100))}</span> log-odds --
            positional run over the last 5 picks logged.
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Dots({ value }: { value: number }) {
  const filled = dotsFilled(value);
  return (
    <div style={{ display: 'flex', gap: 3 }} title={freqText(value)}>
      {Array.from({ length: 10 }, (_, i) => (
        <span
          key={i}
          style={{ width: 6, height: 6, borderRadius: '50%', background: i < filled ? 'var(--acc)' : 'var(--line2)' }}
        />
      ))}
    </div>
  );
}

function CorrPart({ label, value, note, field }: { label: string; value: string; note: string; field: string }) {
  return (
    <div style={{ padding: '9px 12px', background: 'var(--panel2)' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
        <span style={{ flex: 1, fontSize: 12.5 }}>{label}</span>
        <span className="num" style={{ fontSize: 13, color: 'var(--te)' }}>
          {value}
        </span>
      </div>
      <div style={{ marginTop: 4, fontSize: 12, lineHeight: 1.55, color: 'var(--dim)' }}>{note}</div>
      <div className="num" style={{ marginTop: 5, fontSize: 9, color: 'var(--dim2)' }}>
        {field}
      </div>
    </div>
  );
}
