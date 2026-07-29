import { useMemo, useState, type ReactNode } from 'react';
import { SOON_ITEMS, Sidebar, type ScreenId } from './components/shell/Sidebar';
import { TopBar, type Mode } from './components/shell/TopBar';
import { useTheme } from './components/shell/useTheme';
import { NotBuilt } from './components/shell/NotBuilt';
import { Availability } from './views/Availability';
import { Board } from './views/Board';
import { Glossary } from './views/Glossary';
import { Methodology } from './views/Methodology';
import { Opponents } from './views/Opponents';
import { Predictions } from './views/Predictions';
import { StrategyGuide } from './views/StrategyGuide';
import { buildRows } from './data/board';
import { buildLeagueConfig } from './data/league';
import { STANDALONE_DATASET } from './data/standaloneEmbedded.generated';

/**
 * Standalone entry (ui/main.standalone.tsx renders this, not App.tsx) -- a
 * single self-contained HTML file with no dev server, no network, no `fetch()`
 * at runtime. Built via `npm run build:standalone` -> frontend/dist-standalone/board.html.
 * See docs/frontend-cloud-runbook.md for the full recipe and what does not work
 * here versus the live app.
 *
 * Every difference from App.tsx is a deliberate scope cut for a frozen data
 * snapshot with no backend, never a silently-broken copy of a live feature:
 *
 *   - Data is STANDALONE_DATASET, a build-time-embedded object
 *     (scripts/build-standalone-data.mjs), not an async `loadDataset()` fetch.
 *     There is no loading state because there is nothing to wait for.
 *   - Only Prep mode exists. Draft mode is the live-draft pick-entry loop --
 *     recomputing availability/scarcity against picks nobody is logging --
 *     and Season mode has no content in the live app either. Both require a
 *     session with a backend or at least a live localStorage draft in
 *     progress; neither belongs in a frozen file, so TopBar's `modes` prop
 *     renders only Prep, not a disabled Draft/Season button that would invite
 *     a click leading nowhere.
 *   - The league switcher shows exactly one option, the real league this file
 *     was built from -- not a dropdown implying other leagues are reachable.
 *     Matches TopBar's own existing "single honest option" convention for
 *     when only one league is registered.
 *   - "Refresh data" is absent, not disabled: it POSTs to `/__refresh`, a dev-
 *     server-only endpoint that does not exist here. StandaloneFreshnessNote
 *     shows the same export/freshness text with no button.
 *   - The Assistant dock is absent. Its template and fallback lanes are pure
 *     local computation and would have worked, but its reasoning lane POSTs
 *     to `/__reasoning` -- dropped for a hard, verifiable zero-fetch-at-runtime
 *     guarantee rather than a mixed dock where one lane works offline and
 *     the rest have to explain themselves.
 *   - PlayerDetail's sections 7/8 (season history) report a real, existing
 *     error state instead of fetching: see ui/data/playerHistory.standalone.ts,
 *     aliased in over the network-backed module by vite.standalone.config.ts.
 *
 * Everything else -- Board (table, sort, filters, tier bands, delta view,
 * round grid, player detail, structural rank-attribution breakdown, watchlist
 * via localStorage), Availability, Opponents, Predictions (reads/writes the
 * same localStorage draft-state key the live app uses; honestly reports
 * "not yet" with zero picks logged), Strategy Guide, Methodology, and
 * Glossary -- is the real, unmodified view component, because none of them
 * need anything beyond the embedded Dataset.
 */

const SOON_MAP = new Map(SOON_ITEMS.map((item) => [item.key, item]));
const PREP_ONLY_MODES: Array<{ key: Mode; label: string }> = [{ key: 'prep', label: 'Prep' }];

const data = STANDALONE_DATASET;

export function StandaloneApp() {
  const [screen, setScreen] = useState<ScreenId>('board');
  const [theme, toggleTheme] = useTheme();

  const rows = useMemo(() => buildRows(data), []);
  const league = useMemo(() => buildLeagueConfig(data), []);

  const leagues = useMemo(
    () => [{ id: 'default', label: data.league.league_name ?? 'Default league' }],
    [],
  );

  const soon = SOON_MAP.get(screen);

  function changeScreen(next: ScreenId) {
    setScreen(next);
  }

  let body: ReactNode;
  if (soon) {
    body = <NotBuilt title={soon.label} body={soon.body} />;
  } else if (screen === 'board') {
    body = <Board data={data} rows={rows} league={league} />;
  } else if (screen === 'availability') {
    body = <Availability data={data} rows={rows} />;
  } else if (screen === 'opponents') {
    body = (
      <div className="view" style={{ flex: 1, minHeight: 0 }}>
        <Opponents data={data} />
      </div>
    );
  } else if (screen === 'predictions') {
    body = (
      <div className="view" style={{ flex: 1, minHeight: 0 }}>
        <Predictions data={data} rows={rows} league={league} />
      </div>
    );
  } else if (screen === 'strategy') {
    body = (
      <div className="view" style={{ flex: 1, minHeight: 0 }}>
        <StrategyGuide data={data} />
      </div>
    );
  } else if (screen === 'method') {
    body = (
      <div className="view" style={{ flex: 1, minHeight: 0 }}>
        <Methodology data={data} league={league} />
      </div>
    );
  } else if (screen === 'glossary') {
    body = (
      <div className="view" style={{ flex: 1, minHeight: 0 }}>
        <Glossary data={data} />
      </div>
    );
  } else {
    body = null;
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <TopBar
        mode="prep"
        onModeChange={() => {}}
        modes={PREP_ONLY_MODES}
        theme={theme}
        onToggleTheme={toggleTheme}
        league={league}
        leagues={leagues}
        leagueId="default"
        onSelectLeague={() => {}}
        refreshSlot={<StandaloneFreshnessNote />}
      />

      <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>
        <Sidebar screen={screen} onScreen={changeScreen} />
        <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {body}
        </div>
      </div>
    </div>
  );
}

/**
 * Static equivalent of RefreshData.tsx's freshness line, with the button
 * removed rather than disabled -- there is no dev server for it to reach, so
 * a click could only ever fail, and this app has a standing rule against a
 * control that exists only to fail on click. The generation timestamp is the
 * one thing this component exists to keep visible per the founder's
 * instruction, independent of which screen is open.
 */
function StandaloneFreshnessNote() {
  const generated = data.board.generated_utc;
  const age = data.board.snapshot_age_days;
  const maxAge = data.board.snapshot_max_age_days;
  const stale = data.board.snapshot_stale;
  const hasFreshness = age !== null && age !== undefined && maxAge !== null && maxAge !== undefined && stale !== null && stale !== undefined;
  const freshnessText = hasFreshness
    ? `snapshot ${stale ? 'STALE' : 'fresh'} (${age}d old, max ${maxAge}d)`
    : 'snapshot freshness not exported by backend';
  return (
    <span
      className="num"
      data-testid="freshness-note"
      title="Static snapshot, built once from data/export/. There is no dev server here to re-check
        against, so this timestamp only ever reflects the day this file was generated."
      style={{
        fontSize: 11,
        color: 'var(--dim2)',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        minWidth: 0,
      }}
    >
      {`exported ${generated ?? '—'} · ${freshnessText} · static snapshot, not live`}
    </span>
  );
}
