import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import type { BoardRow } from '../data/board';
import {
  currentOverallPick,
  isSlotOnClock,
  loadDraftState,
  nextPickForSlot,
  pruneQueue,
  roundOfPick,
  saveDraftState,
  takenPlayerIds,
  teamSlotAtPick,
  toDraftLog,
  type DraftPickRecord,
  type DraftState,
} from '../data/draft';
import { computeLiveAvailability, type LiveAvailabilityResult } from '../data/liveAvailability';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { rankByRecommendation } from '../data/recommendation';
import { depletionWarning, positionScarcity } from '../data/scarcity';
import { useWatchlist } from '../data/useWatchlist';
import { PlayerDetail } from '../components/PlayerDetail';
import { Value } from '../components/Value';
import { decimal, integer, percent, signed } from '../lib/format';

/** §3.2's pane-width formula, using the spec's own defaults since this build has
 *  no host props editor (see the module doc). Returns a grid-template-columns
 *  value with each pane as a normalised percentage. */
function paneColumns(boardPct = 35, centerPct = 40): string {
  const board = Math.min(60, Math.max(20, boardPct));
  const center = Math.min(65, Math.max(20, centerPct));
  const right = Math.max(14, 100 - board - center);
  const total = board + center + right;
  return `minmax(0,${((board / total) * 100).toFixed(2)}%) minmax(0,${((center / total) * 100).toFixed(2)}%) minmax(0,${((right / total) * 100).toFixed(2)}%)`;
}

const SCARCITY_POSITIONS = ['QB', 'RB', 'WR', 'TE'] as const;

/**
 * Draft Room, ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html, lines 143-441) and
 * upgraded to FRONTEND-SPEC.md §7.1/§3.2: a command bar (search-to-mark-pick,
 * undo, on-clock/until-you/next-pick stats) over a three-pane grid -- available
 * players, recommendation/scarcity, roster + log.
 *
 * Pane widths follow §3.2's formula exactly (board/center/right, clamped and
 * normalised to 100%), using the spec's own defaults (35/40/25) -- this build has
 * no host environment to expose the tweakable-props editor (§3.4) to, so the
 * ratios are real but not user-adjustable, which is a smaller and more honest gap
 * than building a props-editing UI nothing else in this app has a parallel for.
 *
 * Explicit departures, each because the prototype's or spec's version needs data
 * or a live simulator this build does not have:
 *
 *   - "Auto-fill to my pick" (prototype's simToMe, line 2083) is NOT built. It
 *     would inject random opponent picks into exactly the log this session's
 *     export feature exists to keep real (item 2's whole point is picks usable as
 *     real mock-draft data) -- fabricating picks to fill screen space would work
 *     directly against that.
 *   - Availability everywhere in this file (row badges, watchlist, per-pick
 *     strip in the player sheet) is the real two-number model, ui/data/
 *     liveAvailability.ts -- baseline and live shown together, never one
 *     replacing the other, per §5.2's explicit display contract.
 *   - The decision-rules-with-evidence list (prototype lines 367-384) is not
 *     built -- there is no backtested rule set behind it in this project yet
 *     (see docs/test-registry.md upstream); fabricating rule text would violate
 *     the same "no rendered value without a named field" principle everything
 *     else here follows.
 *   - Hub tabs (Board / Opponents / Predictions, §7.1) are not yet folded into
 *     this pane -- Opponents and a standalone Predictions table exist as their
 *     own Prep-mode screens; duplicating them inside the draft hub is a follow-up,
 *     not core to a working draft room.
 *   - The recommendation score (ui/data/recommendation.ts) is a simple,
 *     unvalidated stopgap formula, not a backtested model -- said so on screen.
 */

const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
};

const POSITION_TABS = ['ALL', 'QB', 'RB', 'WR', 'TE'] as const;
type PositionTab = (typeof POSITION_TABS)[number];

interface RosterSlot {
  slot: string;
  kind: 'starter' | 'flex' | 'bench';
  position: string | null; // null for FLEX/BN, which accept multiple positions
  row: BoardRow | null;
}

/** Greedy slot assignment: each of the user's picks, in draft order, fills the
 *  first open slot that matches its position, then the first open FLEX it's
 *  eligible for, then the first open bench slot. Good enough for a dry run --
 *  not a claim about how the real platform will assign slots. */
