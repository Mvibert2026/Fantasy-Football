import { useRef, useState } from 'react';
import { EXPECTED_CONTRACT } from '../data/contract';
import { useDismissOnOutsideOrEscape } from '../lib/dismiss';

/**
 * The Refresh control.
 *
 * Sits in the top bar rather than behind a menu, because it bridges two sessions: the
 * backend regenerates exports on its own schedule and nothing here finds out until
 * someone asks. Waiting to notice a stale drift banner is not a workflow.
 *
 * A no-op is reported as a no-op. "No update available" and "nothing happened because
 * the button is broken" look identical otherwise.
 */

interface ArtifactChange {
  artifact: string;
  before: { contract_version: string | null; generated_utc: string | null } | null;
  after: { contract_version: string | null; generated_utc: string | null };
  change: 'added' | 'version' | 'regenerated' | 'unchanged';
}

interface RefreshReport {
  updated: boolean;
  message: string;
  checkedAt: string;
  changes: ArtifactChange[];
  behindExpected: Array<{ artifact: string; version: string | null }>;
  expected: string;
}

const CHANGE_LABEL: Record<ArtifactChange['change'], string> = {
  added: 'new artifact',
  version: 'contract version changed',
  regenerated: 'regenerated, same contract version',
  unchanged: 'unchanged',
};

export function RefreshData({
  onApplied,
  boardGeneratedUtc = null,
  snapshotAgeDays = null,
  snapshotMaxAgeDays = null,
  snapshotStale = null,
}: {
  onApplied: () => void;
  /**
   * Real, named field: `board.json:generated_utc` -- the timestamp the export was written,
   * threaded down from App's loaded Dataset. Null (dataset not loaded yet) renders as "-",
   * never a fabricated placeholder date.
   */
  boardGeneratedUtc?: string | null;
  /**
   * Contract 1.13.0 (thread 074). `board.json:snapshot_age_days` / `snapshot_max_age_days` /
   * `snapshot_stale` -- the `FreshnessResult` `src/freshness.py` computes on every board build
   * (as_of_date/age_days/stale, measured against `rankings.as_of_date`), now attached to the
   * export instead of only printed to the build console. Distinct from `boardGeneratedUtc`,
   * which is the export-file write time, not the underlying ranking snapshot's age. Null when
   * the loaded export predates 1.13.0 or the dataset hasn't loaded yet -- the banner falls back
   * to naming that gap explicitly rather than showing a stale claim as if it were current.
   */
  snapshotAgeDays?: number | null;
  snapshotMaxAgeDays?: number | null;
  snapshotStale?: boolean | null;
}) {
  const [report, setReport] = useState<RefreshReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  // Thread 073: the report popover previously only closed via its own
  // "Dismiss" button -- no click-outside, no Escape. The founder tried both
  // of the ordinary ways to clear a floating message and neither worked.
  // Every dismissible surface in this app must support both (see
  // ui/lib/dismiss.ts); this was the confirmed failing case.
  useDismissOnOutsideOrEscape(wrapperRef, Boolean(report || error), () => {
    setReport(null);
    setError(null);
  });

  async function refresh() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch('/__refresh', { method: 'POST' });
      const body = (await res.json()) as RefreshReport;
      setReport(body);
      // Only re-read the dataset when something actually moved -- reloading on a no-op
      // would make the button feel like it worked when it had nothing to do.
      if (body.updated) onApplied();
    } catch {
      setError(
        'The refresh endpoint could not be reached. It runs inside the dev server, so this ' +
          'means the server is not running — the board you are looking at is still valid, just ' +
          'not re-checked.',
      );
    } finally {
      setBusy(false);
    }
  }

  const hasFreshness = snapshotAgeDays !== null && snapshotMaxAgeDays !== null && snapshotStale !== null;
  const freshnessText = hasFreshness
    ? `snapshot ${snapshotStale ? 'STALE' : 'fresh'} (${snapshotAgeDays}d old, max ${snapshotMaxAgeDays}d)`
    : 'snapshot freshness not exported by backend';
  const freshnessTitle = hasFreshness
    ? 'board.json:generated_utc is the export-file timestamp. snapshot_age_days/snapshot_max_age_days/' +
      'snapshot_stale are a separate claim -- src/freshness.py\'s check (T5) against ' +
      'rankings.as_of_date, attached to the export since contract 1.13.0 (thread 074).'
    : 'board.json:generated_utc is the export-file timestamp. It is NOT the same claim as ' +
      '"is the underlying ranking snapshot stale" -- src/freshness.py computes that (T5) on ' +
      'every board build but this export predates contract 1.13.0, so it does not carry that ' +
      'result. This is an honest gap, not a silent omission.';

  return (
    <div
      ref={wrapperRef}
      style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}
    >
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
      <button
        onClick={refresh}
        disabled={busy}
        title="Re-read data/export/ and report what changed"
        style={{ flex: 'none', whiteSpace: 'nowrap' }}
      >
        {busy ? 'Checking…' : 'Refresh data'}
      </button>
      {(report || error) && (
        <div className="refresh-report">
          {error ? (
            <div className="refresh-head">
              <p style={{ margin: 0 }}>{error}</p>
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          ) : null}
          {report ? <Report report={report} onDismiss={() => setReport(null)} /> : null}
        </div>
      )}
    </div>
  );
}

function Report({ report, onDismiss }: { report: RefreshReport; onDismiss: () => void }) {
  const moved = report.changes.filter((c) => c.change !== 'unchanged');

  return (
    <div>
      <div className="refresh-head">
        <strong>{report.message}</strong>
        <button onClick={onDismiss}>Dismiss</button>
      </div>

      {moved.length > 0 ? (
        <table className="board">
          <thead>
            <tr>
              <th>Artifact</th>
              <th>Before</th>
              <th>After</th>
              <th>What changed</th>
            </tr>
          </thead>
          <tbody>
            {moved.map((c) => (
              <tr key={c.artifact}>
                <td>{c.artifact}</td>
                <td className="num">{c.before ? (c.before.contract_version ?? 'unversioned') : 'absent'}</td>
                <td className="num">{c.after.contract_version ?? 'unversioned'}</td>
                <td>{CHANGE_LABEL[c.change]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      {report.behindExpected.length > 0 ? (
        <p className="notice">
          {`This app is written against contract ${EXPECTED_CONTRACT}. Still on a different version: `}
          {report.behindExpected.map((b) => `${b.artifact} (${b.version ?? 'unversioned'})`).join(', ')}
          {'. Values from those artifacts are shown as exported; nothing is adjusted to compensate.'}
        </p>
      ) : (
        <p className="notice">
          {`All artifacts are at contract ${report.expected}, which is what this app expects.`}
        </p>
      )}

      <p className="provenance">{`checked ${report.checkedAt}`}</p>
    </div>
  );
}
