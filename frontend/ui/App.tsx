import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { AssistantDock } from './components/shell/AssistantDock';
import { NotBuilt } from './components/shell/NotBuilt';
import { NAV_MAIN, SOON_ITEMS, Sidebar, type ScreenId } from './components/shell/Sidebar';
import { TopBar, type Mode } from './components/shell/TopBar';
import { useTheme } from './components/shell/useTheme';
import { RefreshData } from './components/RefreshData';
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
import { buildLeagueConfig } from './data/league';
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

  // Bumping this re-runs the load, which is how the Refresh control applies new exports
  // without a page reload.
  const [reloadKey, setReloadKey] = useState(0);

  const [leagues, setLeagues] = useState<SelectableLeague[]>([{ id: DEFAULT_LEAGUE_ID, label: 'Default league' }]);
  const [leagueId, setLeagueId] = useState<string>(DEFAULT_LEAGUE_ID);

  useEffect(() => {
    fetchSelectableLeagues().then(setLeagues);
  }, [reloadKey]);

  useEffect(() => {
    setData(null);
    setError(null);
    setFocusedPlayer(null);
    loadDataset(leagueId).then(setData, (e: unknown) =>
      setError(e instanceof Error ? e.message : String(e)),
    );
  }, [reloadKey, leagueId]);

  const rows = useMemo(() => (data ? buildRows(data) : []), [data]);
  const league = useMemo(() => (data ? buildLeagueConfig(data) : null), [data]);

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
      <DraftRoom data={data} rows={rows} league={league} onOpenPlayer={setFocusedPlayer} onPickContext={setDraftPick} />
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
            <Availability data={data} rows={rows} />
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
        refreshSlot={
          <RefreshData
            onApplied={() => setReloadKey((k) => k + 1)}
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
          <Assistant data={data} rows={rows} league={league} />
        </AssistantDock>
      ) : null}
    </div>
  );
}
