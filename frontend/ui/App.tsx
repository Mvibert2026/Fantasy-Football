import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { AssistantDock } from './components/shell/AssistantDock';
import { NotBuilt } from './components/shell/NotBuilt';
import { NAV_MAIN, SOON_ITEMS, Sidebar, type ScreenId } from './components/shell/Sidebar';
import { TopBar, type Mode } from './components/shell/TopBar';
import { useTheme } from './components/shell/useTheme';
import type { ContextItem } from './assistant/reasoning';
import { Assistant } from './views/Assistant';
import { Availability } from './views/Availability';
import { Board } from './views/Board';
import { DraftRoom } from './views/DraftRoom';
import { Glossary } from './views/Glossary';
import { Methodology } from './views/Methodology';
import { Opponents } from './views/Opponents';
import { Predictions } from './views/Predictions';
import { StrategyGuide } from './views/StrategyGuide';
import { buildRows } from './data/board';
import { applyUserSlotOverride, buildLeagueConfig } from './data/league';
import { clearSlotOverride, loadSlotOverride, saveSlotOverride } from './data/draftSlot';
import { TraceModeProvider, useTraceMode } from './data/traceMode';
import { DEFAULT_LEAGUE_ID, fetchSelectableLeagues, type SelectableLeague } from './data/league-registry';
import { loadDataset, type Dataset } from './data/load';

/**
 * PREP: read-only draft preparation over the exported board.
 *
 * Shell ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html) -- top bar, left
 * sidebar, and a floating assistant dock, replacing the earlier horizontal tab
 * bar. See ui/components/shell/*.tsx for the per-component fidelity notes.
 *
 * Draft mode and Season mode have a mode-switcher position (ported, since the
 * prototype's chrome includes them) but Season has no content behind it yet --
 * it renders an explicit "not built" pane rather than a stub screen or a
 * silently dead click. Availability and Opponents are both real: Availability
 * reads availability.json directly (ui/views/Availability.tsx), now that the
 * model no longer carries the circular prior-year-repeat assumption that used to
 * keep it out of scope (ADR-033/034, contract 1.6.0); Opponents reads
 * opponents.json directly (ui/views/Opponents.tsx), showing the real 7-of-9-no-
 * data coverage honestly rather than refusing to render at all. Glossary is a
 * real nav entry again (it briefly wasn't, folded conceptually into Methodology
 * per an earlier reading of the design prototype) -- FRONTEND-SPEC.md §7.3 lists
 * it as its own screen, categorised, so it's back as one, with a backing-field
 * cross-reference per term (ui/data/glossaryCategories.ts).
 */

const SOON_MAP = new Map(SOON_ITEMS.map((item) => [item.key, item]));
const NAV_LABEL = new Map(NAV_MAIN.map((item) => [item.key, item.label]));