function buildRosterSlots(
  userPicks: DraftPickRecord[],
  league: LeagueConfig,
  data: Dataset,
  rowsById: Map<number, BoardRow>,
): RosterSlot[] {
  const slots: RosterSlot[] = [];
  for (const t of league.thresholds) {
    if (t.position === 'FLEX') continue; // placed after named positions, below
    const count = t.starters.kind === 'present' ? t.starters.value : 0;
    for (let i = 0; i < count; i++) slots.push({ slot: t.position, kind: 'starter', position: t.position, row: null });
  }
  const flex = league.thresholds.find((t) => t.position === 'FLEX');
  const flexCount = flex && flex.starters.kind === 'present' ? flex.starters.value : 0;
  for (let i = 0; i < flexCount; i++) slots.push({ slot: 'FLEX', kind: 'flex', position: null, row: null });
  const bench = data.league.roster.bench ?? 0;
  for (let i = 0; i < bench; i++) slots.push({ slot: 'BN', kind: 'bench', position: null, row: null });
  const flexEligible = new Set(data.league.roster.flex_eligible ?? []);

  for (const pick of userPicks) {
    if (pick.playerId === null) continue;
    const row = rowsById.get(pick.playerId);
    const pos = row?.raw.position ?? null;
    let target =
      slots.find((s) => s.kind === 'starter' && s.position === pos && s.row === null) ??
      (pos && flexEligible.has(pos) ? slots.find((s) => s.kind === 'flex' && s.row === null) : undefined) ??
      slots.find((s) => s.kind === 'bench' && s.row === null);
    if (!target) continue;
    target.row = row ?? null;
    if (!row) target.slot = `${target.slot} (${pick.playerName})`;
  }
  return slots;
}

