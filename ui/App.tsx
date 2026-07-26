import { useEffect, useMemo, useState } from 'react';
import { buildRows } from './data/board';
import { buildLeagueConfig } from './data/league';
import { loadDataset, type Dataset } from './data/load';
import { RefreshData } from './components/RefreshData';
import { Assistant } from './views/Assistant';
import { Board } from './views/Board';
import { Glossary } from './views/Glossary';
import { Methodology } from './views/Methodology';
import { StrategyGuide } from './views/StrategyGuide';

/**
 * PREP: read-only draft preparation over the exported board.
 *
 * Out of scope, deliberately: availability (the model is being replaced), opponents
 * (seven of nine have no data), the draft room, player profiles, and season mode.
 * None of them are stubbed here -- a greyed-out tab implies something is coming, and
 * the honest state is that they are not part of this app.
 */

type Tab = 'board' | 'ask' | 'guide' | 'glossary' | 'method';

const TABS: Array<{ id: Tab; label: string }> = [
  { id: 'board', label: 'Board' },
  { id: 'ask', label: 'Ask' },
  { id: 'guide', label: 'Strategy' },
  { id: 'glossary', label: 'Glossary' },
  { id: 'method', label: 'Methodology' },
];

export function App() {
  const [data, setData] = useState<Dataset | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('board');

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

  return (
    <div className="app">
      <header className="topbar">
        <span className="wordmark">PREP</span>
        <nav>
          {TABS.map((t) => (
            <button key={t.id} aria-pressed={tab === t.id} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>
        <span className="stamp" title="The export run every value on screen comes from">
          {data.board.contract_version} · {data.board.generated_utc}
        </span>
        <RefreshData onApplied={() => setReloadKey((k) => k + 1)} />
      </header>

      <main className="view">
        {tab === 'board' ? <Board data={data} rows={rows} league={league} /> : null}
        {tab === 'ask' ? <Assistant data={data} rows={rows} league={league} /> : null}
        {tab === 'guide' ? <StrategyGuide data={data} /> : null}
        {tab === 'glossary' ? <Glossary data={data} /> : null}
        {tab === 'method' ? <Methodology data={data} league={league} /> : null}
      </main>
    </div>
  );
}