export function App() {
  const [data, setData] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [mode, setMode] = useState<Mode>('prep');
  const [screen, setScreen] = useState<ScreenId>('board');
  const [theme, toggleTheme] = useTheme();
  // The player currently open in Board's detail panel, if any -- becomes the
  // assistant's "this player: X" context anchor (prototype's asstFocusTxt, line
  // 1279). Cleared whenever the screen changes so a stale player doesn't linger
  // as context after navigating away from Board.
  const [focusedPlayer, setFocusedPlayer] = useState<string | null>(null);
  // Thread 058 section C4: the current overall pick, reported by DraftRoom
  // while Draft mode is active, so the assistant dock's context line can read
  // "Draft · pick 24" (matching the design) instead of just "Draft". The
  // assistant itself was already mounted on this screen before this thread --
  // see the App() doc comment above -- this only enriches its context string.
  const [draftPick, setDraftPick] = useState<number | null>(null);
  // FR-076: the bounded page-context bundle DraftRoom reports for its own
  // current render (see DraftRoom.tsx's onAssistantContext effect), handed to
  // the assistant so a question like "what are my choices at my next pick"
  // can be answered from the same values already on screen instead of "the
  // backend doesn't have that." [] outside Draft mode -- Assistant.tsx passes
  // an empty bundle through to the reasoning lane exactly like having no page
  // context at all, not a stale one from a prior screen.
  const [assistantPageContext, setAssistantPageContext] = useState<ContextItem[]>([]);

  const [leagues, setLeagues] = useState<SelectableLeague[]>([{ id: DEFAULT_LEAGUE_ID, label: 'Default league' }]);
  const [leagueId, setLeagueId] = useState<string>(DEFAULT_LEAGUE_ID);

  // FR-034: draft-slot override, local and per-league (ui/data/draftSlot.ts), same
  // storage shape/lifecycle as draft state. Re-read whenever the league changes so a
  // switch never carries one league's override into another's -- the exact leak FR-034
  // explicitly rules out.
  const [slotOverride, setSlotOverride] = useState<number | null>(() => loadSlotOverride(leagueId));
  useEffect(() => {
    setSlotOverride(loadSlotOverride(leagueId));
  }, [leagueId]);

  function setDraftSlotOverride(slot: number) {
    saveSlotOverride(leagueId, slot);
    setSlotOverride(slot);
  }
  function clearDraftSlotOverride() {
    clearSlotOverride(leagueId);
    setSlotOverride(null);
  }

  useEffect(() => {
    fetchSelectableLeagues().then(setLeagues);
  }, []);

  // Found while verifying FR-036's persistence (not part of that request, but a real
  // bug surfaced by switching leagues repeatedly): this effect had no guard against
  // out-of-order async resolution. loadDataset(leagueId) is a Promise with no
  // cancellation; if leagueId changes again before it resolves, the OLD call is still
  // in flight and can resolve *after* the new one, overwriting `data` with a dataset
  // for a league that is no longer selected -- `leagueId` (state) and `data.league`
  // (what's rendered) silently disagree, with no error and no loading state to
  // signal it. That's a Principle #3 violation, and a worse one than the principle's
  // usual case: not "still holds the pre-edit value," but "holds an actively wrong
  // value that looks current." Reproduced directly: switch to a non-default league,
  // back to default, then to the same non-default league again -- `data` can end up
  // never updating from the "back to default" load, while every UI affordance
  // (the league <select>, TopBar's pill) reports the new league as selected.
  // Standard fix: an effect-scoped cancellation flag via the cleanup function, so a
  // stale resolution becomes a no-op instead of a write.
  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    setFocusedPlayer(null);
    setAssistantPageContext([]);
    loadDataset(leagueId).then(
      (d) => {
        if (!cancelled) setData(d);
      },
      (e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      },
    );
    return () => {
      cancelled = true;
    };
  }, [leagueId]);

  const rows = useMemo(() => (data ? buildRows(data) : []), [data]);
  // FR-034: the override is applied once, here, so every consumer below (Board,
  // DraftRoom, PlayerDetail, Predictions, RoundGrid, the assistant) reads the
  // overridden userSlot/pickSequence automatically -- no per-screen change needed,
  // and no screen can accidentally read the un-overridden `league.json` value instead.
  const baseLeague = useMemo(() => (data ? buildLeagueConfig(data) : null), [data]);
  const league = useMemo(
    () => (baseLeague ? applyUserSlotOverride(baseLeague, slotOverride) : null),
    [baseLeague, slotOverride],
  );

  // league.json:league_name (contract 1.7.0+) is a better label than "Default
  // league" once it's actually loaded -- overlaid here rather than baked into the
  // leagues list itself, since fetchSelectableLeagues has no reason to load the
  // full dataset just to name the option the app is already sitting on.
  const displayLeagues = useMemo(() => {
    if (!data?.league.league_name) return leagues;
    return leagues.map((l) => (l.id === leagueId ? { ...l, label: data.league.league_name! } : l));
  }, [leagues, data, leagueId]);

  const soon = SOON_MAP.get(screen);
  const screenLabel =
    mode !== 'prep' ? (mode === 'draft' ? 'Draft' : 'Season') : (soon?.label ?? NAV_LABEL.get(screen) ?? 'Board');
  const showsFocusedPlayer = mode === 'draft' || (mode === 'prep' && screen === 'board');
  const assistantWhere = [
    screenLabel,
    mode === 'draft' && draftPick !== null ? `pick ${draftPick}` : null,
    showsFocusedPlayer && focusedPlayer ? `this player: ${focusedPlayer}` : null,
  ]
    .filter((part): part is string => part !== null)
    .join(' · ');

  function changeScreen(next: ScreenId) {
    setScreen(next);
    setFocusedPlayer(null);
  }

  function changeMode(next: Mode) {
    setMode(next);
    setFocusedPlayer(null);
    setDraftPick(null);
    setAssistantPageContext([]);
  }

  // The top bar -- and the league switcher inside it -- stays mounted through
  // loading and error states, not just the loaded one. A league that fails to
  // load (the guard in loadDataset refusing a league_id mismatch, or any other
  // load error) must not also strand the user with no way back to a working
  // league: that would turn "refuse to render bad data" into "refuse to render
  // anything, including the control that would fix it."
  let body: ReactNode;
  if (error) {
    body = (
      <div className="view">
        <div className="empty">
          <strong>The exports could not be loaded.</strong>
          <p>{error}</p>
        </div>
      </div>
    );
  } else if (!data || !league) {
    body = (
      <div className="view">
        <div className="empty">Loading the exports…</div>
      </div>
    );
  } else if (mode === 'draft') {
    body = (
      <DraftRoom
        data={data}
        rows={rows}
        league={league}
        onOpenPlayer={setFocusedPlayer}
        onPickContext={setDraftPick}
        onAssistantContext={setAssistantPageContext}
      />
    );
  } else if (mode === 'season') {
    body = <NotBuilt title="Season mode" body="Season mode is not built in this app yet." />;
  } else {
    body = (
      <>
        <Sidebar screen={screen} onScreen={changeScreen} />
        <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {soon ? (
            <NotBuilt title={soon.label} body={soon.body} />
          ) : screen === 'board' ? (
            <Board data={data} rows={rows} league={league} onFocusPlayer={setFocusedPlayer} />
          ) : screen === 'availability' ? (
            <Availability data={data} rows={rows} league={league} />
          ) : screen === 'opponents' ? (
            <div className="view" style={{ flex: 1, minHeight: 0 }}>
              <Opponents data={data} />
            </div>
          ) : screen === 'predictions' ? (
            <div className="view" style={{ flex: 1, minHeight: 0 }}>
              <Predictions data={data} rows={rows} league={league} />
            </div>
          ) : screen === 'strategy' ? (
            // StrategyGuide/Methodology don't manage their own scroll region (they
            // relied on the old shell's <main className="view">) -- reproduced here
            // rather than touched in each view file, since that's shell layout, not
            // their content.
            <div className="view" style={{ flex: 1, minHeight: 0 }}>
              <StrategyGuide data={data} />
            </div>
          ) : screen === 'method' ? (
            <div className="view" style={{ flex: 1, minHeight: 0 }}>
              <Methodology data={data} league={league} />
            </div>
          ) : screen === 'glossary' ? (
            <div className="view" style={{ flex: 1, minHeight: 0 }}>
              <Glossary data={data} />
            </div>
          ) : null}
        </div>
      </>
    );
  }

  return (
    <TraceModeProvider>
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <TopBar
          mode={mode}
          onModeChange={changeMode}
          theme={theme}
          onToggleTheme={toggleTheme}
          league={league}
          leagues={displayLeagues}
          leagueId={leagueId}
          onSelectLeague={setLeagueId}
          onSelectSlot={setDraftSlotOverride}
          onClearSlot={clearDraftSlotOverride}
          refreshSlot={
            <FreshnessNote
              boardGeneratedUtc={data?.board.generated_utc ?? null}
              snapshotAgeDays={data?.board.snapshot_age_days ?? null}
              snapshotMaxAgeDays={data?.board.snapshot_max_age_days ?? null}
              snapshotStale={data?.board.snapshot_stale ?? null}
            />
          }
        />

        <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>{body}</div>

        {data && rows && league ? (
          <AssistantDock where={assistantWhere}>
            <Assistant data={data} rows={rows} league={league} pageContext={assistantPageContext} />
          </AssistantDock>
        ) : null}
      </div>
    </TraceModeProvider>
  );
}

