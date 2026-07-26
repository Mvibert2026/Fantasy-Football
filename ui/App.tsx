import { useEffect, useMemo, useState } from 'react';
import { AssistantDock } from './components/shell/AssistantDock';
import { NotBuilt } from './components/shell/NotBuilt';
import { NAV_MAIN, SOON_ITEMS, Sidebar, type ScreenId } from './components/shell/Sidebar';
import { TopBar, type Mode } from './components/shell/TopBar';
import { useTheme } from './components/shell/useTheme';
import { RefreshData } from './components/RefreshData';
import { Assistant } from './views/Assistant';
import { Board } from './views/Board';
import { Methodology } from './views/Methodology';
import { StrategyGuide } from './views/StrategyGuide';
import { buildRows } from './data/board';
import { buildLeagueConfig } from './data/league';
import { loadDataset, type Dataset } from './data/load';

/**
 * PREP: read-only draft preparation over the exported board.
 *
 * Shell ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html) -- top bar, left
 * sidebar, and a floating assistant dock, replacing the earlier horizontal tab
 * bar. See ui/components/shell/*.tsx for the per-component fidelity notes.
 *
 * Availability, Opponents, Draft mode and Season mode all have nav entries or a
 * mode-switcher position (ported, since the prototype's chrome includes them) but
 * no content behind them -- each renders an explicit "not built" pane rather than
 * a stub screen or a silently dead click. Glossary, previously a top-level tab, is
 * not in this nav: the prototype folds glossary content into Methodology
 * ("METHODOLOGY & GLOSSARY") and inline info-icon popovers, which is content work
 * belonging to a later step. The existing Glossary view is kept in the codebase,
 * just unreachable from navigation for now -- noted rather than silently dropped.
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

  // Bumping this re-runs the load, which is how the Refresh control applies new exports
  // without a page reload.
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    loadDataset().then(setData, (e: unknown) =>
      setError(e instanceof Error ? e.message : String(e)),
    );
  }, [reloadKey]);

  const rows = useMemo(() => (data ? buildRows(data) : []), [data]);
  const league = useMemo(() => (data ? buildLeagueConfig(data) : null), [data]);

  if (error) {
    return (
      <div className="view">
        <div className="empty">
          <strong>The exports could not be loaded.</strong>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!data || !league) {
    return (
      <div className="view">
        <div className="empty">Loading the exports…</div>
      </div>
    );
  }

  const soon = SOON_MAP.get(screen);
  const screenLabel =
    mode !== 'prep' ? (mode === 'draft' ? 'Draft' : 'Season') : (soon?.label ?? NAV_LABEL.get(screen) ?? 'Board');
  const assistantWhere =
    screen === 'board' && focusedPlayer ? `${screenLabel} · this player: ${focusedPlayer}` : screenLabel;

  function changeScreen(next: ScreenId) {
    setScreen(next);
    setFocusedPlayer(null);
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <TopBar
        mode={mode}
        onModeChange={setMode}
        theme={theme}
        onToggleTheme={toggleTheme}
        league={league}
        refreshSlot={<RefreshData onApplied={() => setReloadKey((k) => k + 1)} />}
      />

      <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
        {mode === 'draft' ? (
          <NotBuilt title="Draft mode" body="Draft mode is not built in this app yet." />
        ) : mode === 'season' ? (
          <NotBuilt title="Season mode" body="Season mode is not built in this app yet." />
        ) : (
          <>
            <Sidebar screen={screen} onScreen={changeScreen} />
            <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
              {soon ? (
                <NotBuilt title={soon.label} body={soon.body} />
              ) : screen === 'board' ? (
                <Board data={data} rows={rows} league={league} onFocusPlayer={setFocusedPlayer} />
              ) : screen === 'availability' ? (
                <NotBuilt
                  title="Availability"
                  body="Not available in this build. The availability model is being replaced."
                  badge="OUT OF SCOPE"
                />
              ) : screen === 'opponents' ? (
                <NotBuilt
                  title="Opponents"
                  body="Not available in this build. Seven of nine opponents have no supplied draft history to work from."
                  badge="OUT OF SCOPE"
                />
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
              ) : null}
            </div>
          </>
        )}
      </div>

      <AssistantDock where={assistantWhere}>
        <Assistant data={data} rows={rows} league={league} />
      </AssistantDock>
    </div>
  );
}
