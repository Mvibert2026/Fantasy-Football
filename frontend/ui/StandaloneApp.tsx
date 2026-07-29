import { useMemo, useState, type ReactNode } from 'react';
import { SOON_ITEMS, Sidebar, type ScreenId } from './components/shell/Sidebar';
import { TopBar, type Mode } from './components/shell/TopBar';
import { useTheme } from './components/shell/useTheme';
import { NotBuilt } from './components/shell/NotBuilt';
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
 *   - Draft mode IS included (as of this pass -- an earlier version of this
 *     file excluded it on the assumption it needed a backend; checked and
 *     that assumption was wrong). `ui/data/draft.ts`'s own module doc: "No
 *     backend call per pick -- picks and the queue persist to localStorage."
 *     Confirmed no `fetch()` anywhere in DraftRoom.tsx, draft.ts,
 *     liveAvailability.ts, scarcity.ts or recommendation.ts. "Export draft
 *     log" is a client-side Blob download (`downloadJson`, DraftRoom.tsx),
 *     not a network call, and works from `file://`.
 *   - Season mode stays out. `docs/CURRENT-STATE.md` lists it as not built at
 *     all in the live app -- there is nothing to restore, standalone or not.
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
 *     error state instead of fetching: see ui/data/playerHistory.ts's
 *     `__STANDALONE__` compile-time flag (set by vite.standalone.config.ts's
 *     `define`), which skips the fetch entirely rather than issuing one that
 *     would only ever fail.
 *
 * Everything else -- Board (table, sort, filters, tier bands, delta view,
 * round grid, player detail, structural rank-attribution breakdown, watchlist
 * via localStorage), Draft (pick entry, undo, queue, roster panel, live
 * availability/scarcity, all over localStorage + the embedded Dataset),
 * Availability, Opponents, Predictions (reads/writes the same
 * localStorage draft-state key Draft mode does; honestly reports "not yet"
 * with zero picks logged), Strategy Guide, Methodology, and Glossary -- is
 * the real, unmodified view component, because none of them need anything
 * beyond the embedded Dataset and the browser's own localStorage.
 */

const SOON_MAP = new Map(SOON_ITEMS.map((item) => [item.key, item]));
const PREP_AND_DRAFT_MODES: Array<{ key: Mode; label: string }> = [
  { key: 'prep', label: 'Prep' },
  { key: 'draft', label: 'Draft' },
];

const data = STANDALONE_DATASET;

export function StandaloneApp() {
  const [mode, setMode] = useState<Mode>('prep');
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
  if (mode === 'draft') {
    // Full-width, no Sidebar -- matching App.tsx's own layout for Draft mode
    // (DraftRoom has its own three-pane board/scarcity/roster layout that
    // doesn't share the Prep-mode nav rail).
    body = <DraftRoom data={data} rows={rows} league={league} />;
  } else if (soon) {
    body = (
      <>
        <Sidebar screen={screen} onScreen={changeScreen} />
        <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <NotBuilt title={soon.label} body={soon.body} />
        </div>
      </>
    );
  } else {
    let screenBody: ReactNode;
    if (screen === 'board') {
      screenBody = <Board data={data} rows={rows} league={league} />;
    } else if (screen === 'availability') {
      screenBody = <Availability data={data} rows={rows} />;
    } else if (screen === 'opponents') {
      screenBody = (
        <div className="view" style={{ flex: 1, minHeight: 0 }}>
          <Opponents data={data} />
        </div>
      );
    } else if (screen === 'predictions') {
      screenBody = (
        <div className="view" style={{ flex: 1, minHeight: 0 }}>
          <Predictions data={data} rows={rows} league={league} />
        </div>
      );
    } else if (screen === 'strategy') {
      screenBody = (
        <div className="view" style={{ flex: 1, minHeight: 0 }}>
          <StrategyGuide data={data} />
        </div>
      );
    } else if (screen === 'method') {
      screenBody = (
        <div className="view" style={{ flex: 1, minHeight: 0 }}>
          <Methodology data={data} league={league} />
        </div>
      );
    } else if (screen === 'glossary') {
      screenBody = (
        <div className="view" style={{ flex: 1, minHeight: 0 }}>
          <Glossary data={data} />
        </div>
      );
    } else {
      screenBody = null;
    }
    body = (
      <>
        <Sidebar screen={screen} onScreen={changeScreen} />
        <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          {screenBody}
        </div>
      </>
    );
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <TopBar
        mode={mode}
        onModeChange={setMode}
        modes={PREP_AND_DRAFT_MODES}
        theme={theme}
        onToggleTheme={toggleTheme}
        league={league}
        leagues={leagues}
        leagueId="default"
        onSelectLeague={() => {}}
        refreshSlot={<StandaloneFreshnessNote />}
      />

      <div style={{ flex: 1, minHeight: 0, display: 'flex' }}>{body}</div>
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
