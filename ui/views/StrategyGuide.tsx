import type { Dataset } from '../data/load';
import { decimal, integer } from '../lib/format';

/**
 * The strategy guide.
 *
 * Two rules from the data contract are enforced in the layout rather than left to the
 * reader. `sign_test_p` is never shown against a 0.05 threshold -- with four seasons
 * the floor is 0.125, so nothing can clear 0.05 and rendering a red/green verdict
 * against it would be theatre. And the power-floor sentence sits immediately beside
 * any significance number, not in a footnote.
 *
 * `simulation_se` and the season interval are also kept visually apart, because they
 * are different uncertainties: the first shrinks with more simulated drafts, the
 * second does not.
 */

export function StrategyGuide({ data }: { data: Dataset }) {
  const s = data.strategies;

  if (s.strategies.length === 0) {
    return (
      <div className="stack">
        <h2>Strategy guide</h2>
        <div className="empty">
          <strong>No strategies in the export.</strong> strategies.json carries no runs.
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <section>
        <h2>Strategy guide</h2>
        <p className="notice">
          <strong>What can and cannot be concluded here.</strong> {s.power_floor.plain_english}
        </p>
        <p className="notice">
          <strong>Lineup assumption.</strong> {s.lineup_assumption}
        </p>
        <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--fg-muted)' }}>
          Baseline: <code>{s.baseline}</code>. Seasons{' '}
          <span className="num">{s.seasons.map(integer).join(', ')}</span>, with{' '}
          <span className="num">{integer(s.simulations_per_cell)}</span> simulated drafts per cell.
          Sigma is how closely simulated opponents follow consensus — higher means more random.
        </p>
      </section>

      {s.strategies.map((strategy) => (
        <section key={strategy.name}>
          <h3>
            {strategy.name}
            {strategy.is_baseline ? ' · baseline' : ''}
          </h3>
          <p>{strategy.verdict}</p>
          <div className="table-wrap">
            <table className="board">
              <thead>
                <tr>
                  <th className="n">Sigma</th>
                  <th className="n">Mean roster pts</th>
                  <th className="n">P(top 4)</th>
                  <th className="n">Margin vs baseline</th>
                  <th className="n">Season interval</th>
                  <th className="n">Seasons positive</th>
                  <th className="n">Sim. SE</th>
                  <th>Sign test</th>
                </tr>
              </thead>
              <tbody>
                {strategy.by_sigma.map((cell) => (
                  <tr key={cell.sigma}>
                    <td className="n">{integer(cell.sigma)}</td>
                    <td className="n">{decimal(cell.mean_roster_points)}</td>
                    <td className="n">{decimal(cell.p_top4)}</td>
                    <td className="n">
                      {cell.margin_vs_baseline === null ? '—' : decimal(cell.margin_vs_baseline)}
                    </td>
                    <td className="n">
                      {cell.ci_low === null || cell.ci_high === null
                        ? '—'
                        : `${decimal(cell.ci_low)} – ${decimal(cell.ci_high)}`}
                    </td>
                    <td className="n">
                      {cell.seasons_positive === null
                        ? '—'
                        : `${integer(cell.seasons_positive)} of ${integer(s.power_floor.n_seasons)}`}
                    </td>
                    <td className="n">{decimal(cell.simulation_se)}</td>
                    {/* Rendered as a bare number with the floor beside it. No threshold, no verdict. */}
                    <td className="num">
                      {cell.sign_test_p === null ? (
                        '—'
                      ) : (
                        <span title={s.power_floor.plain_english}>
                          {`p = ${decimal(cell.sign_test_p)} (floor ${decimal(s.power_floor.smallest_attainable_two_sided_p)})`}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--fg-faint)', marginTop: 'var(--pad-y)' }}>
            The season interval and the simulation standard error are different uncertainties and
            are never combined: more simulated drafts shrink the second and leave the first alone.
          </p>
        </section>
      ))}
    </div>
  );
}