function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function DraftRoom({
  data,
  rows,
  league,
  onOpenPlayer,
}: {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
  onOpenPlayer?: (name: string | null) => void;
}) {
  const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
  const [draft, setDraft] = useState<DraftState>(() => loadDraftState(leagueId));
  const [watchlist, toggleWatch] = useWatchlist();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  const [positionTab, setPositionTab] = useState<PositionTab>('ALL');
  const [detailRow, setDetailRow] = useState<BoardRow | null>(null);
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);
  const [railTab, setRailTab] = useState<'queue' | 'watch'>('watch');
  const searchRef = useRef<HTMLInputElement>(null);

  function openDetail(row: BoardRow) {
    setDetailRow(row);
    onOpenPlayer?.(row.name.kind === 'present' ? row.name.value : null);
  }

  // Reload from storage when the league changes underneath this component
  // (switching leagues in the top bar) rather than carrying stale picks over.
  useEffect(() => {
    setDraft(loadDraftState(leagueId));
  }, [leagueId]);

  const rowsById = useMemo(() => new Map(rows.map((r) => [r.id, r])), [rows]);
  const teams = league.teams.kind === 'present' ? league.teams.value : 0;
  const rounds = league.rounds.kind === 'present' ? league.rounds.value : 0;
  const userSlot = league.userSlot.kind === 'present' ? league.userSlot.value : 0;

  const taken = useMemo(() => takenPlayerIds(draft.picks), [draft.picks]);
  const available = useMemo(() => rows.filter((r) => !taken.has(r.id)), [rows, taken]);
  const availableInTab = useMemo(
    () => (positionTab === 'ALL' ? available : available.filter((r) => r.raw.position === positionTab)),
    [available, positionTab],
  );

  const currentPick = currentOverallPick(draft.picks);
  const currentRound = teams > 0 ? roundOfPick(currentPick, teams) : 0;
  const onClockSlot = teams > 0 ? teamSlotAtPick(currentPick, teams) : 0;
  const userOnClock = teams > 0 && isSlotOnClock(draft.picks, teams, userSlot);
  const nextUserPick = teams > 0 ? nextPickForSlot(draft.picks, teams, userSlot, rounds) : null;
  const picksUntilYou = userOnClock ? 0 : nextUserPick !== null ? nextUserPick - currentPick : null;
  const draftComplete = teams > 0 && rounds > 0 && currentPick > teams * rounds;

  function persist(next: DraftState) {
    setDraft(next);
    saveDraftState(next);
  }

  function recordPick(playerId: number | null, playerName: string) {
    if (draftComplete || !playerName.trim()) return;
    const overallPick = currentOverallPick(draft.picks);
    const round = roundOfPick(overallPick, teams);
    const teamSlot = teamSlotAtPick(overallPick, teams);
    const entry: DraftPickRecord = {
      overallPick,
      round,
      teamSlot,
      playerId,
      playerName,
      timestamp: new Date().toISOString(),
    };
    persist({ ...draft, picks: [...draft.picks, entry], queue: pruneQueue(draft.queue, playerId) });
    setQuery('');
    setSelected(0);
    searchRef.current?.focus();
  }

  /** Removes one pick and renumbers everything after it -- overallPick/round/
   *  teamSlot are derived from list position, so they must be recomputed, not
   *  just deleted in place, or every later pick would report the wrong slot. */
  function removePick(overallPick: number) {
    const remaining = draft.picks.filter((p) => p.overallPick !== overallPick);
    const renumbered = remaining.map((p, i) => {
      const n = i + 1;
      return { ...p, overallPick: n, round: roundOfPick(n, teams), teamSlot: teamSlotAtPick(n, teams) };
    });
    persist({ ...draft, picks: renumbered });
  }

  function resetDraft() {
    persist({ leagueId, mockId: draft.mockId, picks: [], queue: draft.queue });
  }

  function toggleQueue(id: number) {
    const has = draft.queue.includes(id);
    persist({ ...draft, queue: has ? draft.queue.filter((q) => q !== id) : [...draft.queue, id] });
  }

  const searchResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return available
      .filter((r) => r.name.kind === 'present' && r.name.value.toLowerCase().includes(q))
      .slice(0, 8);
  }, [query, available]);

  function onSearchKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelected((s) => Math.min(searchResults.length - 1, s + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelected((s) => Math.max(0, s - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const hit = searchResults[selected];
      if (hit && hit.name.kind === 'present') {
        recordPick(hit.id, hit.name.value);
      } else if (query.trim()) {
        // No board match -- log the raw text (a kicker, a DST, a rookie off this
        // board). Real data entry beats refusing to record what actually happened.
        recordPick(null, query.trim());
      }
    } else if (e.key === 'Escape') {
      setQuery('');
      setSelected(0);
    }
  }

  const userPicks = useMemo(() => draft.picks.filter((p) => p.teamSlot === userSlot), [draft.picks, userSlot]);
  const rosterSlots = useMemo(
    () => buildRosterSlots(userPicks, league, data, rowsById),
    [userPicks, league, data, rowsById],
  );
  const unfilledPositions = useMemo(
    () => new Set(rosterSlots.filter((s) => s.kind === 'starter' && s.row === null).map((s) => s.position as string)),
    [rosterSlots],
  );

  const recommended = useMemo(() => {
    if (!userOnClock) return [];
    return rankByRecommendation(available, currentRound, unfilledPositions).slice(0, 6);
  }, [userOnClock, available, currentRound, unfilledPositions]);

  const watchRows = useMemo(() => {
    if (userOnClock || nextUserPick === null) return [];
    return watchlist
      .map((name) => available.find((r) => r.name.kind === 'present' && r.name.value === name))
      .filter((r): r is BoardRow => !!r)
      .map((row) => ({
        row,
        avail: computeLiveAvailability({ data, league, row, targetPick: nextUserPick, picks: draft.picks, rowsById }),
      }));
  }, [userOnClock, nextUserPick, watchlist, available, data, league, draft.picks, rowsById]);

  const queueRows = useMemo(() => {
    if (userOnClock || nextUserPick === null) return [];
    return draft.queue
      .map((id) => rowsById.get(id))
      .filter((r): r is BoardRow => !!r && !taken.has(r.id))
      .map((row) => ({
        row,
        avail: computeLiveAvailability({ data, league, row, targetPick: nextUserPick, picks: draft.picks, rowsById }),
      }));
  }, [userOnClock, nextUserPick, draft.queue, taken, data, league, draft.picks, rowsById]);

  const scarcityList = useMemo(
    () =>
      positionScarcity(
        data,
        rows,
        draft.picks,
        currentPick,
        nextUserPick,
        SCARCITY_POSITIONS,
        Object.fromEntries(
          league.thresholds.map((t) => [t.position, t.starters.kind === 'present' ? t.starters.value : 0]),
        ),
        teams,
      ),
    [data, rows, draft.picks, currentPick, nextUserPick, league.thresholds, teams],
  );

  if (teams === 0 || rounds === 0 || userSlot === 0) {
    return (
      <div style={{ padding: 20 }}>
        <div className="empty">
          <strong>Draft mode needs league.json:teams, rounds and user_draft_slot.</strong> One or
          more is missing for this league.
        </div>
      </div>
    );
  }

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          flex: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          padding: '9px 14px',
          borderBottom: '1px solid var(--line)',
          background: 'var(--panel2)',
        }}
      >
        <div style={{ position: 'relative', flex: 1, maxWidth: 540 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 9,
              border: '1px solid var(--line2)',
              background: 'var(--bg)',
              padding: '0 10px',
              height: 38,
            }}
          >
            <span style={{ fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)' }}>/</span>
            <input
              ref={searchRef}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setSelected(0);
              }}
              onKeyDown={onSearchKeyDown}
              placeholder={
                draftComplete
                  ? 'Draft complete'
                  : `Mark pick ${currentPick} (team ${onClockSlot}${userOnClock ? ' — you' : ''}) — type a player name`
              }
              disabled={draftComplete}
              style={{ flex: 1, height: 36, background: 'transparent', border: 0, outline: 'none', fontSize: 14 }}
            />
          </div>
          {searchResults.length > 0 ? (
            <div
              style={{
                position: 'absolute',
                top: 40,
                left: 0,
                right: 0,
                zIndex: 60,
                background: 'var(--panel)',
                border: '1px solid var(--line2)',
              }}
            >
              {searchResults.map((r, i) => (
                <div
                  key={r.id}
                  onClick={() => r.name.kind === 'present' && recordPick(r.id, r.name.value)}
                  onMouseEnter={() => setSelected(i)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '8px 10px',
                    cursor: 'pointer',
                    background: i === selected ? 'var(--panel2)' : 'transparent',
                    borderBottom: '1px solid var(--line)',
                  }}
                >
                  <span style={{ fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)', width: 26 }}>
                    <Value cell={r.overallRank} render={integer} />
                  </span>
                  <span style={{ fontWeight: 600, flex: 1 }}>{r.name.kind === 'present' ? r.name.value : ''}</span>
                  <span style={{ fontSize: 11, letterSpacing: '.045em', color: POSITION_COLOR[r.raw.position] }}>
                    {r.raw.position}
                  </span>
                  <span style={{ fontSize: 11, letterSpacing: '.045em', color: 'var(--dim2)', width: 34, textAlign: 'right' }}>
                    {r.raw.team}
                  </span>
                </div>
              ))}
              <div style={{ padding: '5px 10px', fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)', display: 'flex', gap: 14 }}>
                <span>↑↓ navigate</span>
                <span>⏎ mark taken</span>
                <span>esc clear</span>
              </div>
            </div>
          ) : null}
        </div>

        {draft.picks.length > 0 ? (
          <div
            onClick={() => removePick(draft.picks[draft.picks.length - 1]!.overallPick)}
            title="Undo last pick"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '5px 10px',
              border: '1px dashed var(--line2)',
              cursor: 'pointer',
              maxWidth: 230,
            }}
          >
            <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)' }}>UNDO</span>
            <span style={{ fontSize: 12, color: 'var(--dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              #{draft.picks[draft.picks.length - 1]!.overallPick} {draft.picks[draft.picks.length - 1]!.playerName}
            </span>
          </div>
        ) : null}

        <div style={{ flex: 1 }} />

        <button
          onClick={() => downloadJson(`draft-log-${draft.mockId}.json`, toDraftLog(draft))}
          disabled={draft.picks.length === 0}
          style={{
            padding: '5px 10px',
            background: 'transparent',
            border: '1px solid var(--line2)',
            color: draft.picks.length === 0 ? 'var(--dim2)' : 'var(--txt)',
            fontSize: 11,
          }}
        >
          Export draft log
        </button>
        <button
          onClick={resetDraft}
          disabled={draft.picks.length === 0}
          style={{
            padding: '5px 10px',
            background: 'transparent',
            border: '1px solid var(--line2)',
            color: draft.picks.length === 0 ? 'var(--dim2)' : 'var(--dim)',
            fontSize: 11,
          }}
        >
          Reset draft
        </button>

        <div style={{ display: 'flex', alignItems: 'stretch', gap: 0, border: '1px solid var(--line2)' }}>
          <div style={{ padding: '4px 12px', textAlign: 'center', borderRight: '1px solid var(--line)' }}>
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 9, letterSpacing: '.1em', color: 'var(--dim2)' }}>
              ON THE CLOCK
            </div>
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 18, fontWeight: 600 }}>
              {draftComplete ? 'done' : `#${currentPick} · team ${onClockSlot}`}
            </div>
          </div>
          <div
            style={{
              padding: '4px 14px',
              textAlign: 'center',
              background: userOnClock ? 'var(--live)' : 'transparent',
              borderRight: '1px solid var(--line)',
            }}
          >
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 9, letterSpacing: '.1em', color: userOnClock ? '#0a0d12' : 'var(--dim2)' }}>
              PICKS UNTIL YOU
            </div>
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 26, lineHeight: 1, fontWeight: 600, color: userOnClock ? '#0a0d12' : 'var(--txt)' }}>
              {userOnClock ? 'NOW' : (picksUntilYou ?? '—')}
            </div>
          </div>
          <div style={{ padding: '4px 12px', textAlign: 'center' }}>
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 9, letterSpacing: '.1em', color: 'var(--dim2)' }}>YOUR NEXT</div>
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 18, fontWeight: 600 }}>
              {nextUserPick ?? '—'}
            </div>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0, display: 'grid', gridTemplateColumns: paneColumns() }}>
        <div style={{ minHeight: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--line)' }}>
          <div style={{ flex: 'none', padding: '8px 12px 6px', borderBottom: '1px solid var(--line)', display: 'flex', gap: 4 }}>
            {POSITION_TABS.map((t) => (
              <button
                key={t}
                aria-pressed={positionTab === t}
                onClick={() => setPositionTab(t)}
                style={{
                  flex: 1,
                  padding: '5px 0',
                  background: positionTab === t ? 'var(--panel2)' : 'transparent',
                  border: `1px solid ${positionTab === t ? 'var(--line2)' : 'var(--line)'}`,
                  color: positionTab === t ? (POSITION_COLOR[t] ?? 'var(--txt)') : 'var(--dim2)',
                  fontFamily: 'var(--font-num)',
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                {t}
              </button>
            ))}
          </div>
          <div style={{ flex: 'none', padding: '6px 12px', fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)' }}>
            {availableInTab.length} left
          </div>
          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
            {availableInTab.map((r) => {
              const expanded = expandedRowId === r.id;
              const delta = r.deltaVsConsensus.kind === 'present' ? r.deltaVsConsensus.value : null;
              const deltaColor = delta === null ? 'var(--dim2)' : delta > 2 ? 'var(--up)' : delta < -2 ? 'var(--down)' : 'var(--dim2)';
              const avail =
                nextUserPick !== null
                  ? computeLiveAvailability({ data, league, row: r, targetPick: nextUserPick, picks: draft.picks, rowsById })
                  : null;
              return (
                <div key={r.id} style={{ borderBottom: '1px solid var(--line)' }}>
                  <div
                    onClick={() => openDetail(r)}
                    style={{ display: 'flex', alignItems: 'center', gap: 9, padding: '6px 12px', cursor: 'pointer' }}
                  >
                    <span className="num" style={{ fontSize: 11, color: 'var(--dim2)', width: 22, textAlign: 'right' }}>
                      <Value cell={r.overallRank} render={integer} />
                    </span>
                    <span style={{ fontWeight: 600, fontSize: 13, flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.name.kind === 'present' ? r.name.value : ''}
                    </span>
                    <span style={{ fontSize: 11, letterSpacing: '.045em', fontWeight: 600, color: POSITION_COLOR[r.raw.position], width: 30 }}>
                      {r.raw.position}
                    </span>
                    <span style={{ fontSize: 10, letterSpacing: '.045em', color: 'var(--dim2)', width: 26 }}>{r.raw.team}</span>
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        setExpandedRowId(expanded ? null : r.id);
                      }}
                      title="Why this rank -- click to expand"
                      className="num"
                      style={{ fontSize: 11, fontWeight: 600, color: deltaColor, width: 30, textAlign: 'right', cursor: 'pointer' }}
                    >
                      {delta === null ? '—' : delta > 2 ? `▲${integer(delta)}` : delta < -2 ? `▼${integer(Math.abs(delta))}` : '·'}
                    </span>
                    {avail ? (
                      <span
                        className="num"
                        title={
                          avail.live !== null
                            ? 'baseline → live availability at your next pick'
                            : `live not yet computed -- ${avail.picksLogged} of ${avail.picksRequired} picks logged`
                        }
                        style={{ fontSize: 10, width: 58, textAlign: 'right', color: 'var(--dim2)' }}
                      >
                        <Value cell={avail.baseline} render={percent} />
                        {avail.live !== null ? (
                          <span style={{ color: 'var(--acc)' }}> → {percent(avail.live)}</span>
                        ) : (
                          // Narrow-cell not-computed treatment (design-system/AUDIT.md
                          // RETROFIT-1): "--" here, the reason in the title above, never
                          // the baseline silently standing in for a live value that was
                          // never computed.
                          <span style={{ color: 'var(--dim2)' }}> → —</span>
                        )}
                      </span>
                    ) : null}
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        if (r.name.kind === 'present') toggleWatch(r.name.value);
                      }}
                      title="Star to track availability on your next pick"
                      style={{
                        fontSize: 11,
                        color: r.name.kind === 'present' && watchlist.includes(r.name.value) ? 'var(--down)' : 'var(--dim2)',
                        cursor: 'pointer',
                      }}
                    >
                      {r.name.kind === 'present' && watchlist.includes(r.name.value) ? '★' : '☆'}
                    </span>
                    <span
                      onClick={(e) => {
                        e.stopPropagation();
                        recordPick(r.id, r.name.kind === 'present' ? r.name.value : '');
                      }}
                      title="Mark taken"
                      className="num"
                      style={{ fontSize: 10, color: 'var(--dim2)', border: '1px solid var(--line)', padding: '0 4px' }}
                    >
                      ✕
                    </span>
                  </div>
                  {expanded ? (
                    <div style={{ padding: '0 12px 10px 43px', display: 'flex', flexDirection: 'column', gap: 3 }}>
                      {r.replacementLevelsComponent.kind === 'present' ? (
                        <div style={{ fontSize: 11, color: 'var(--dim)' }}>
                          Replacement levels: <span className="num">{signed(r.replacementLevelsComponent.value)}</span>{' '}
                          <span style={{ color: 'var(--dim2)' }}>({r.replacementLevelsComponent.path})</span>
                        </div>
                      ) : null}
                      {r.scoringAndVbdComponent.kind === 'present' ? (
                        <div style={{ fontSize: 11, color: 'var(--dim)' }}>
                          Scoring and VBD method: <span className="num">{signed(r.scoringAndVbdComponent.value)}</span>{' '}
                          <span style={{ color: 'var(--dim2)' }}>({r.scoringAndVbdComponent.path})</span>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ minHeight: 0, overflowY: 'auto', borderRight: '1px solid var(--line)', background: 'var(--panel)' }}>
          {draftComplete ? (
            <div style={{ padding: 14, color: 'var(--dim)' }}>Draft complete.</div>
          ) : userOnClock ? (
            <div style={{ padding: 14 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '9px 12px',
                  background: 'var(--live)',
                  color: '#0a0d12',
                  fontWeight: 700,
                  letterSpacing: '.06em',
                  fontSize: 15,
                }}
              >
                YOU'RE ON THE CLOCK — PICK {currentPick}
              </div>
              <div style={{ marginTop: 12, fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
                RECOMMENDED (unvalidated stopgap score, not a backtested model)
              </div>
              <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {recommended.map(({ row, score }, i) => (
                  <div
                    key={row.id}
                    style={{
                      padding: '10px 12px',
                      border: i === 0 ? '1px solid var(--acc)' : '1px solid var(--line)',
                      background: 'var(--panel2)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 9 }}>
                      <span onClick={() => openDetail(row)} style={{ fontWeight: 600, fontSize: i === 0 ? 20 : 15, cursor: 'pointer' }}>
                        {row.name.kind === 'present' ? row.name.value : ''}
                      </span>
                      <span style={{ fontSize: 12, letterSpacing: '.045em', color: POSITION_COLOR[row.raw.position] }}>
                        {row.raw.position}
                      </span>
                      <span style={{ fontSize: 11, letterSpacing: '.045em', color: 'var(--dim2)' }}>
                        {row.raw.team} · BYE{' '}
                        <span className="num">
                          <Value cell={row.byeWeek} render={integer} />
                        </span>
                      </span>
                      <span style={{ flex: 1 }} />
                      <span style={{ fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)' }}>
                        score {decimal(score)}
                      </span>
                      <button
                        onClick={() => recordPick(row.id, row.name.kind === 'present' ? row.name.value : '')}
                        style={{ padding: '4px 10px', background: 'var(--acc)', border: 0, color: '#08120c', fontWeight: 700, fontSize: 12 }}
                      >
                        Draft
                      </button>
                    </div>
                    <div style={{ marginTop: 6, fontSize: 12, color: 'var(--dim)' }}>
                      <Value cell={row.projectedPoints} render={decimal} /> proj pts · VBD{' '}
                      <Value cell={row.vbd} render={decimal} />
                      {unfilledPositions.has(row.raw.position) ? ' · fills an open starting slot' : ''}
                    </div>
                  </div>
                ))}
                {recommended.length === 0 ? (
                  <div style={{ fontSize: 12.5, color: 'var(--dim2)' }}>Nothing left with a projection to score.</div>
                ) : null}
              </div>
            </div>
          ) : (
            <div style={{ padding: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                <span style={{ fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>POSITION SCARCITY</span>
                <span style={{ flex: 1, height: 1, background: 'var(--line)' }} />
                <span className="num" style={{ fontSize: 10, color: 'var(--dim2)' }}>
                  vs. expected by pick {integer(currentPick)}
                </span>
              </div>
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 9 }}>
                {scarcityList.map((s) => {
                  const pct = s.total > 0 ? s.remaining / s.total : 0;
                  const warning = depletionWarning(s, nextUserPick);
                  return (
                    <div key={s.pos}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '.045em', color: POSITION_COLOR[s.pos], width: 30 }}>
                          {s.pos}
                        </span>
                        <span style={{ flex: 1, height: 10, background: 'var(--line)', position: 'relative' }}>
                          <span
                            style={{
                              position: 'absolute',
                              inset: 0,
                              width: `${Math.round(pct * 100)}%`,
                              background: POSITION_COLOR[s.pos],
                              opacity: 0.85,
                            }}
                          />
                        </span>
                        <span className="num" style={{ fontSize: 11, color: 'var(--dim)', width: 74, textAlign: 'right' }}>
                          {s.remaining} / {s.total} left
                        </span>
                        <span
                          className="num"
                          style={{ fontSize: 11, width: 44, textAlign: 'right', color: s.pace > 0 ? 'var(--down)' : 'var(--dim2)' }}
                        >
                          {signed(s.pace)}
                        </span>
                      </div>
                      {warning ? (
                        <div style={{ marginTop: 4, marginLeft: 40, padding: '6px 9px', borderLeft: '2px solid var(--down)', background: 'var(--panel2)', fontSize: 11.5, color: 'var(--dim)' }}>
                          {warning}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>

              <div style={{ marginTop: 20, display: 'flex', gap: 4 }}>
                <button
                  aria-pressed={railTab === 'queue'}
                  onClick={() => setRailTab('queue')}
                  style={{ flex: 1, padding: '5px 0', background: railTab === 'queue' ? 'var(--panel2)' : 'transparent', border: `1px solid ${railTab === 'queue' ? 'var(--line2)' : 'var(--line)'}`, fontSize: 11.5, fontWeight: 600, color: railTab === 'queue' ? 'var(--txt)' : 'var(--dim2)' }}
                >
                  Queue ({draft.queue.length})
                </button>
                <button
                  aria-pressed={railTab === 'watch'}
                  onClick={() => setRailTab('watch')}
                  style={{ flex: 1, padding: '5px 0', background: railTab === 'watch' ? 'var(--panel2)' : 'transparent', border: `1px solid ${railTab === 'watch' ? 'var(--line2)' : 'var(--line)'}`, fontSize: 11.5, fontWeight: 600, color: railTab === 'watch' ? 'var(--txt)' : 'var(--dim2)' }}
                >
                  Watchlist ({watchlist.length})
                </button>
              </div>
              <div style={{ marginTop: 4, fontSize: 10, color: 'var(--dim2)' }}>
                {railTab === 'queue'
                  ? 'Draft-scoped, self-pruning: a queued player drops off the moment anyone drafts him.'
                  : 'Account-wide: persists across leagues and seasons.'}
              </div>

              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {(railTab === 'queue' ? queueRows : watchRows).length === 0 ? (
                  <div style={{ fontSize: 12.5, color: 'var(--dim2)' }}>
                    {railTab === 'queue'
                      ? 'Nothing queued. Add a player from the available list or their detail panel.'
                      : 'No players starred. Star a player from the available list to track them here.'}
                  </div>
                ) : (
                  (railTab === 'queue' ? queueRows : watchRows).map(({ row, avail }) => (
                    <AvailabilityRow key={row.id} row={row} avail={avail} />
                  ))
                )}
              </div>

              <div style={{ marginTop: 20, padding: '11px 12px', border: '1px solid var(--line)', background: 'var(--panel2)' }}>
                <div style={{ fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>NEXT DECISION</div>
                <div style={{ marginTop: 7, fontSize: 13, lineHeight: 1.55, color: 'var(--dim)' }}>
                  {nextUserPick
                    ? `You pick at ${nextUserPick} (round ${roundOfPick(nextUserPick, teams)}), ${
                        picksUntilYou ?? 0
                      } picks from now.`
                    : 'No further picks left in this draft.'}
                </div>
              </div>
            </div>
          )}
        </div>

        <div style={{ minHeight: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
                MY ROSTER
              </span>
              <span style={{ flex: 1 }} />
              <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)' }}>
                {userPicks.length} / {rosterSlots.length}
              </span>
            </div>
            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 2 }}>
              {rosterSlots.map((s, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '4px 6px',
                    background: s.row ? 'var(--panel2)' : 'transparent',
                    borderLeft: `2px solid ${s.row ? (POSITION_COLOR[s.row.raw.position] ?? 'var(--line2)') : 'var(--line)'}`,
                  }}
                >
                  <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)', width: 34 }}>{s.slot}</span>
                  <span
                    style={{
                      flex: 1,
                      fontSize: 12.5,
                      color: s.row ? 'var(--txt)' : 'var(--dim2)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {s.row ? (s.row.name.kind === 'present' ? s.row.name.value : '') : '—'}
                  </span>
                  {s.row ? (
                    <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)' }}>
                      <Value cell={s.row.byeWeek} render={integer} />
                    </span>
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
              MY PICKS
            </div>
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {userPicks.map((p) => (
                <span
                  key={p.overallPick}
                  title={p.playerName}
                  style={{ fontFamily: 'var(--font-num)', fontSize: 11, padding: '3px 7px', border: '1px solid var(--line2)', background: 'var(--panel2)' }}
                >
                  {p.overallPick}
                </span>
              ))}
              {userPicks.length === 0 ? <span style={{ fontSize: 12, color: 'var(--dim2)' }}>None yet.</span> : null}
            </div>
          </div>

          <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '10px 12px 6px', fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
              DRAFT LOG
            </div>
            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '0 12px 12px' }}>
              {draft.picks
                .slice()
                .reverse()
                .map((p) => (
                  <div
                    key={p.overallPick}
                    onClick={() => removePick(p.overallPick)}
                    title="Click to undo / correct"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 7,
                      padding: '5px 6px',
                      marginLeft: -6,
                      borderLeft: `2px solid ${p.teamSlot === userSlot ? 'var(--acc)' : 'var(--line2)'}`,
                      cursor: 'pointer',
                      fontFamily: 'var(--font-num)',
                      fontSize: 11,
                    }}
                  >
                    <span style={{ color: 'var(--dim2)', width: 26 }}>{p.overallPick}</span>
                    <span style={{ color: p.teamSlot === userSlot ? 'var(--acc)' : 'var(--dim2)', width: 52 }}>
                      team {p.teamSlot}
                    </span>
                    <span
                      style={{
                        flex: 1,
                        color: 'var(--txt)',
                        fontFamily: 'var(--font-ui)',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {p.playerName}
                    </span>
                  </div>
                ))}
              {draft.picks.length === 0 ? <div style={{ fontSize: 12, color: 'var(--dim2)' }}>No picks logged yet.</div> : null}
            </div>
          </div>
        </div>
      </div>

      {detailRow ? (
        <PlayerDetail
          row={detailRow}
          rows={rows}
          data={data}
          league={league}
          picks={draft.picks}
          watchlist={watchlist}
          onToggleWatch={toggleWatch}
          queue={draft.queue}
          onToggleQueue={toggleQueue}
          onMarkTaken={(id, name) => {
            recordPick(id, name);
            setDetailRow(null);
            onOpenPlayer?.(null);
          }}
          onClose={() => {
            setDetailRow(null);
            onOpenPlayer?.(null);
          }}
        />
      ) : null}
    </div>
  );
}

/** One queue or watchlist row: baseline and live shown together, per §5.2's
 *  display contract -- never one number replacing the other. */
function AvailabilityRow({ row, avail }: { row: BoardRow; avail: LiveAvailabilityResult }) {
  const pct = avail.live ?? (avail.baseline.kind === 'present' ? avail.baseline.value : null);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ width: 130, fontSize: 12.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {row.name.kind === 'present' ? row.name.value : ''}
      </span>
      <span style={{ flex: 1, height: 8, background: 'var(--line)', position: 'relative' }}>
        <span
          style={{
            position: 'absolute',
            inset: 0,
            width: pct === null ? '0%' : `${Math.round(pct * 100)}%`,
            background: 'var(--acc)',
          }}
        />
      </span>
      <span className="num" style={{ fontSize: 11, width: 70, textAlign: 'right', color: 'var(--dim)' }}>
        <Value cell={avail.baseline} render={percent} />
        {avail.live !== null ? <span style={{ color: 'var(--acc)' }}> → {percent(avail.live)}</span> : null}
      </span>
    </div>
  );
}
