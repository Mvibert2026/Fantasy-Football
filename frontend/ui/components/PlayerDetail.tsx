import { Component, useEffect, useMemo, type ReactNode } from 'react';
import type { BoardRow } from '../data/board';
import type { DraftPickRecord } from '../data/draft';
import { currentOverallPick, nextPickForSlot, pickNumbersForSlot, roundPickLabel } from '../data/draft';
import { isPresent } from '../data/cell';
import { computeLiveAvailability, dotsFilled, freqText, type LiveAvailabilityResult } from '../data/liveAvailability';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { recentSeasonKeys, usePlayerHistory, type PlayerHistoryState } from '../data/playerHistory';
import type { RawBoard, RawSeasonStatsPlayer, RawWeeklyFinishesPlayer, RawWeeklyFinishWeek } from '../data/types';
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
 * Sections 6 (archetype) and 9 (bullet takeaways) collapse into one line per
 * §8's rule for multiple empty sections on one player ("one collapsed line
 * naming everything missing at once, never three stacked empty headers"):
 * neither has a real field anywhere in this app's exports, for any player,
 * ever -- not a per-player gap, a permanent one. Headshot: same story, §6.9's
 * own admission -- no player in any real export has an ESPN id, so every card
 * renders initials on the team colour, always.
 *
 * Sections 7 (weekly finishes / consistency heat-map) and 8 (three-season
 * table) are a DIFFERENT claim from sections 6/9 and were deliberately NOT
 * folded into that collapse even while blocked (thread 052, Principle #2).
 * `weekly_finishes.json` / `season_stats.json` are real, non-empty, 1481-player
 * exports (thread 017/039), keyed by nflverse `player_id`. Until thread 052
 * landed, `board.json`'s matching field (`player_id_gsis`) was emitted null for
 * every player (0 of 378, verified against the live export at the time), so
 * these sections rendered an explicit "not yet joinable" reason instead of a
 * fetch. Thread 052/ADR-048 fixed the join: `player_id_gsis` is now populated
 * for 378/378 board players, and 371/378 (98.15%) resolve against
 * `weekly_finishes.json`/`season_stats.json` -- the 7 misses are real,
 * per-player absences (players with zero rows in `player_weekly_stats`,
 * plausibly rookies), a DIFFERENT claim again from "board-wide unjoinable",
 * so they get their own reason string too (`usePlayerHistory`'s `ready` state
 * with `weeklyFinishes`/`seasonStats` undefined -- see
 * `ui/data/playerHistory.ts`). "Not computed" (6/9), "not yet joinable"
 * (historical, pre-052), and "no rows for this player" (post-052, 7 of 378)
 * are three different claims and must never collapse into the same notice.
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

  // Sections 7/8 -- thread 052/ADR-048 join key. Re-fetches only when the
  // player changes (module-cached across the whole session either way).
  const history = usePlayerHistory(row.raw.player_id_gsis);
  const startableLine = data.board.replacement_levels_used[row.raw.position] ?? null;
  const startableLabel = startableLine !== null ? `${row.raw.position}${startableLine}` : null;

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

  // Thread 073 dismissible-surface audit: click-outside already worked (the
  // transparent click-catcher below calls onClose), but Escape did not -- the
  // close button is literally labelled "esc" without the key ever being
  // wired. Fixed here rather than via the shared ui/lib/dismiss.ts hook,
  // because that hook's click-outside half would conflict with the existing,
  // deliberately-transparent click-catcher pattern (§3.3); Escape alone is
  // all this component is missing.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  return (
    <>
      {/* Transparent click-catcher, not a scrim (§3.3) -- the board and the pick
          clock must stay visible while this panel is open. */}
      <div
        data-testid="player-detail-backdrop"
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, zIndex: 80, background: 'transparent' }}
      />
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

            {/* Contract 1.12.0 (thread 073): suspension state, rendered only when
                a confirmed suspension is on file. Every live row is false today
                (the curated list is empty -- ADR-053), so this block's absence
                everywhere is the correct current state. Pending-appeal rows are
                deliberately NOT point-adjusted upstream; say so rather than
                showing an adjusted number that does not exist. */}
            {row.raw.suspension_flag ? (
              <div
                data-testid="suspension-note"
                style={{ marginTop: 9, border: '1px solid var(--down)', padding: '8px 10px' }}
              >
                <div style={{ fontSize: 10, letterSpacing: '.08em', color: 'var(--down)' }}>
                  SUSPENSION ON FILE
                </div>
                <div style={{ marginTop: 4, fontSize: 12.5, lineHeight: 1.5 }}>
                  {row.raw.suspension_adjustment_note === 'games_adjusted' ? (
                    <>
                      Suspended{' '}
                      {row.raw.suspension_games != null
                        ? `${row.raw.suspension_games} games`
                        : '(game count missing from export)'}
                      .{' '}
                      {row.raw.projected_points_suspension_adjusted != null ? (
                        <>
                          Season projection adjusted to{' '}
                          <span className="num">
                            {decimal(row.raw.projected_points_suspension_adjusted)}
                          </span>{' '}
                          pts for the games missed.
                        </>
                      ) : (
                        'No adjusted projection in the export.'
                      )}
                    </>
                  ) : row.raw.suspension_adjustment_note === 'not_adjusted_pending_appeal' ? (
                    'Appeal pending — games are not final, so the projection is deliberately not adjusted.'
                  ) : (
                    'Suspension flagged without a recognised adjustment note.'
                  )}
                </div>
                <div className="num" style={{ marginTop: 5, fontSize: 9, color: 'var(--dim2)' }}>
                  board.json:suspension_flag · board.json:suspension_games ·
                  board.json:projected_points_suspension_adjusted
                </div>
              </div>
            ) : null}

            {/* 4. Availability at your picks. */}
            <SectionHeader label="AVAILABILITY AT YOUR PICKS" />
            {nextUserPick === null ? (
              <p className="notice" style={{ marginTop: 10 }}>
                No further picks for this team in this league's format.
              </p>
            ) : (
              <>
                {/* FR-087: which pick this section is about, and which round it
                    falls in -- nextUserPick itself still drives
                    computeLiveAvailability above, unchanged. */}
                <div style={{ marginTop: 10, fontSize: 11, color: 'var(--dim2)' }}>
                  at pick <span className="num">{integer(nextUserPick)}</span> ({roundPickLabel(nextUserPick, teams)})
                </div>
                <AvailabilitySection avail={availAtNext!} targetPick={nextUserPick} />
              </>
            )}
            {perPickStrip.length > 0 ? (
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {perPickStrip.map(({ pick, result }) => (
                  <div key={pick} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                    {/* FR-087: round + pick-within-round next to the overall pick
                        number -- `pick` itself (what feeds computeLiveAvailability
                        above) is unchanged. */}
                    <span className="num" style={{ width: 68, color: 'var(--dim2)' }}>
                      #{pick} <span style={{ color: 'var(--dim2)' }}>{roundPickLabel(pick, teams)}</span>
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

            {/* Contract 1.14.0 (thread 082, FR-024): market ADP, a different
                claim from CONSENSUS above -- that box is FantasyPros expert
                opinion, this is where MyFantasyLeague drafters actually took
                the player. Kept in this section (near the other "how does
                the market see this player" numbers) rather than as its own
                numbered section, and deliberately not a delta against our
                rank -- WHY OUR RANK DIFFERS above already covers that
                relationship for consensus; a second, differently-defined
                delta here would read as the same signal. */}
            <AdpBlock row={row} board={data.board} league={league} />

            {/* 6. Archetype -- permanently absent, no field in any export, ever.
                Previously collapsed with section 9 into one shared line under
                §8's multi-empty-section rule; that only works when the empty
                sections are adjacent, and 7/8 no longer are (they're a real,
                distinct claim now -- see above). Each keeps its own one-line
                header + notice instead, per §7.2's normal numbered layout. */}
            <SectionHeader label="ARCHETYPE" />
            <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
              Not computed: archetype. No backend field in this build.
            </p>

            {/* 7. Weekly finishes / consistency heat-map. Real data as of
                thread 052/ADR-048's join-key fix -- see WeeklyFinishesSection
                below for the loading / no-key / error / no-rows-for-this-
                player states, each a distinct claim per Principle #2. */}
            <SectionHeader label="WEEKLY FINISHES" />
            <HistorySectionBoundary label="weekly finishes">
              <WeeklyFinishesSection history={history} startableLine={startableLine} startableLabel={startableLabel} />
            </HistorySectionBoundary>

            {/* 8. Three-season table. */}
            <SectionHeader label="THREE SEASONS" />
            <HistorySectionBoundary label="three-season table">
              <ThreeSeasonSection history={history} />
            </HistorySectionBoundary>

            {/* 9. Bullet takeaways -- permanently absent, same as archetype. */}
            <SectionHeader label="TAKEAWAYS" />
            <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
              Not computed: takeaways. No backend field in this build.
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
          {/* design/INERT-CONTROLS.md (FR-037): Compare and Ask were both dead
              buttons -- neither is built, and the assistant dock (always
              reachable, bottom of the app) already does Ask's job. "Absent from
              the action row. The row shrinks; it does not hold a gap." -- removed
              outright, not replaced with a statement, since a statement is only
              for cases where an action was expected right here specifically. */}
        </div>
      </div>
    </>
  );
}

/**
 * Sections 7/8 read real, freshly-wired historical data (thread 052/ADR-048)
 * with several honest-null branches (loading / no-key / no-rows-for-this-
 * player). A bug in any one of those branches, or in a single unexpected
 * player's data shape, should never blank the whole sheet -- identity,
 * projection, availability and the why-differs breakdown above are all
 * independently useful even if the history sections have a defect. Scoped
 * tightly to these two sections rather than wrapping the whole component.
 */
class HistorySectionBoundary extends Component<
  { label: string; children: ReactNode },
  { error: Error | null }
> {
  state: { error: Error | null } = { error: null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <p className="notice" style={{ marginTop: 10, fontSize: 12, color: 'var(--down)' }}>
          Could not render {this.props.label}: {this.state.error.message}
        </p>
      );
    }
    return this.props.children;
  }
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

/**
 * Contract 1.14.0 (thread 082). The one place this app shows the full ADP
 * caveat verbatim -- board.json:adp_source_note, written for display and
 * not summarised here, because the board/draft-room columns only have room
 * for a hover tooltip and this sheet is where a reader would go to check.
 * `adp_selected_pct` is 0-100 already (not a 0-1 fraction like the
 * availability percentages elsewhere in this file), so it gets its own
 * formatter rather than reusing `percent()` -- and the same real-zero /
 * genuinely-small / genuinely-absent three-way distinction Principle #2
 * requires applies here too.
 *
 * FR-083 ("Why do player notes cards not show adp for the correct format for
 * the league selected?"). Traced, not assumed: `board.json:adp_source` is
 * `mfl_proxy` for every league export, always -- `src/export_contract.py`'s
 * `_load_adp_snapshot` takes no `cfg` argument and defaults to that one
 * source regardless of which league built the board. `adp_source_note`
 * itself (rendered below, verbatim from the export) even says so in its own
 * prose for the primary league ("MFL's IS_PPR flag is binary and this league
 * scores half-PPR") -- text that is factually WRONG when read on any
 * non-Westwood league export, since it hardcodes Westwood's ruleset rather
 * than reading `cfg.scoring`. This is a real backend defect (flagged to
 * `backend` via a handoff thread, not fixed here -- `src/export_contract.py`
 * is backend's file and this worktree has no `nfl.db` to verify a fix
 * against), not a frontend routing bug: `row.adp` already traces correctly
 * to whichever league's `board.json` is currently loaded (`ui/data/board.ts`
 * reads it straight off `data.board.players[i].adp`, no caching across a
 * league switch) -- the SOURCE itself just isn't league-aware yet. Per this
 * project's absent-not-inert rule, the fix here is not to silently rewrite
 * or suppress the backend's (currently wrong-for-non-Westwood) note, but to
 * put the league's own real, per-league-correct scoring ruleset
 * (`league.json:scoring_ruleset_note`, contract 1.15.0, always accurate --
 * unlike `adp_source_note` it DOES vary correctly by league) right next to
 * it, so a reader can see the two don't necessarily describe the same thing.
 */
function AdpBlock({ row, board, league }: { row: BoardRow; board: RawBoard; league: LeagueConfig }) {
  const sourceLabel =
    row.adpSource === 'mfl_proxy'
      ? 'MyFantasyLeague proxy, full PPR -- not this league\'s own ADP'
      : row.adpSource
        ? row.adpSource
        : null;
  return (
    <div style={{ marginTop: 10, border: '1px solid var(--line)' }}>
      <div style={{ padding: '9px 12px' }}>
        <div style={{ fontSize: 9.5, letterSpacing: '.08em', color: 'var(--dim2)' }}>
          MARKET ADP{sourceLabel ? ` — ${sourceLabel}` : ''}
        </div>
        {row.adp.kind === 'present' ? (
          <>
            <div style={{ marginTop: 5, display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
              <span className="num" style={{ fontSize: 20, fontWeight: 600 }}>
                {decimal(row.adp.value)}
              </span>
              <span style={{ fontSize: 11, color: 'var(--dim2)' }}>avg. pick</span>
              {row.adpMinPick.kind === 'present' && row.adpMaxPick.kind === 'present' ? (
                <span className="num" style={{ fontSize: 12, color: 'var(--dim)' }}>
                  range {integer(row.adpMinPick.value)}–{integer(row.adpMaxPick.value)}
                </span>
              ) : null}
              {row.adpSelectedPct.kind === 'present' ? (
                <span className="num" style={{ fontSize: 12, color: 'var(--dim)' }}>
                  taken in {adpPctText(row.adpSelectedPct.value)} of sampled drafts
                </span>
              ) : null}
            </div>
          </>
        ) : (
          <p className="notice" style={{ marginTop: 6, fontSize: 12 }}>
            {row.adp.reason}
          </p>
        )}
        {board.adp_source_note ? (
          <p className="notice" style={{ marginTop: 8, fontSize: 11 }}>
            {board.adp_source_note}
          </p>
        ) : null}
        {/* FR-083: this league's own real scoring ruleset, so a reader can check
            it against the ADP note above -- see this function's doc comment for
            why that note's own prose is not reliably about THIS league. */}
        {league.scoringRulesetNote.kind === 'present' ? (
          <p className="notice" style={{ marginTop: 8, fontSize: 11 }}>
            This league's scoring ruleset: {league.scoringRulesetNote.value}
          </p>
        ) : null}
        <div className="num" style={{ marginTop: 6, fontSize: 9, color: 'var(--dim2)' }}>
          board.json:players[].adp{board.adp_as_of_date ? ` · snapshot as of ${board.adp_as_of_date}` : ''}
          {league.scoringRulesetNote.kind === 'present' ? ' · league.json:scoring_ruleset_note' : ''}
        </div>
      </div>
    </div>
  );
}

/** `adp_selected_pct` is already a 0-100 percentage (16.0 means 16%), not a
 *  0-1 fraction -- `lib/format.ts#percent` expects the latter, so this is a
 *  small local formatter rather than a misuse of that one. Same honest-zero
 *  vs. genuinely-small distinction: a real, computed sub-1% share reads
 *  "<1%", never a rounded-down "0%". */
function adpPctText(n: number): string {
  if (n > 0 && n < 1) return '<1%';
  return `${Math.round(n)}%`;
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

/**
 * Sections 7/8's shared state machine. `loading` / `no-key` / `error` are the
 * same three strings for both sections modulo the file name; `ready` with the
 * relevant player record `undefined` is the fourth, per-player state (thread
 * 052: 7 of 378 board players have no rows at all in either file). None of
 * these four collapse into each other or into section 6/9's "not computed" --
 * see the file-top docstring for why that distinction is load-bearing.
 */
function HistoryFallback({ history, file }: { history: PlayerHistoryState; file: string }) {
  if (history.status === 'loading') {
    return (
      <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
        Loading {file}…
      </p>
    );
  }
  if (history.status === 'no-key') {
    return (
      <>
        <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
          This player's board row carries no player_id_gsis -- can't attach {file}. Distinct from
          the 371/378 that do resolve (thread 052/ADR-048); this specific row is the exception.
        </p>
        <div className="num" style={{ marginTop: 5, fontSize: 9, color: 'var(--dim2)' }}>
          board.json:player_id_gsis
        </div>
      </>
    );
  }
  // history.status === 'error'
  return (
    <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
      Could not load {file}: {history.status === 'error' ? history.message : ''}
    </p>
  );
}

function WeeklyFinishesSection({
  history,
  startableLine,
  startableLabel,
}: {
  history: PlayerHistoryState;
  startableLine: number | null;
  startableLabel: string | null;
}) {
  if (history.status !== 'ready') {
    return <HistoryFallback history={history} file="weekly_finishes.json" />;
  }
  if (!history.weeklyFinishes) {
    return (
      <>
        <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
          No historical stats on file for this player -- zero rows in player_weekly_stats (thread
          052 measured 7 of 378 board players this way, plausibly rookies). The join key resolved;
          there is simply no prior NFL history to show. Not the same claim as a join failure.
        </p>
        <div className="num" style={{ marginTop: 5, fontSize: 9, color: 'var(--dim2)' }}>
          weekly_finishes.json:players[]
        </div>
      </>
    );
  }
  return <WeeklyFinishesHeatmap player={history.weeklyFinishes} startableLine={startableLine} startableLabel={startableLabel} />;
}

function ThreeSeasonSection({ history }: { history: PlayerHistoryState }) {
  if (history.status !== 'ready') {
    return <HistoryFallback history={history} file="season_stats.json" />;
  }
  if (!history.seasonStats) {
    return (
      <>
        <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
          No historical stats on file for this player -- zero rows in player_weekly_stats (thread
          052 measured 7 of 378 board players this way, plausibly rookies). The join key resolved;
          there is simply no prior NFL history to show. Not the same claim as a join failure.
        </p>
        <div className="num" style={{ marginTop: 5, fontSize: 9, color: 'var(--dim2)' }}>
          season_stats.json:players[]
        </div>
      </>
    );
  }
  return <ThreeSeasonTable player={history.seasonStats} />;
}

/** §7.2 item 7: 18-cell heatmap, gradient over positional finish, 2px bottom
 *  rule on cells below the startable line -- a redundant non-colour cue, not
 *  a replacement for the gradient, since colour alone isn't an accessible
 *  signal. Most recent season this player has in the export; weeks beyond 18
 *  don't occur in an NFL season so `.slice` is a no-op guard, not a real cap. */
function WeeklyFinishesHeatmap({
  player,
  startableLine,
  startableLabel,
}: {
  player: RawWeeklyFinishesPlayer;
  startableLine: number | null;
  startableLabel: string | null;
}) {
  const [seasonKey] = recentSeasonKeys(player, 1);
  if (!seasonKey) {
    return (
      <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
        weekly_finishes.json has this player but no season rows under them.
      </p>
    );
  }
  const season = player.seasons[seasonKey]!;
  const weeks = [...season.weeks].sort((a, b) => a.week - b.week).slice(0, 18);
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ fontSize: 10, letterSpacing: '.08em', color: 'var(--dim2)' }}>
        {seasonKey} SEASON · POSITIONAL FINISH BY WEEK
      </div>
      <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: 'repeat(9, 1fr)', gap: 4 }}>
        {weeks.map((w) => (
          <HeatCell key={w.week} week={w} startableLine={startableLine} />
        ))}
      </div>
      <div style={{ marginTop: 6, fontSize: 10.5, lineHeight: 1.5, color: 'var(--dim2)' }}>
        Darker = better positional finish that week.
        {startableLabel ? ` Orange bottom rule = finished worse than this league's ${startableLabel} startable line.` : ''}
      </div>
      {/* FR-079 ("Last few seasons should be in correct fomat as well").
          Traced, not assumed: `src/export_history.py::build_weekly_finishes`
          ranks positional finish by `player_weekly_stats.fantasy_points_ppr`
          -- a fixed, standard-PPR figure computed once, with no `scoring_cfg`
          argument at all (unlike `make_board.build_board`, which does take
          one). weekly_finishes.json is also not exported per league -- it
          lives unprefixed at the top level, never under `leagues/<id>/`
          (confirmed: `data/export/espn_10_standard/` etc. carry no copy) --
          so switching leagues cannot change this number even in principle
          yet. This is a genuine export-contract gap, not a frontend routing
          bug: converting it in the browser would mean re-deriving fantasy
          points from raw stats client-side, which this project's rule
          against approximating scoring outside the pipeline forbids. Say so
          plainly instead. Flagged to `backend` via a handoff thread. */}
      <p className="notice" style={{ marginTop: 6, fontSize: 10.5 }}>
        Ranked by standard PPR scoring, not this league's own ruleset (see MARKET ADP above) --
        weekly_finishes.json does not yet vary by league.
      </p>
      <div className="num" style={{ marginTop: 5, fontSize: 9, color: 'var(--dim2)' }}>
        weekly_finishes.json:players[].seasons[{seasonKey}].weeks
      </div>
    </div>
  );
}

