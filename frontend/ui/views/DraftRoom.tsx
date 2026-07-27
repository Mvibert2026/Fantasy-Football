import { useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import type { BoardRow } from '../data/board';
import {
  currentOverallPick,
  isSlotOnClock,
  loadDraftState,
  nextPickForSlot,
  pickNumbersForSlot,
  pruneQueue,
  roundOfPick,
  saveDraftState,
  takenPlayerIds,
  teamSlotAtPick,
  toDraftLog,
  type DraftPickRecord,
  type DraftState,
  type EntryMode,
} from '../data/draft';
import { computeLiveAvailability, dotsFilled, freqText, type LiveAvailabilityResult } from '../data/liveAvailability';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { rankByRecommendation } from '../data/recommendation';
import {
  depletionWarning,
  orderByUrgency,
  paceLabel,
  positionScarcity,
  tierDepletionLine,
  under50Line,
} from '../data/scarcity';
import { useWatchlist } from '../data/useWatchlist';
import { PlayerDetail } from '../components/PlayerDetail';
import { Value } from '../components/Value';
import { decimal, integer, interval as intervalText, percent, signed } from '../lib/format';

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

// Thread 058 section A item 4: DEF is a fifth scarcity row, matching the
// design's five positions. board.json carries zero DEF players (ADR-039, no
// DST data ingested) -- positionScarcity's `dataAvailable` gate renders that
// honestly (see scarcity.ts), it does not fabricate a DEF board.
const SCARCITY_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'DEF'] as const;

/** Thread 049 item 5: a placeholder pick used by "Auto-fill to my pick" (see
 *  autoFillToMyPick below) for opponent turns the user hasn't logged. Never a
 *  real name -- unlike the design mockup's `simToMe`, this build does not
 *  assign a real board player to a fabricated pick, because doing so would
 *  falsely mark that player unavailable for every availability/scarcity
 *  computation downstream and would be indistinguishable from a real logged
 *  pick in "Export draft log". playerId stays null (so takenPlayerIds never
 *  counts it) and this exact string is the only thing that marks it synthetic. */
const AUTO_FILL_PLACEHOLDER = '(auto-filled — unknown pick)';

/**
 * Thread 049 item 2: the RECOMMENDED card's "honest range" on *points*, not
 * VBD -- a deliberate, documented derivation, not a second data source.
 *
 * board.json's own `interval` field is explicitly an interval on VBD
 * (`ci_applies_to: "vbd"` on every one of the 378 real rows -- confirmed
 * directly against the export, not assumed), and this file's board.ts sibling
 * carries a comment warning specifically against treating it as a points
 * interval. That warning is respected here, not overridden: this function
 * does not relabel the VBD interval as a points interval. It converts it.
 *
 * VBD is defined as projected points minus a fixed per-position replacement
 * baseline (verified empirically across the full board: `projected_points -
 * vbd` is constant per position to within floating-point noise, e.g. RB
 * 130.99-131.00 across 116 players, WR 124.45-124.46 across 148). That
 * baseline is therefore a real, row-derivable constant -- not fabricated --
 * so adding it back to both ends of the real VBD interval is an exact,
 * traceable unit conversion (an affine shift), the same kind of arithmetic
 * `signed()`/`decimal()` already apply to real fields elsewhere in this app.
 * Every input (interval.low, interval.high, projectedPoints, vbd) is a named
 * board.json field on the same row.
 *
 * This is a considered call, not an uncontested one -- flagged explicitly in
 * the thread 049 reply for backend/PM to override if a real points-scale
 * interval should exist as its own contract field instead.
 */
function pointsRangeFromVbdInterval(row: BoardRow): { low: number; high: number } | null {
  if (row.interval.kind !== 'present' || row.projectedPoints.kind !== 'present' || row.vbd.kind !== 'present') {
    return null;
  }
  const offset = row.projectedPoints.value - row.vbd.value;
  return { low: row.interval.value.low + offset, high: row.interval.value.high + offset };
}

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
 *   - "Auto-fill to my pick" (thread 049 item 5) is built, but deliberately NOT
 *     as the prototype's simToMe (line 2083). simToMe assigns a random real
 *     board player to every skipped opponent pick -- indistinguishable from a
 *     real logged pick in "Export draft log" and silently wrong for every
 *     availability/scarcity number downstream (a fabricated player would read
 *     as actually taken). This build advances the pick clock instead, writing
 *     each skipped pick with playerId: null and the fixed AUTO_FILL_PLACEHOLDER
 *     name -- honestly "someone picked, we don't know who," never a fabricated
 *     identity. See autoFillToMyPick and the thread 049 reply for the tradeoff
 *     this leaves (availability/scarcity through the skipped range won't reflect
 *     the opponents' real picks, since none are invented to stand in for them).
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
  DEF: 'var(--def)',
};

// Thread 058 section B4: DEF added to the position filter, matching the
// design's ALL/QB/RB/WR/TE/DEF row. Selecting it shows an honest "no DEF
// players on this board" empty state (see availableInTab below) rather than a
// silently blank list -- board.json has no DEF rows at all (ADR-039).
const POSITION_TABS = ['ALL', 'QB', 'RB', 'WR', 'TE', 'DEF'] as const;
type PositionTab = (typeof POSITION_TABS)[number];

// Thread 058 section B3: explicit sort controls, matching the design's
// "SORT: Our rank | Consensus | Delta | Proj pts" row. FRONTEND-SPEC.md §7.1
// names exactly these four sorts. Held in component state -- not written to
// ffda_v6 localStorage, since §4.1's persisted-state shape does not include a
// sort/filter field and this session is not extending that contract -- so
// "persisted within session" here means "survives re-renders while the Draft
// Room stays mounted," the same guarantee every other piece of this screen's
// local state gets.
const SORT_TABS = [
  { key: 'rank', label: 'Our rank' },
  { key: 'consensus', label: 'Consensus' },
  { key: 'delta', label: 'Delta' },
  { key: 'proj', label: 'Proj pts' },
] as const;
type SortKey = (typeof SORT_TABS)[number]['key'];

/** Comparator per sort key. `consensus`/`delta`/`proj` fall back to keeping
 *  rank order for any row missing the sort field, rather than throwing it to
 *  the top or bottom of the list arbitrarily. */
function compareBySort(a: BoardRow, b: BoardRow, sort: SortKey): number {
  const rankA = a.overallRank.kind === 'present' ? a.overallRank.value : Number.POSITIVE_INFINITY;
  const rankB = b.overallRank.kind === 'present' ? b.overallRank.value : Number.POSITIVE_INFINITY;
  if (sort === 'consensus') {
    const ca = a.consensusRank.kind === 'present' ? a.consensusRank.value : null;
    const cb = b.consensusRank.kind === 'present' ? b.consensusRank.value : null;
    if (ca !== null && cb !== null) return ca - cb;
    if (ca !== null) return -1;
    if (cb !== null) return 1;
    return rankA - rankB;
  }
  if (sort === 'delta') {
    const da = a.deltaVsConsensus.kind === 'present' ? a.deltaVsConsensus.value : null;
    const db = b.deltaVsConsensus.kind === 'present' ? b.deltaVsConsensus.value : null;
    if (da !== null && db !== null) return db - da; // biggest positive delta (we rank higher than consensus) first
    if (da !== null) return -1;
    if (db !== null) return 1;
    return rankA - rankB;
  }
  if (sort === 'proj') {
    const pa = a.projectedPoints.kind === 'present' ? a.projectedPoints.value : null;
    const pb = b.projectedPoints.kind === 'present' ? b.projectedPoints.value : null;
    if (pa !== null && pb !== null) return pb - pa;
    if (pa !== null) return -1;
    if (pb !== null) return 1;
    return rankA - rankB;
  }
  return rankA - rankB;
}

