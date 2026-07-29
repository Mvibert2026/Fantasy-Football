import { Fragment } from 'react';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { decimal, integer } from '../lib/format';
import { Value } from '../components/Value';

/**
 * Methodology: what the numbers are, what they are not, and where each one lives.
 *
 * The registered nulls are a section here rather than an appendix. Publishing what was
 * tested and did not hold up is the part most guides leave out, and it is the part that
 * tells you how much to trust the rest.
 */

export function Methodology({ data, league }: { data: Dataset; league: LeagueConfig }) {
  const fits = Object.entries(data.board.curve_fits);

  return (
    <div className="stack">
      <section>
        <h2>Methodology</h2>
        <p className="notice">{data.board.curve_caveat}</p>
      </section>

      <section>
        <h3>Startable thresholds</h3>
        <p style={{ color: 'var(--fg-muted)' }}>{league.replacementLevelsNote}</p>
        {league.thresholdDrift ? <p className="notice">{league.thresholdDrift}</p> : null}
        <dl className="defs">
          {league.thresholds.map((t) => (
            <Fragment key={t.position}>
              <dt>{t.position}</dt>
              <dd>
                {t.level.kind === 'present' ? (
                  <>
                    Startable through{' '}
                    <strong className="num">
                      {t.position}
                      <Value cell={t.level} render={integer} />
                    </strong>
                    {' · '}
                    <span className="num">
                      <Value cell={t.starters} render={integer} />
                    </span>{' '}
                    started per team
                  </>
                ) : (
                  <span style={{ color: 'var(--fg-muted)' }}>{t.level.reason}</span>
                )}
              </dd>
            </Fragment>
          ))}
        </dl>
      </section>

      <section>
        <h3>Projection curve fit</h3>
        <p style={{ color: 'var(--fg-muted)' }}>
          R² is the share of variance in actual scoring that consensus rank explains. These are
          low, which is why the board suppresses point projections outside the fitted range rather
          than extrapolating into a number that would look precise.
        </p>
        <div className="table-wrap">
          <table className="board">
            <thead>
              <tr>
                <th>Position</th>
                <th className="n">R²</th>
                <th className="n">Residual SD</th>
                <th className="n">Observations</th>
              </tr>
            </thead>
            <tbody>
              {fits.map(([pos, fit]) => (
                <tr key={pos}>
                  <td>{pos}</td>
                  <td className="n">{decimal(fit.r_squared)}</td>
                  <td className="n">{decimal(fit.residual_sd)}</td>
                  <td className="n">{integer(fit.n_obs)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3>What the board does not claim</h3>
        <p className="notice">{data.board.consensus_source_note}</p>
        <p className="notice">{data.board.def_note}</p>
        <p className="notice">{league.flexSplitNote}</p>
      </section>

      {data.board.adp_source_note ? (
        <section>
          <h3>ADP (market average draft position)</h3>
          <p style={{ color: 'var(--fg-muted)' }}>
            <code>ADP</code> is display-only. It does not feed <code>projected_points</code>,{' '}
            <code>vbd</code>, tiers, availability, or any recommendation this board makes — those
            are all still driven entirely by expert consensus rank (see &ldquo;consensus
            rank&rdquo; and &ldquo;VBD&rdquo; in the glossary). ADP is shown next to those numbers
            for comparison, never merged into them.
          </p>
          <p className="notice">{data.board.adp_source_note}</p>
          {data.board.adp_match_rate_note ? (
            <p style={{ color: 'var(--fg-muted)', fontSize: 'var(--fs-xs)' }}>
              {data.board.adp_match_rate_note}
              {data.board.adp_as_of_date ? ` Snapshot as of ${data.board.adp_as_of_date}.` : ''}
            </p>
          ) : null}
        </section>
      ) : null}

      <section>
        <h3>Tested and found nothing</h3>
        <p style={{ color: 'var(--fg-muted)' }}>{data.nulls.preamble}</p>
        <dl className="defs">
          {data.nulls.findings.map((f) => (
            <Fragment key={f.id}>
              <dt>{f.id}</dt>
              <dd>
                <strong>{f.claim_tested}</strong>
                <p style={{ marginTop: 'var(--pad-y)' }}>{f.plain_language_summary}</p>
                <p style={{ color: 'var(--fg-muted)', fontSize: 'var(--fs-xs)' }}>
                  {f.result === 'NOT_YET_RUN_FOR_THIS_LEAGUE'
                    ? 'Not yet re-run for this league (see the summary above).'
                    : f.result}
                </p>
              </dd>
            </Fragment>
          ))}
        </dl>
      </section>

      <section>
        <h3>Where these numbers came from</h3>
        <p style={{ color: 'var(--fg-muted)' }}>
          Each artifact and the export run it came from. Values on this page are copied
          verbatim from these files — nothing is rewritten, filled in, or adjusted in between.
        </p>
        <dl className="defs">
          {Object.entries(data.manifest.artifacts).map(([name, entry]) => (
            <Fragment key={name}>
              <dt>{name}</dt>
              <dd className="num" style={{ fontSize: 'var(--fs-xs)' }}>
                {entry.run_id}
              </dd>
            </Fragment>
          ))}
        </dl>
      </section>
    </div>
  );
}