/**
 * The founder asked twice for the "Refresh data" button to be removed (recorded, but
 * the first ask was never actioned) -- it called a dev-server-only endpoint
 * (`/__refresh`, `server/refresh.ts`) that has never existed on the hosted static
 * build, so on the live site every click could only fail. Present-but-inert is the
 * one state this project's own standing rule rules out (see the module docs on
 * DraftRoom/Season mode's "not built" panes for the same principle applied
 * elsewhere) -- so the button and the component behind it (`RefreshData.tsx`) are
 * gone entirely, not merely hidden in production.
 *
 * The freshness line survives, unconditionally -- it is real information
 * (`board.json:generated_utc` and the snapshot-freshness fields, contract 1.13.0),
 * and the button was never its source, only something sitting upstream of it. This
 * mirrors `StandaloneApp.tsx`'s `StandaloneFreshnessNote`, the working pattern
 * already in this codebase for "the note without the button" -- not reinvented here,
 * just adapted for the live app (this one still gets fresher data on a real page
 * reload or a league switch; the standalone build never does, hence its extra
 * "static snapshot, not live" clause, correctly absent here).
 */
function FreshnessNote({
  boardGeneratedUtc,
  snapshotAgeDays,
  snapshotMaxAgeDays,
  snapshotStale,
}: {
  boardGeneratedUtc: string | null;
  snapshotAgeDays: number | null;
  snapshotMaxAgeDays: number | null;
  snapshotStale: boolean | null;
}) {
  const { on: showSources } = useTraceMode();
  const hasFreshness = snapshotAgeDays !== null && snapshotMaxAgeDays !== null && snapshotStale !== null;
  const freshnessText = hasFreshness
    ? `snapshot ${snapshotStale ? 'STALE' : 'fresh'} (${snapshotAgeDays}d old, max ${snapshotMaxAgeDays}d)`
    : 'snapshot freshness not exported by backend';
  const freshnessTitle = showSources
    ? "board.json:generated_utc is the export-file timestamp. snapshot_age_days/snapshot_max_age_days/" +
      "snapshot_stale are src/freshness.py's separate staleness check (T5), attached to the export since " +
      "contract 1.13.0. Reload the page, or switch leagues, to re-check against the latest export."
    : 'When this export was built, and whether the rankings snapshot it used was fresh. Reload the ' +
      'page, or switch leagues, to re-check against the latest export.';
  return (
    <span
      className="num"
      data-testid="freshness-note"
      title={freshnessTitle}
      style={{
        fontSize: 11,
        color: 'var(--dim2)',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        minWidth: 0,
      }}
    >
      {`exported ${boardGeneratedUtc ?? '—'} · ${freshnessText}`}
    </span>
  );
}