function HeatCell({ week, startableLine }: { week: RawWeeklyFinishWeek; startableLine: number | null }) {
  if (week.bye) {
    return (
      <div
        className="num"
        style={{
          aspectRatio: '1',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 8,
          color: 'var(--dim2)',
          border: '1px dashed var(--line2)',
        }}
        title={`Week ${week.week}: bye`}
      >
        BYE
      </div>
    );
  }
  if (week.finish === null) {
    // Honest "no row" state, per the artifact's own no_row_semantics_note --
    // NOT a confirmed inactive/roster-status lookup, just an absent stat line.
    return (
      <div
        className="num"
        style={{ aspectRatio: '1', border: '1px solid var(--line)', background: 'var(--panel2)' }}
        title={`Week ${week.week}: no recorded stat line (not a confirmed inactive)`}
      />
    );
  }
  const opacity = Math.max(0.12, Math.min(1, 1.15 - week.finish / 40));
  const belowStartable = startableLine !== null && week.finish > startableLine;
  return (
    <div
      style={{ position: 'relative', aspectRatio: '1', overflow: 'hidden' }}
      title={`Week ${week.week}: finished ${week.finish} at position${belowStartable ? ' (below startable line)' : ''}`}
    >
      <div style={{ position: 'absolute', inset: 0, background: 'var(--acc)', opacity }} />
      <div
        className="num"
        style={{
          position: 'relative',
          display: 'flex',
          height: '100%',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 9,
          fontWeight: 600,
          color: 'var(--txt)',
        }}
      >
        {week.finish}
      </div>
      {belowStartable ? (
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 2, background: 'var(--down)' }} />
      ) : null}
    </div>
  );
}