interface RosterSlot {
  slot: string;
  kind: 'starter' | 'flex' | 'bench' | 'ir';
  position: string | null; // null for FLEX/BN/IR, which accept multiple positions
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
  // Thread 058 section D2: an IR slot, one per league.json:roster.ir (a real
  // field, already typed -- not the design mockup's hardcoded single IR row).
  // Deliberately excluded from the fill-target search below, same as the
  // design reference (docs/design-reference/prototype.dc.html line 2563,
  // `slots.push({slot:"IR",p:null})` -- never filled from the generic pick
  // pool): this build has no injury-designation data to decide which pick
  // belongs on IR, and guessing would be exactly the kind of fabricated
  // assignment Principle #1 forbids. It renders as a permanently-open slot
  // until a real injury signal exists to drive it.
  const ir = data.league.roster.ir ?? 0;
  for (let i = 0; i < ir; i++) slots.push({ slot: 'IR', kind: 'ir', position: null, row: null });
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
  onPickContext,
}: {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
  onOpenPlayer?: (name: string | null) => void;
  /** Thread 058 section C4 audit finding: the assistant dock already renders
   *  on this screen (App.tsx mounts it regardless of mode) -- this was a
   *  placement/content gap, not a missing feature, per the thread's own
   *  instruction to check first. Reports the current overall pick (or null
   *  once the draft is complete / before league config loads) so App.tsx can
   *  compose "Draft · pick 24", matching the design's assistant context line. */
  onPickContext?: (pick: number | null) => void;
}) {
  const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
  const [draft, setDraft] = useState<DraftState>(() => loadDraftState(leagueId));
  const [watchlist, toggleWatch] = useWatchlist();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(0);
  // RETROFIT-5: which of 'typed' / 'pasted' the current query's content came
  // from, so a commit while the query is non-empty logs the right entry_mode.
  // Reset to 'typed' on every commit/clear -- 'pasted' describes only the
  // content currently sitting in the field, not some sticky mode.
  const [queryEntryMode, setQueryEntryMode] = useState<'typed' | 'pasted'>('typed');
  const [positionTab, setPositionTab] = useState<PositionTab>('ALL');
  // Thread 058 section B3: explicit sort controls (Our rank / Consensus /
  // Delta / Proj pts), matching the design's SORT row.
  const [sortMode, setSortMode] = useState<SortKey>('rank');
  const [detailRow, setDetailRow] = useState<BoardRow | null>(null);
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);
  const [railTab, setRailTab] = useState<'queue' | 'watch'>('watch');
  // Thread 049 item 1: the Board/Opponents/Predictions tab shell. Board is
  // this file's existing three-pane content, unchanged. Opponents and
  // Predictions are real, working screens elsewhere in this app (Opponents is
  // shipped in Prep mode; Predictions may or may not exist yet depending on
  // build order this round) -- this shell does not import or duplicate them,
  // since doing so from DraftRoom.tsx would take a dependency on files owned
  // by other sessions working concurrently in this same tree. It states
  // plainly that they are not wired into Draft mode yet, which is true today,
  // rather than fabricating placeholder content or risking a broken import.
  const [hubTab, setHubTab] = useState<'board' | 'opponents' | 'predictions'>('board');
  // Thread 051 items 1-2: the pick-entry suggester (candidate dropdown) is
  // shown/hidden independently of whether candidates exist. Defaults closed --
  // "not on arrival" -- and opens only on a real focus, `/`, typing, or a
  // click back into the field; never merely because the component mounted.
  const [suggesterOpen, setSuggesterOpen] = useState(false);
  // Typed `| null` explicitly (rather than the bare `useRef<HTMLInputElement>(null)`
  // form) so this is a mutable ref -- the callback below writes `.current`
  // itself instead of handing that job to React's own `ref={searchRef}` wiring.
  const searchRef = useRef<HTMLInputElement | null>(null);
  // The wrapper around both the search box and the dropdown -- click-outside
  // detection (thread 051 item 1) treats anything inside this ref as "inside",
  // so clicking a candidate row to commit it never mis-fires as a dismiss.
  const suggesterWrapperRef = useRef<HTMLDivElement | null>(null);
  // Set immediately before the ref-callback's own programmatic focus() call
  // below, and consumed by the input's onFocus handler -- distinguishes "this
  // node was just (re)attached and autofocus fired" from a genuine focus event
  // (a click, or focus regained after a commit), so only the latter opens the
  // suggester. Without this, remounting the input (switching leagues, tabbing
  // away and back) would reopen the popover exactly the way arrival did before
  // this fix, since both go through the same synchronous focus() call.
  const suppressNextFocusOpen = useRef(false);
  // RETROFIT-5 / ML-02: autofocus re-asserted whenever the input node
  // (re)attaches, not a one-shot guard -- a guard that fires once silently
  // stops re-focusing after any remount (switching leagues, switching the top
  // nav away and back), which breaks the field's "never needs the mouse"
  // claim. useCallback keeps this function's identity stable so React only
  // invokes it on real mount/unmount, not on every render.
  const setSearchInputRef = useCallback((el: HTMLInputElement | null) => {
    searchRef.current = el;
    // Synchronous, not deferred behind requestAnimationFrame: React calls a
    // ref callback during the commit phase, after the node is already
    // attached to the document, so it is already focusable here. A rAF
    // wrapper was tried first and measurably failed in a backgrounded/
    // automated browser tab (rAF callbacks are throttled or never fire while
    // a tab isn't the active one) -- direct focus() has no such dependency.
    if (el) {
      suppressNextFocusOpen.current = true;
      try {
        el.focus();
      } catch {
        // Best-effort -- a focus() on a since-unmounted node is a no-op risk,
        // never worth crashing the draft room over.
      }
    }
  }, []);

  // Thread 063 root-cause fix: 051 only guarded the *mount/remount* focus()
  // call above (setSearchInputRef). It missed that recordPick -- called on
  // every single commit, from every commit site (digit shortcut, typed/pasted
  // Enter, clicking a candidate row, and the board row's "mark taken" X for
  // logging an opponent's pick) -- also calls searchRef.current?.focus()
  // directly, for the documented "fast keyboard entry" reason (digits 1-5
  // should keep working pick after pick without reaching for the mouse). That
  // second call site went through the same onFocus handler with no suppress
  // flag set, so the *next* pick's genuine-looking focus event reopened the
  // popover every time -- "opens every pick" is literally what that code did.
  //
  // This helper is the single choke point both call sites should use: it
  // re-focuses (preserving the fast-entry behaviour) while suppressing the
  // *next* focus event from being treated as user intent. Guarded on
  // `document.activeElement` rather than setting the flag unconditionally:
  // if the field already has focus (the common case -- committing via a
  // digit shortcut never blurs the field), calling .focus() again is a
  // browser no-op and fires no focus event at all, so nothing would ever
  // consume the flag and it would leak into suppressing the *next real*
  // click-to-focus later on. Only arm the suppression when we know a focus
  // event will actually fire.
  const refocusSearchWithoutOpening = useCallback(() => {
    const el = searchRef.current;
    if (!el || document.activeElement === el) return;
    suppressNextFocusOpen.current = true;
    try {
      el.focus();
    } catch {
      // Best-effort, same reasoning as setSearchInputRef above.
    }
  }, []);

  function openDetail(row: BoardRow) {
    setDetailRow(row);
    onOpenPlayer?.(row.name.kind === 'present' ? row.name.value : null);
  }

  // Thread 051 item 1: dismiss the suggester on a click anywhere outside the
  // search box + dropdown. Subscribed only while open, so this costs nothing
  // the rest of the time.
  useEffect(() => {
    if (!suggesterOpen) return;
    function onDocMouseDown(e: MouseEvent) {
      if (suggesterWrapperRef.current && !suggesterWrapperRef.current.contains(e.target as Node)) {
        setSuggesterOpen(false);
      }
    }
    document.addEventListener('mousedown', onDocMouseDown);
    return () => document.removeEventListener('mousedown', onDocMouseDown);
  }, [suggesterOpen]);

  // Thread 051 item 2: `/` focuses and opens the suggester from anywhere on
  // the page, matching the field's own "/" affordance -- but not while the
  // user is already typing into some other input/textarea/contenteditable,
  // where `/` should just be a literal character.
  useEffect(() => {
    function onGlobalKeyDown(e: globalThis.KeyboardEvent) {
      if (e.key !== '/') return;
      const target = e.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable) return;
      e.preventDefault();
      setSuggesterOpen(true);
      searchRef.current?.focus();
    }
    document.addEventListener('keydown', onGlobalKeyDown);
    return () => document.removeEventListener('keydown', onGlobalKeyDown);
  }, []);

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
  const availableInTabUnsorted = useMemo(
    () => (positionTab === 'ALL' ? available : available.filter((r) => r.raw.position === positionTab)),
    [available, positionTab],
  );
  // Thread 058 section B3: apply the active sort. Board-rank order is a plain
  // slice (already board-rank ordered), matching every other sort's stable
  // comparator rather than special-casing it.
  const availableInTab = useMemo(
    () => [...availableInTabUnsorted].sort((a, b) => compareBySort(a, b, sortMode)),
    [availableInTabUnsorted, sortMode],
  );

  // Thread 029 (amended to target this screen, not Board.tsx): tier grouping
  // with headers, ported from Board.tsx's own band-divider pattern. Restricted
  // to a single position, same restriction Board.tsx applies and for the same
  // reason -- board.json's tier_label is assigned per position, so under "ALL"
  // consecutive rows from different positions can share a tier string (e.g. both
  // "T2") without describing the same tier, and a band would misrepresent that
  // as one group.
  //
  // Thread 058 section B1 audit finding: the design reference's own ALL-tab
  // tier bands (docs/design-reference/prototype.dc.html ~line 3424, `useG =
  // S.filter==="ALL"`) do NOT mix each position's own tier under one header --
  // they switch to a distinct `p.gtier` ("global tier"), computed once by
  // walking the whole board sorted by score and cutting a new tier on a >4.5
  // point score gap (min bucket size 2, max 9). That is a real, separate
  // statistical clustering decision -- exactly the kind of judgment this
  // codebase already treats as backend's to make and export (board.json ships
  // `tier`/`tier_label`, always per-position -- confirmed directly against the
  // real export: QB tier 1 stops at positional rank 2 while RB tier 1 runs to
  // positional rank 4, so a QB1 and an RB4 sharing a tier LABEL are not
  // describing the same value tier). Fabricating a global-tier bucketing
  // algorithm client-side, on numbers never vetted for that use, would be
  // exactly the kind of invented derived value Principle #1 forbids. So bands
  // stay restricted to a single position tab until backend exports a real
  // `global_tier` field (flagged to backend/PM in the thread reply) -- this is
  // a correction to the thread's read of section B1, not a gap in this build.
  const bandsEnabled = positionTab !== 'ALL' && sortMode === 'rank';
  const boardItems = useMemo(() => {
    const items: Array<{ kind: 'band'; tier: string; count: number } | { kind: 'row'; row: BoardRow }> = [];
    if (bandsEnabled) {
      let lastTier: string | null = null;
      for (const row of availableInTab) {
        const tier = row.tierLabel.kind === 'present' ? row.tierLabel.value : null;
        if (tier !== null && tier !== lastTier) {
          lastTier = tier;
          const count = availableInTab.filter((r) => r.tierLabel.kind === 'present' && r.tierLabel.value === tier).length;
          items.push({ kind: 'band', tier, count });
        }
        items.push({ kind: 'row', row });
      }
    } else {
      for (const row of availableInTab) items.push({ kind: 'row', row });
    }
    return items;
  }, [availableInTab, bandsEnabled]);

  const currentPick = currentOverallPick(draft.picks);
  const currentRound = teams > 0 ? roundOfPick(currentPick, teams) : 0;
  const onClockSlot = teams > 0 ? teamSlotAtPick(currentPick, teams) : 0;
  const userOnClock = teams > 0 && isSlotOnClock(draft.picks, teams, userSlot);
  const nextUserPick = teams > 0 ? nextPickForSlot(draft.picks, teams, userSlot, rounds) : null;
  const picksUntilYou = userOnClock ? 0 : nextUserPick !== null ? nextUserPick - currentPick : null;
  const draftComplete = teams > 0 && rounds > 0 && currentPick > teams * rounds;

  // Thread 058 section C4: report the live pick number up to App.tsx for the
  // assistant dock's context line ("Draft · pick 24"). Null once the draft is
  // complete, or before league config resolves, rather than reporting a stale
  // pick number that no longer describes anything real.
  useEffect(() => {
    onPickContext?.(teams > 0 && !draftComplete ? currentPick : null);
    return () => onPickContext?.(null);
  }, [onPickContext, teams, draftComplete, currentPick]);

  function persist(next: DraftState) {
    setDraft(next);
    saveDraftState(next);
  }

  function recordPick(playerId: number | null, playerName: string, entryMode: EntryMode) {
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
      entryMode,
    };
    persist({ ...draft, picks: [...draft.picks, entry], queue: pruneQueue(draft.queue, playerId) });
    setQuery('');
    setSelected(0);
    setQueryEntryMode('typed');
    // Thread 063: the rule states the panel "closes on ... commit" -- if it
    // happened to be open (a genuine focus/typing session that ended in a
    // commit), a commit must close it, not leave it standing open showing the
    // next pick's shortlist uninvited. Independent of the reopen-prevention
    // fix below: this is "commit closes it", that one is "commit must never
    // *open* it".
    setSuggesterOpen(false);
    // Was a bare `searchRef.current?.focus()` -- see
    // refocusSearchWithoutOpening's comment for why that reopened the
    // suggester on every single commit.
    refocusSearchWithoutOpening();
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

  /**
   * Thread 049 item 5: advance past every pick between now and the user's next
   * turn in one action. See AUTO_FILL_PLACEHOLDER's doc comment for why this
   * deliberately does NOT assign real player identities to the skipped picks
   * the way the design mockup's `simToMe` does -- each filler pick is written
   * with playerId: null and a fixed placeholder name, so it never counts as a
   * real taken player and is never mistakable for a real logged pick.
   *
   * Written as a single persist() call over the whole batch, per Principle #3
   * -- there is no intermediate render where only some of the skipped picks
   * exist, which would show a briefly-wrong pick clock and roster state.
   */
  function autoFillToMyPick() {
    if (draftComplete || userOnClock || nextUserPick === null) return;
    const start = currentOverallPick(draft.picks);
    if (start >= nextUserPick) return;
    const now = new Date().toISOString();
    const fillers: DraftPickRecord[] = [];
    for (let n = start; n < nextUserPick; n++) {
      fillers.push({
        overallPick: n,
        round: roundOfPick(n, teams),
        teamSlot: teamSlotAtPick(n, teams),
        playerId: null,
        playerName: AUTO_FILL_PLACEHOLDER,
        timestamp: now,
        entryMode: null,
      });
    }
    if (fillers.length === 0) return;
    persist({ ...draft, picks: [...draft.picks, ...fillers] });
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
      .slice(0, 5); // RETROFIT-5: 5 slots, matching the digit keys that commit them.
  }, [query, available]);

  /**
   * RETROFIT-5's default (no-query) shortlist: top 5 still-available players by
   * real board rank (`overallRank`, board.json's own field -- never a fabricated
   * "probability this player goes next," which this codebase has no model for;
   * see the entry_mode doc comment in ui/data/draft.ts for why that departure
   * from the Mock Lab reference is deliberate).
   *
   * Board-rank order, top of list first -- NOT shuffled (thread 051 item 3,
   * reversing this build's own earlier choice). Randomising the shortlist is a
   * real, deliberate mitigation for calibration contamination, but this screen
   * does not collect calibration data; the Draft room is a user racing a pick
   * clock to log a real draft, and forcing them to read all five names every
   * pick to defeat a bias that isn't being measured here is pure friction. The
   * rule going forward: randomise where calibration data is collected (Mock
   * Lab, gated separately by ADR-D/thread 034), order by BPA everywhere else.
   */
  const defaultCandidateIds = useMemo(() => {
    return available
      .map((r) => ({ row: r, rank: r.overallRank.kind === 'present' ? r.overallRank.value : null }))
      .filter((x): x is { row: BoardRow; rank: number } => x.rank !== null)
      .sort((a, b) => a.rank - b.rank)
      .slice(0, 5)
      .map((x) => x.row.id);
  }, [available]);
  const defaultCandidates = useMemo(
    () => defaultCandidateIds.map((id) => rowsById.get(id)).filter((r): r is BoardRow => !!r),
    [defaultCandidateIds, rowsById],
  );

  const candidates = query.trim() ? searchResults : defaultCandidates;

  function commitCandidate(row: BoardRow, mode: EntryMode) {
    if (row.name.kind === 'present') recordPick(row.id, row.name.value, mode);
  }

  function onSearchKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    // RETROFIT-5: digits 1-5 commit the corresponding candidate directly,
    // whichever list is showing -- the common case is one keystroke, no
    // typing at all.
    if (/^[1-5]$/.test(e.key)) {
      const i = Number(e.key) - 1;
      const hit = candidates[i];
      if (hit) {
        e.preventDefault();
        commitCandidate(hit, 'shortcut');
      }
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelected((s) => Math.min(candidates.length - 1, s + 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelected((s) => Math.max(0, s - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const hit = candidates[selected];
      if (hit && hit.name.kind === 'present') {
        // Committing the highlighted row from the un-typed default shortlist is
        // still a shortcut (no search performed); committing a typed/pasted
        // search match is not.
        commitCandidate(hit, query.trim() ? queryEntryMode : 'shortcut');
      } else if (query.trim()) {
        // No board match -- log the raw text (a kicker, a DST, a rookie off this
        // board). Real data entry beats refusing to record what actually happened.
        recordPick(null, query.trim(), queryEntryMode);
      }
    } else if (e.key === 'Escape') {
      // Thread 051 item 1: Escape both clears the field (pre-existing) and
      // dismisses the suggester (was previously advertised in the help row but
      // not actually wired to close anything -- confirmed missing this session).
      setQuery('');
      setSelected(0);
      setQueryEntryMode('typed');
      setSuggesterOpen(false);
    } else if (e.key === 'Backspace' && !query) {
      // RETROFIT-5: Backspace on an empty field undoes the last pick -- the
      // field itself has nothing left to delete, so the key is free to mean
      // something else.
      e.preventDefault();
      const last = draft.picks[draft.picks.length - 1];
      if (last) removePick(last.overallPick);
    }
  }

  const userPicks = useMemo(() => draft.picks.filter((p) => p.teamSlot === userSlot), [draft.picks, userSlot]);
  // Thread 049 item 4: MY PICKS shows the full planned sequence
  // (league.json:pick_sequence, real, not derived), current pick highlighted --
  // not just the picks already made, which is all the app showed before.
  const fullPickSequence = league.pickSequence.kind === 'present' ? league.pickSequence.value : [];
  const userPicksByOverall = useMemo(() => new Map(userPicks.map((p) => [p.overallPick, p])), [userPicks]);
  const rosterSlots = useMemo(
    () => buildRosterSlots(userPicks, league, data, rowsById),
    [userPicks, league, data, rowsById],
  );
  const unfilledPositions = useMemo(
    () => new Set(rosterSlots.filter((s) => s.kind === 'starter' && s.row === null).map((s) => s.position as string)),
    [rosterSlots],
  );

  // Thread 049 item 3: roster slot chips (`QB 0/1 · RB 0/2 · ...`) -- filled/
  // total per slot type, aggregated from the same real rosterSlots this file
  // already builds for the MY ROSTER list, not a second source of truth.
  // Fixed display order (QB/RB/WR/TE/FLEX/DEF, then BN) rather than
  // league.json:roster.starters' own key order, which is a presentation
  // choice, not a data one -- the counts themselves are exactly rosterSlots'.
  const ROSTER_CHIP_ORDER = ['QB', 'RB', 'WR', 'TE', 'FLEX', 'DEF'];
  const rosterChips = useMemo(() => {
    const counts = new Map<string, { filled: number; total: number }>();
    for (const s of rosterSlots) {
      // Thread 058 section D2: IR is excluded from the requirement chips,
      // matching the design's own checklist exactly (prototype.dc.html line
      // 3778, `checklist` builds from a fixed {QB,RB,WR,TE,FLEX,DEF,BN} map
      // with no IR key) -- IR appears in the roster slot list below instead.
      // Without this guard, IR's null `position` would fall through to the
      // 'BN' bucket and silently inflate the bench requirement.
      if (s.kind === 'ir') continue;
      const key = s.kind === 'bench' ? 'BN' : s.kind === 'flex' ? 'FLEX' : (s.position ?? 'BN');
      const c = counts.get(key) ?? { filled: 0, total: 0 };
      c.total += 1;
      if (s.row) c.filled += 1;
      counts.set(key, c);
    }
    const order = [...ROSTER_CHIP_ORDER, 'BN'];
    return order.filter((k) => counts.has(k)).map((k) => ({ label: k, ...counts.get(k)! }));
  }, [rosterSlots]);

  // The overall pick number strictly after the current one where this user's
  // slot is next on the clock -- distinct from `nextUserPick` above, which
  // equals `currentPick` itself while the user is on the clock right now.
  // Needed for "WHAT YOU GIVE UP" (thread 049 item 2): the survival
  // probability that matters for a pick being made *right now* is at the
  // user's *following* turn, not this one.
  const followingUserPick = useMemo(
    () => (teams > 0 ? (pickNumbersForSlot(teams, userSlot, rounds).find((p) => p > currentPick) ?? null) : null),
    [teams, userSlot, rounds, currentPick],
  );

  const recommended = useMemo(() => {
    if (!userOnClock) return [];
    return rankByRecommendation(available, currentRound, unfilledPositions).slice(0, 6);
  }, [userOnClock, available, currentRound, unfilledPositions]);

  /**
   * Thread 049 item 2: the RECOMMENDED card's reason and "WHAT YOU GIVE UP"
   * text, plus the honest points range. All of it built from fields already on
   * BoardRow -- nothing here is a second data source.
   *
   * Survival percentages use `followingUserPick` (the user's turn AFTER this
   * one), not `nextUserPick` (which equals the current pick while on the
   * clock) -- "will this player survive to my NEXT turn" is the actual
   * question the give-up trade is answering. Null when no such pick remains
   * (last user pick of the draft) or when live availability isn't computed
   * yet for one/both players -- rendered as an honest gap, never a guess.
   */
  const recommendationDetail = useMemo(() => {
    if (!userOnClock || recommended.length === 0) return null;
    const top = recommended[0]!;
    const alt = recommended[1] ?? null;

    const availAt = (row: BoardRow) =>
      followingUserPick !== null
        ? computeLiveAvailability({ data, league, row, targetPick: followingUserPick, picks: draft.picks, rowsById })
        : null;
    const pctOf = (a: LiveAvailabilityResult | null) =>
      a ? (a.live ?? (a.baseline.kind === 'present' ? a.baseline.value : null)) : null;

    const topAvail = availAt(top.row);
    const topPct = pctOf(topAvail);

    const survivalFragment = (pct: number | null) =>
      pct !== null && followingUserPick !== null ? `, and only ${percent(pct)} likely to survive to your pick at ${followingUserPick}.` : '.';

    let reason: string;
    if (top.row.projectedPoints.kind !== 'present') {
      reason = `Best available on our board at rank ${top.row.overallRank.kind === 'present' ? integer(top.row.overallRank.value) : '—'}. ${top.row.projectedPoints.reason}`;
    } else {
      const topTier = top.row.tierLabel;
      const tierLeft =
        topTier.kind === 'present'
          ? available.filter((r) => r.raw.position === top.row.raw.position && r.tierLabel.kind === 'present' && r.tierLabel.value === topTier.value)
              .length
          : null;
      if (tierLeft !== null && tierLeft <= 2 && top.row.raw.tier <= 2) {
        reason = `Only ${tierLeft} tier-${top.row.raw.tier} ${top.row.raw.position} left on the board${survivalFragment(topPct)}`;
      } else {
        reason = `Best value by VBD — ${integer(top.row.vbd.kind === 'present' ? top.row.vbd.value : 0)} points over replacement in your format${survivalFragment(topPct)}`;
      }
    }

    const pointsRange = pointsRangeFromVbdInterval(top.row);

    let giveUp: string | null = null;
    if (alt) {
      const altAvail = availAt(alt.row);
      const altPct = pctOf(altAvail);
      const altName = alt.row.name.kind === 'present' ? alt.row.name.value : 'The next option';
      const topName = top.row.name.kind === 'present' ? top.row.name.value : 'This player';

      let valueClause: string;
      if (alt.row.vbd.kind === 'present' && top.row.vbd.kind === 'present') {
        const dv = Math.round(alt.row.vbd.value - top.row.vbd.value);
        valueClause = `${altName} is ${integer(alt.row.vbd.value)} over replacement vs ${topName}'s ${integer(top.row.vbd.value)} — you ${
          dv > 0 ? `give up ${dv}` : `gain ${Math.abs(dv)}`
        } points of value today.`;
      } else if (alt.row.vbd.kind === 'present') {
        valueClause = `${altName} has a VBD value and ${topName} does not, so the two are not directly comparable on points.`;
      } else {
        valueClause = `Neither has a VBD value yet, so the comparison is board rank only.`;
      }

      let survivalClause: string;
      if (followingUserPick === null) {
        survivalClause = ' No further pick of yours remains this draft to compare survival odds against.';
      } else if (topPct !== null && altPct !== null) {
        survivalClause = ` ${topName} is ${percent(topPct)} to still be there at ${followingUserPick} and ${altName} is ${percent(altPct)}. That difference, not the point gap, is the reason for the order.`;
      } else {
        survivalClause = ' Survival odds at your next pick are not yet computed for one or both players (see the availability cell on their rows for why).';
      }

      giveUp = `${altName} (${alt.row.raw.position}) is the next best. ${valueClause}${survivalClause}`;
    }

    return { top, alt, reason, pointsRange, giveUp };
  }, [userOnClock, recommended, followingUserPick, data, league, draft.picks, rowsById, available]);

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
      // Thread 058 section A item 5: ordered by urgency rather than a fixed
      // QB/RB/WR/TE/DEF row order -- see orderByUrgency's doc comment in
      // scarcity.ts for the exact tie-break rule and why FRONTEND-SPEC.md
      // doesn't settle this (it doesn't specify a formula either way).
      orderByUrgency(
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

  // Thread 058 section C1: sentence case, boxed tabs sitting on the content
  // panel with a filled active state -- not the all-caps underline strip this
  // screen had before. Matches docs/design-reference/prototype.dc.html's own
  // `dtabs` styling exactly (line ~3241-3244: active = panel2 background +
  // line2 border + weight 600, rounded top corners only, border-bottom:0 so
  // the active tab visually merges into the panel below; a trailing hairline
  // spans the remaining width so inactive tabs still read as "on a rail").
  // The founder named this tab's location/treatment specifically in thread 058.
  const HUB_TABS: Array<{ key: typeof hubTab; label: string }> = [
    { key: 'board', label: 'Board' },
    { key: 'opponents', label: 'Opponents' },
    { key: 'predictions', label: 'Predictions' },
  ];

  return (
    <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          flex: 'none',
          display: 'flex',
          alignItems: 'stretch',
          gap: 2,
          padding: '6px 8px 0',
          background: 'var(--panel)',
          minWidth: 0,
          overflow: 'hidden',
        }}
      >
        {HUB_TABS.map((t) => (
          <button
            key={t.key}
            aria-pressed={hubTab === t.key}
            onClick={() => setHubTab(t.key)}
            style={{
              padding: '6px 14px',
              background: hubTab === t.key ? 'var(--panel2)' : 'transparent',
              borderTop: `1px solid ${hubTab === t.key ? 'var(--line2)' : 'transparent'}`,
              borderLeft: `1px solid ${hubTab === t.key ? 'var(--line2)' : 'transparent'}`,
              borderRight: `1px solid ${hubTab === t.key ? 'var(--line2)' : 'transparent'}`,
              borderBottom: 0,
              borderRadius: 'var(--r-c) var(--r-c) 0 0',
              color: hubTab === t.key ? 'var(--txt)' : 'var(--dim2)',
              fontSize: 12.5,
              fontWeight: hubTab === t.key ? 600 : 400,
            }}
          >
            {t.label}
          </button>
        ))}
        <span style={{ flex: 1, borderBottom: '1px solid var(--line2)' }} />
      </div>

      {hubTab === 'opponents' ? (
        <div style={{ padding: 20 }}>
          <div className="empty">
            <strong>Opponents is not wired into Draft mode yet.</strong> It ships as its own screen
            in Prep mode today (rosters.json/opponents.json-backed) -- this tab is a placeholder
            for folding that in, not a duplicate build of it.
          </div>
        </div>
      ) : hubTab === 'predictions' ? (
        <div style={{ padding: 20 }}>
          <div className="empty">
            <strong>Predictions is not wired into Draft mode yet.</strong>
          </div>
        </div>
      ) : (
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
        <div ref={suggesterWrapperRef} style={{ position: 'relative', flex: 1, maxWidth: 540 }}>
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
              ref={setSearchInputRef}
              value={query}
              onMouseDown={() => {
                // Thread 063: a real click is unambiguous user intent
                // regardless of whether the field already had focus. Browsers
                // do not fire a `focus` event from clicking an element that is
                // already the active one (true here on the very first click
                // after mount, since setSearchInputRef's autofocus already
                // moved focus to this field before the user could click it) --
                // relying on onFocus alone silently no-ops that click. A real
                // mousedown on this element is never fired by this
                // component's own programmatic .focus() calls (JS focus()
                // does not synthesize mouse events), so this is a safe,
                // independent "did the user actually click here" signal, not
                // a second mechanism competing with onFocus's suppress flag.
                setSuggesterOpen(true);
              }}
              onFocus={() => {
                // Thread 051 item 2: open on a real focus -- but not the
                // programmatic autofocus the ref callback just fired on
                // (re)attach, which setSearchInputRef flagged immediately
                // before calling .focus(). That flag is consumed here, once,
                // so every subsequent genuine focus (click, tab back in,
                // refocus after a commit) opens the suggester normally.
                if (suppressNextFocusOpen.current) {
                  suppressNextFocusOpen.current = false;
                  return;
                }
                setSuggesterOpen(true);
              }}
              onChange={(e) => {
                // RETROFIT-5 entry_mode: a native 'insertFromPaste' input event
                // means this change's content arrived via paste, not keystrokes.
                // Not supported in every environment (e.g. jsdom in tests) --
                // falls back to 'typed', the safe default, when absent.
                const inputType = (e.nativeEvent as InputEvent).inputType;
                setQueryEntryMode(inputType === 'insertFromPaste' ? 'pasted' : 'typed');
                setQuery(e.target.value);
                setSelected(0);
                // Thread 051 item 2: typing opens the suggester independently
                // of focus (covers the case where onFocus was suppressed above).
                setSuggesterOpen(true);
              }}
              onKeyDown={onSearchKeyDown}
              placeholder={
                draftComplete
                  ? 'Draft complete'
                  : `Mark pick ${currentPick} (team ${onClockSlot}${userOnClock ? ' — you' : ''}) — 1-5 to commit, or type a name`
              }
              disabled={draftComplete}
              style={{ flex: 1, height: 36, background: 'transparent', border: 0, outline: 'none', fontSize: 14 }}
            />
          </div>
          {!draftComplete && suggesterOpen && candidates.length > 0 ? (
            <div
              data-testid="suggester-dropdown"
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
              {!query.trim() ? (
                <div style={{ padding: '5px 10px', fontFamily: 'var(--font-num)', fontSize: 9.5, letterSpacing: '.08em', color: 'var(--dim2)' }}>
                  TOP 5 BY BOARD RANK, STILL AVAILABLE
                </div>
              ) : null}
              {candidates.map((r, i) => (
                <div
                  key={r.id}
                  data-testid={`candidate-row-${i + 1}`}
                  onClick={() => commitCandidate(r, query.trim() ? queryEntryMode : 'shortcut')}
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
                  <span
                    className="num"
                    style={{ fontSize: 11, fontWeight: 700, color: 'var(--acc)', width: 14, textAlign: 'right' }}
                  >
                    {i + 1}
                  </span>
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
                <span>1-5 commit</span>
                <span>↑↓ navigate</span>
                <span>⏎ mark taken</span>
                <span>⌫ on empty undoes last</span>
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
          onClick={autoFillToMyPick}
          disabled={draftComplete || userOnClock || nextUserPick === null}
          title="Fills opponent picks between now and your next turn with an honest placeholder (not a real player) so you can catch up quickly."
          style={{
            padding: '5px 10px',
            background: 'transparent',
            border: '1px solid var(--line2)',
            color: draftComplete || userOnClock || nextUserPick === null ? 'var(--dim2)' : 'var(--dim)',
            fontSize: 11,
          }}
        >
          Auto-fill to my pick
        </button>
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
          <div
            style={{
              flex: 'none',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              borderBottom: '1px solid var(--line)',
            }}
          >
            <span style={{ fontSize: 9, letterSpacing: '.09em', color: 'var(--dim2)', flex: 'none' }}>SORT</span>
            {SORT_TABS.map((s) => (
              <button
                key={s.key}
                aria-pressed={sortMode === s.key}
                onClick={() => setSortMode(s.key)}
                style={{
                  padding: '3px 8px',
                  background: 'transparent',
                  border: 0,
                  borderBottom: `1px solid ${sortMode === s.key ? 'var(--acc)' : 'transparent'}`,
                  color: sortMode === s.key ? 'var(--txt)' : 'var(--dim2)',
                  fontSize: 11,
                }}
              >
                {s.label}
              </button>
            ))}
            <div style={{ flex: 1 }} />
            <span
              title="Baseline → live-adjusted availability at your next pick"
              style={{ fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)', flex: 'none' }}
            >
              {availableInTab.length} left
            </span>
          </div>
          {positionTab === 'DEF' && availableInTab.length === 0 ? (
            <div style={{ padding: '12px', fontSize: 12.5, color: 'var(--dim2)', lineHeight: 1.5 }}>
              No DEF players on this board. {data.board.def_note}
            </div>
          ) : null}
          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
            {boardItems.map((item) => {
              if (item.kind === 'band') {
                return (
                  <div
                    key={`band-${item.tier}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '5px 12px',
                      background: 'var(--panel2)',
                      borderBottom: '1px solid var(--line)',
                    }}
                  >
                    <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.1em', color: 'var(--dim)' }}>
                      TIER {item.tier.replace(/^T/, '')}
                    </span>
                    <span style={{ flex: 1 }} />
                    <span style={{ fontFamily: 'var(--font-num)', fontSize: 10, color: 'var(--dim2)' }}>
                      {item.count} player{item.count === 1 ? '' : 's'} left
                    </span>
                  </div>
                );
              }
              const r = item.row;
              const expanded = expandedRowId === r.id;
              const delta = r.deltaVsConsensus.kind === 'present' ? r.deltaVsConsensus.value : null;
              const deltaColor = delta === null ? 'var(--dim2)' : delta > 2 ? 'var(--up)' : delta < -2 ? 'var(--down)' : 'var(--dim2)';
              const avail =
                nextUserPick !== null
                  ? computeLiveAvailability({ data, league, row: r, targetPick: nextUserPick, picks: draft.picks, rowsById })
                  : null;
              // Same honesty rule as PlayerDetail's HON-02: only plot the dot array
              // when there is a real number behind it (live or baseline) -- a
              // zero-filled array is visually indistinguishable from a genuine 0%.
              const dotsValue = avail ? avail.live ?? (avail.baseline.kind === 'present' ? avail.baseline.value : null) : null;
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
                    {/* Thread 058 section B2: positional rank (WR12), not bare
                        position -- board.json:positional_label, already a real
                        exported field (confirmed "RB1"/"WR1"-style against the
                        real export), just not rendered on this row before. */}
                    <span style={{ fontSize: 11, letterSpacing: '.045em', fontWeight: 600, color: POSITION_COLOR[r.raw.position], width: 38 }}>
                      <Value cell={r.positionalLabel} render={(v) => v} />
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
                    {dotsValue !== null ? <RowDots value={dotsValue} /> : null}
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
                        recordPick(r.id, r.name.kind === 'present' ? r.name.value : '', 'shortcut');
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
              {recommendationDetail ? (
                <div style={{ marginTop: 8, border: '1px solid var(--acc)', background: 'var(--panel2)' }}>
                  <div style={{ padding: 14 }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 9 }}>
                      <span
                        onClick={() => openDetail(recommendationDetail.top.row)}
                        style={{ fontWeight: 700, fontSize: 22, cursor: 'pointer' }}
                      >
                        {recommendationDetail.top.row.name.kind === 'present' ? recommendationDetail.top.row.name.value : ''}
                      </span>
                      <span style={{ fontFamily: 'var(--font-num)', fontSize: 13, fontWeight: 600, color: POSITION_COLOR[recommendationDetail.top.row.raw.position] }}>
                        {recommendationDetail.top.row.positionalLabel.kind === 'present'
                          ? recommendationDetail.top.row.positionalLabel.value
                          : recommendationDetail.top.row.raw.position}
                      </span>
                      <span style={{ fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)' }}>
                        {recommendationDetail.top.row.raw.team} · BYE{' '}
                        <span className="num">
                          <Value cell={recommendationDetail.top.row.byeWeek} render={integer} />
                        </span>
                      </span>
                    </div>
                    {recommendationDetail.top.row.projectedPoints.kind === 'present' ? (
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 8 }}>
                        <span className="num" style={{ fontSize: 20, fontWeight: 600 }}>
                          {decimal(recommendationDetail.top.row.projectedPoints.value)}
                        </span>
                        <span style={{ fontSize: 11, color: 'var(--dim)' }}>projected pts</span>
                        <span className="num" style={{ fontSize: 11, color: 'var(--dim2)' }}>
                          {recommendationDetail.pointsRange
                            ? `honest range ${intervalText(recommendationDetail.pointsRange.low, recommendationDetail.pointsRange.high)}`
                            : 'range not available for this player'}
                        </span>
                      </div>
                    ) : (
                      <p className="notice" style={{ marginTop: 8, fontSize: 12 }}>
                        {recommendationDetail.top.row.projectedPoints.reason}
                      </p>
                    )}
                    <div style={{ marginTop: 4, fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)' }}>
                      VBD <Value cell={recommendationDetail.top.row.vbd} render={decimal} />
                      {unfilledPositions.has(recommendationDetail.top.row.raw.position) ? ' · fills an open starting slot' : ''}
                    </div>
                    <div style={{ marginTop: 10, fontSize: 13, lineHeight: 1.5, color: 'var(--txt)' }}>
                      {recommendationDetail.reason}
                    </div>
                    <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                      <button
                        onClick={() =>
                          recordPick(
                            recommendationDetail.top.row.id,
                            recommendationDetail.top.row.name.kind === 'present' ? recommendationDetail.top.row.name.value : '',
                            'shortcut',
                          )
                        }
                        style={{ padding: '6px 14px', background: 'var(--acc)', border: 0, color: '#08120c', fontWeight: 700, fontSize: 12 }}
                      >
                        Draft {recommendationDetail.top.row.name.kind === 'present' ? recommendationDetail.top.row.name.value : ''}
                      </button>
                      <button
                        onClick={() => openDetail(recommendationDetail.top.row)}
                        style={{ padding: '6px 12px', background: 'transparent', border: '1px solid var(--line2)', color: 'var(--txt)', fontSize: 12 }}
                      >
                        Why this rank
                      </button>
                    </div>
                  </div>
                  {recommendationDetail.giveUp ? (
                    <div style={{ borderTop: '1px solid var(--line)', padding: '11px 14px', background: 'var(--bg)' }}>
                      <div style={{ fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
                        WHAT YOU GIVE UP
                      </div>
                      <div style={{ marginTop: 6, fontSize: 12.5, lineHeight: 1.5, color: 'var(--dim)' }}>
                        {recommendationDetail.giveUp}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--dim2)' }}>Nothing left with a projection to score.</div>
              )}

              {recommended.length > 1 ? (
                <>
                  <div style={{ marginTop: 16, fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
                    ALTERNATIVES
                  </div>
                  <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {recommended.slice(1).map(({ row, score }) => (
                      <div key={row.id} style={{ padding: '10px 12px', border: '1px solid var(--line)', background: 'var(--panel2)' }}>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: 9 }}>
                          <span onClick={() => openDetail(row)} style={{ fontWeight: 600, fontSize: 15, cursor: 'pointer' }}>
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
                            onClick={() => recordPick(row.id, row.name.kind === 'present' ? row.name.value : '', 'shortcut')}
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
                  </div>
                </>
              ) : null}
            </div>
          ) : (
            <div style={{ padding: 14 }} data-testid="position-scarcity">
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
                  const tierLine = tierDepletionLine(s);
                  const under50 = under50Line(s, nextUserPick);
                  return (
                    <div key={s.pos} data-testid={`scarcity-row-${s.pos}`}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '.045em', color: POSITION_COLOR[s.pos], width: 30 }}>
                          {s.pos}
                        </span>
                        <span style={{ flex: 1, height: 10, background: 'var(--line)', position: 'relative' }}>
                          {s.dataAvailable ? (
                            <span
                              style={{
                                position: 'absolute',
                                inset: 0,
                                width: `${Math.round(pct * 100)}%`,
                                background: POSITION_COLOR[s.pos],
                                opacity: 0.85,
                              }}
                            />
                          ) : null}
                        </span>
                        <span className="num" style={{ fontSize: 11, color: 'var(--dim)', width: 74, textAlign: 'right' }}>
                          {s.dataAvailable ? `${s.remaining} / ${s.total} left` : 'no board data'}
                        </span>
                      </div>
                      {s.dataAvailable ? (
                        <>
                          {/* Thread 058 section A item 1: the sign is now a
                              full phrase ("2 ahead of pace" / "on pace" / "1
                              behind pace"), not a bare +2/±0/-1 -- see
                              paceLabel's doc comment in scarcity.ts for why
                              the design reference itself doesn't demonstrate
                              a fix here (it renders the same bare digit). */}
                          <div
                            style={{ marginTop: 3, marginLeft: 40, fontSize: 11, color: (s.pace ?? 0) > 0 ? 'var(--down)' : 'var(--dim2)' }}
                            title={`gone ${s.gone} vs expected ${s.expected ?? '—'} by pick ${integer(currentPick)} (board.position_remaining · pace vs board.consensus_rank)`}
                          >
                            {paceLabel(s.pace)}
                          </div>
                          {tierLine ? (
                            <div style={{ marginTop: 2, marginLeft: 40, fontSize: 11.5, color: 'var(--down)' }}>{tierLine}</div>
                          ) : null}
                          {under50 ? (
                            <div style={{ marginTop: 2, marginLeft: 40, fontSize: 11, color: 'var(--dim2)' }}>{under50}</div>
                          ) : null}
                        </>
                      ) : (
                        // Thread 058 section A item 4 + honest-null discipline:
                        // DEF has zero board rows (ADR-039, no DST data
                        // ingested) -- one collapsed line naming that, quoting
                        // board.json's own def_note, rather than three empty
                        // sub-lines or a fabricated ±0/tier/under-50 claim.
                        <div style={{ marginTop: 3, marginLeft: 40, fontSize: 11, color: 'var(--dim2)', lineHeight: 1.45 }}>
                          {data.board.def_note}
                        </div>
                      )}
                      {warning ? (
                        <div style={{ marginTop: 4, marginLeft: 40, padding: '6px 9px', borderLeft: '2px solid var(--down)', background: 'var(--panel2)', fontSize: 11.5, color: 'var(--dim)' }}>
                          {warning}
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
              {/* Thread 058 section A item 6: traceability footer -- the
                  panel names the exact fields feeding it, per docs/handoffs/
                  058's requested `board.position_remaining · board.position_tier
                  · pace vs board.consensus_rank`. This is also what makes the
                  pace phrase interpretable without opening the code. */}
              <div style={{ marginTop: 8, fontFamily: 'var(--font-num)', fontSize: 9.5, color: 'var(--dim2)' }}>
                board.position_remaining · board.position_tier · pace vs board.consensus_rank
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
              {/* Thread 058 section E4/F: traceability footer, matching the
                  Position Scarcity panel's pattern and the design's own
                  footer for this panel. Rendered whenever the panel has real
                  rows to trace -- an empty queue/watchlist has nothing to
                  attribute yet. */}
              {(railTab === 'queue' ? queueRows : watchRows).length > 0 ? (
                <div style={{ marginTop: 8, fontFamily: 'var(--font-num)', fontSize: 9.5, color: 'var(--dim2)' }}>
                  availability.baseline_p → availability.live_p · adjustment.need + adjustment.run
                </div>
              ) : null}

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
            {/* Thread 058 section D1: requirement chips as bordered boxes,
                not a wrapped comma-separated text line -- matching the
                design's own checklist styling exactly (bd/fg: filled=accent,
                partial=default text, empty=dim -- prototype.dc.html line
                3778-3782). Fill state itself (thread 049 item 3) is unchanged,
                still aggregated from the same rosterSlots the list below
                builds, not a second computation -- only the presentation
                changed here. */}
            <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {rosterChips.map((c) => {
                const filled = c.filled >= c.total;
                const started = c.filled > 0;
                return (
                  <span
                    key={c.label}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 5,
                      padding: '2px 6px',
                      border: `1px solid ${filled ? 'var(--acc)' : 'var(--line)'}`,
                      borderRadius: 'var(--r-c)',
                      fontFamily: 'var(--font-num)',
                      fontSize: 10,
                      color: filled ? 'var(--acc)' : started ? 'var(--txt)' : 'var(--dim2)',
                    }}
                  >
                    <span style={{ color: 'var(--dim2)' }}>{c.label}</span> {c.filled}/{c.total}
                  </span>
                );
              })}
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

          <div data-testid="my-picks" style={{ padding: '10px 12px', borderBottom: '1px solid var(--line)' }}>
            <div style={{ fontFamily: 'var(--font-num)', fontSize: 10, letterSpacing: '.12em', color: 'var(--dim2)' }}>
              MY PICKS
            </div>
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {fullPickSequence.map((n) => {
                const made = userPicksByOverall.get(n);
                const isDone = n < currentPick;
                const isCurrent = n === nextUserPick;
                return (
                  <span
                    key={n}
                    title={made ? made.playerName : isCurrent ? 'Your next pick' : undefined}
                    style={{
                      fontFamily: 'var(--font-num)',
                      fontSize: 11,
                      padding: '3px 7px',
                      border: `1px solid ${isCurrent ? 'var(--acc)' : 'var(--line2)'}`,
                      background: isCurrent ? 'var(--panel2)' : 'transparent',
                      color: isDone ? 'var(--dim2)' : isCurrent ? 'var(--acc)' : 'var(--txt)',
                      fontWeight: isCurrent ? 700 : 400,
                    }}
                  >
                    {n}
                  </span>
                );
              })}
              {fullPickSequence.length === 0 ? (
                <span style={{ fontSize: 12, color: 'var(--dim2)' }}>No pick sequence in league.json.</span>
              ) : null}
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
    </div>
      )}

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
            recordPick(id, name, 'shortcut');
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

/** Thread 029 (amended to DraftRoom): the 10-dot frequency array, ported from
 *  the same component already on the player detail sheet and the Availability
 *  Explorer (`Dots` in PlayerDetail.tsx, `SpotlightDots` in Availability.tsx) --
 *  ten dots, N filled, is how this product says a probability instead of
 *  stating a bare percentage. Sized down (4px dots, 1.5px gap -- the two larger
 *  siblings use 6-7px) so it fits inline in the board row without adding a
 *  second line: the constraint is density must not move, and the row's height
 *  is set by its 13px name text, which this is well under. */
function RowDots({ value }: { value: number }) {
  const filled = dotsFilled(value);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 1.5, flex: 'none' }} title={freqText(value)}>
      {Array.from({ length: 10 }, (_, i) => (
        <span
          key={i}
          style={{ width: 4, height: 4, borderRadius: '50%', background: i < filled ? 'var(--acc)' : 'var(--line2)' }}
        />
      ))}
    </div>
  );
}