/** §7.2 item 8: three most recent seasons on file (not always calendar-recent
 *  -- a player with a gap shows their 3 most recent logged seasons, not 3
 *  consecutive years padded with fabricated blanks). Targets are deliberately
 *  not a column: 2003-2008 rows carry `target_data_unavailable`, and folding
 *  a sometimes-null field into a dense numeric grid invites exactly the
 *  0-vs-null confusion Principle #2 forbids -- called out in a footnote
 *  instead, only when it actually applies to a shown season. */
function ThreeSeasonTable({ player }: { player: RawSeasonStatsPlayer }) {
  const seasons = [...player.seasons].sort((a, b) => b.year - a.year).slice(0, 3);
  if (seasons.length === 0) {
    return (
      <p className="notice" style={{ marginTop: 10, fontSize: 12 }}>
        season_stats.json has this player but no season rows under them.
      </p>
    );
  }
  const cols = '44px 32px 38px 50px 38px 50px 38px 52px';
  const unavailableYears = seasons.filter((s) => s.target_data_unavailable).map((s) => s.year);
  return (
    <div style={{ marginTop: 10 }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: cols,
          gap: 2,
          fontSize: 9,
          letterSpacing: '.04em',
          color: 'var(--dim2)',
        }}
      >
        <span>YEAR</span>
        <span>GM</span>
        <span>REC</span>
        <span>REC YD</span>
        <span>REC TD</span>
        <span>RSH YD</span>
        <span>RSH TD</span>
        <span>PPR PTS</span>
      </div>
      {seasons.map((s) => (
        <div
          key={s.year}
          className="num"
          style={{
            display: 'grid',
            gridTemplateColumns: cols,
            gap: 2,
            fontSize: 11.5,
            padding: '5px 0',
            borderTop: '1px solid var(--line)',
          }}
        >
          <span>{s.year}</span>
          <span>{integer(s.games)}</span>
          <span>{integer(s.receptions)}</span>
          <span>{integer(s.receiving_yards)}</span>
          <span>{integer(s.receiving_tds)}</span>
          <span>{integer(s.rushing_yards)}</span>
          <span>{integer(s.rushing_tds)}</span>
          <span style={{ color: 'var(--acc)', fontWeight: 600 }}>{decimal(s.fantasy_points_ppr)}</span>
        </div>
      ))}
      {unavailableYears.length > 0 ? (
        <p className="notice" style={{ marginTop: 8, fontSize: 10.5 }}>
          Targets not reliably charted for {unavailableYears.join(', ')} (upstream charting-coverage
          gap, not a real zero) -- season_stats.json:players[].seasons[].target_data_unavailable.
          Not shown as its own column for that reason.
        </p>
      ) : null}
      {/* FR-079: same fixed-format gap as WeeklyFinishesHeatmap's own note above
          (`src/export_history.py::build_season_stats` sums the same
          `player_weekly_stats.fantasy_points_ppr`, no `scoring_cfg`, not
          exported per league) -- PPR PTS is real historical PPR scoring, not
          a claim about this league's own ruleset. */}
      <p className="notice" style={{ marginTop: 8, fontSize: 10.5 }}>
        PPR PTS is standard PPR scoring, not this league's own ruleset (see MARKET ADP above) --
        season_stats.json does not yet vary by league.
      </p>
      <div className="num" style={{ marginTop: 6, fontSize: 9, color: 'var(--dim2)' }}>
        season_stats.json:players[].seasons
      </div>
    </div>
  );
}
