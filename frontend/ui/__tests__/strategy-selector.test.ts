import { describe, expect, it } from 'vitest';
import {
  applyStrategyPreference,
  orderedStrategiesFor,
  rosterShapeSummary,
  strategyDemotedPosition,
  strategyLabel,
  strategyPromotedPosition,
  strategyRuleText,
  STRATEGY_CATALOG,
} from '../data/strategySelector';
import type { RawStrategies } from '../data/types';
import type { ScoredRow } from '../data/recommendation';
import type { BoardRow } from '../data/board';
import { present } from '../data/cell';

function row(id: number, position: string, vbd: number): ScoredRow {
  const raw = { position } as BoardRow['raw'];
  return {
    row: { id, raw, vbd: present(vbd, 'board.json:players[].vbd', 'run') } as unknown as BoardRow,
    score: vbd,
  };
}

describe('strategyPromotedPosition / strategyDemotedPosition', () => {
  it('zero_rb demotes RB through round 4 only', () => {
    expect(strategyDemotedPosition('zero_rb', 1)).toBe('RB');
    expect(strategyDemotedPosition('zero_rb', 4)).toBe('RB');
    expect(strategyDemotedPosition('zero_rb', 5)).toBeNull();
  });

  it('hero_rb promotes RB in round 1 only (the softer later lean is not ported)', () => {
    expect(strategyPromotedPosition('hero_rb', 1)).toBe('RB');
    expect(strategyPromotedPosition('hero_rb', 2)).toBeNull();
  });

  it('elite_te_early and qb_early promote through round 3 only', () => {
    expect(strategyPromotedPosition('elite_te_early', 3)).toBe('TE');
    expect(strategyPromotedPosition('elite_te_early', 4)).toBeNull();
    expect(strategyPromotedPosition('qb_early', 3)).toBe('QB');
    expect(strategyPromotedPosition('qb_early', 4)).toBeNull();
  });

  it('balanced and bpa_consensus never promote or demote anything', () => {
    for (const round of [1, 2, 3, 4, 5]) {
      expect(strategyPromotedPosition('balanced', round)).toBeNull();
      expect(strategyDemotedPosition('balanced', round)).toBeNull();
      expect(strategyPromotedPosition('bpa_consensus', round)).toBeNull();
      expect(strategyDemotedPosition('bpa_consensus', round)).toBeNull();
    }
  });
});

describe('applyStrategyPreference', () => {
  const scored = [row(1, 'RB', 172), row(2, 'WR', 152), row(3, 'RB', 137), row(4, 'WR', 123), row(5, 'QB', 90)];

  it('is a no-op for bpa_consensus and balanced', () => {
    expect(applyStrategyPreference(scored, 1, 'bpa_consensus')).toEqual(scored);
    expect(applyStrategyPreference(scored, 1, 'balanced')).toEqual(scored);
  });

  it('demotes every RB below every non-RB, preserving VBD order within each group, for zero_rb in round <= 4', () => {
    const out = applyStrategyPreference(scored, 1, 'zero_rb');
    expect(out.map((s) => s.row.id)).toEqual([2, 4, 5, 1, 3]);
  });

  it('does not reorder zero_rb outside its round window', () => {
    expect(applyStrategyPreference(scored, 5, 'zero_rb')).toEqual(scored);
  });

  it('promotes RB to the front for hero_rb in round 1', () => {
    const out = applyStrategyPreference(scored, 1, 'hero_rb');
    expect(out.map((s) => s.row.id)).toEqual([1, 3, 2, 4, 5]);
  });

  it('promotes QB to the front for qb_early through round 3', () => {
    const out = applyStrategyPreference(scored, 3, 'qb_early');
    expect(out.map((s) => s.row.id)).toEqual([5, 1, 2, 3, 4]);
  });
});

describe('strategyLabel / STRATEGY_CATALOG', () => {
  it('has exactly the six strategies strategies.json ever carries', () => {
    expect(STRATEGY_CATALOG.map((s) => s.key).sort()).toEqual(
      ['balanced', 'bpa_consensus', 'elite_te_early', 'hero_rb', 'qb_early', 'zero_rb'].sort(),
    );
  });

  it('labels every key with a real human word, not the raw identifier', () => {
    expect(strategyLabel('zero_rb')).toBe('Zero RB');
    expect(strategyLabel('bpa_consensus')).toBe('Best player available');
  });
});

describe('strategyRuleText', () => {
  // FR-121: the `src/draft_sim.py::strategy_*` source citation is
  // developer-facing sourcing text, gated by the "show data sources" switch
  // (default off/omitted here) -- never welded into the plain-English rule
  // text itself, which every case must still carry regardless of the switch.
  it('does not name src/draft_sim.py by default -- the switch is off', () => {
    for (const key of ['zero_rb', 'hero_rb', 'elite_te_early', 'qb_early'] as const) {
      expect(strategyRuleText(key)).not.toContain('src/draft_sim.py');
    }
  });

  it('names src/draft_sim.py as the source for every round-gated strategy once the switch is on, never inventing a new rule', () => {
    for (const key of ['zero_rb', 'hero_rb', 'elite_te_early', 'qb_early'] as const) {
      expect(strategyRuleText(key, true)).toContain('src/draft_sim.py');
    }
  });

  it('states plainly that balanced applies no additional reorder, on or off', () => {
    expect(strategyRuleText('balanced')).toContain('does not additionally reorder');
    expect(strategyRuleText('balanced', true)).toContain('does not additionally reorder');
  });
});

function fixtureStrategies(): RawStrategies {
  return {
    contract_version: '1.15.0',
    generated_utc: '2026-07-30T00:00:00Z',
    league_id: 'primary',
    baseline: 'bpa_consensus',
    seasons: [2021, 2022, 2023, 2024],
    simulations_per_cell: 600,
    seed: 1,
    sigma_values: [5, 10, 20],
    power_floor: { n_seasons: 4, smallest_attainable_two_sided_p: 0.125, plain_english: 'power floor text' },
    lineup_assumption: 'lineup assumption text',
    strategies: [
      {
        name: 'bpa_consensus',
        is_baseline: true,
        by_sigma: [
          { sigma: 10, mean_roster_points: 100, p_top4: 0.5, margin_vs_baseline: null, ci_low: null, ci_high: null, seasons_positive: null, sign_test_p: null, per_season_margin: null, simulation_se: 1 },
        ],
        verdict: 'baseline',
      },
      {
        name: 'balanced',
        is_baseline: false,
        by_sigma: [
          {
            sigma: 5,
            mean_roster_points: 110,
            p_top4: 0.6,
            margin_vs_baseline: 13,
            ci_low: -10,
            ci_high: 30,
            seasons_positive: 4,
            sign_test_p: 0.125,
            per_season_margin: { '2021': 10, '2022': 5, '2023': 8, '2024': 12 },
            simulation_se: 1,
          },
          {
            sigma: 10,
            mean_roster_points: 115,
            p_top4: 0.62,
            margin_vs_baseline: 20,
            ci_low: -5,
            ci_high: 40,
            seasons_positive: 4,
            sign_test_p: 0.125,
            per_season_margin: { '2021': 10, '2022': 5, '2023': 8, '2024': 12 },
            simulation_se: 1,
          },
          { sigma: 20, mean_roster_points: 118, p_top4: 0.65, margin_vs_baseline: 28, ci_low: 0, ci_high: 50, seasons_positive: 4, sign_test_p: 0.125, per_season_margin: { '2021': 10, '2022': 5, '2023': 8, '2024': 12 }, simulation_se: 1 },
        ],
        verdict: 'better in all four seasons',
      },
      {
        name: 'zero_rb',
        is_baseline: false,
        by_sigma: [
          { sigma: 5, mean_roster_points: 105, p_top4: 0.55, margin_vs_baseline: 20, ci_low: -15, ci_high: 40, seasons_positive: 3, sign_test_p: 0.375, per_season_margin: { '2021': 5, '2022': -2, '2023': 8, '2024': 6 }, simulation_se: 1 },
          { sigma: 10, mean_roster_points: 108, p_top4: 0.58, margin_vs_baseline: 24, ci_low: -10, ci_high: 45, seasons_positive: 3, sign_test_p: 0.375, per_season_margin: { '2021': 5, '2022': -2, '2023': 8, '2024': 6 }, simulation_se: 1 },
          { sigma: 20, mean_roster_points: 112, p_top4: 0.6, margin_vs_baseline: 28, ci_low: -5, ci_high: 50, seasons_positive: 3, sign_test_p: 0.375, per_season_margin: { '2021': 5, '2022': -2, '2023': 8, '2024': 6 }, simulation_se: 1 },
        ],
        verdict: 'better in three of four',
      },
    ],
  };
}

describe('orderedStrategiesFor', () => {
  it('always puts the baseline first, then sorts the rest by seasons-positive live from the export', () => {
    const ordered = orderedStrategiesFor(fixtureStrategies());
    expect(ordered.map((r) => r.key)).toEqual(['bpa_consensus', 'balanced', 'zero_rb']);
  });

  it('computes the margin range across all sigma settings, not just one', () => {
    const ordered = orderedStrategiesFor(fixtureStrategies());
    const zeroRb = ordered.find((r) => r.key === 'zero_rb')!;
    expect(zeroRb.marginRange).toEqual({ low: 20, high: 28 });
  });

  it('reads season dots from the sigma=10 cell, one fill/direction per season, never green for a negative season', () => {
    const ordered = orderedStrategiesFor(fixtureStrategies());
    const zeroRb = ordered.find((r) => r.key === 'zero_rb')!;
    // 2021 +5 (up), 2022 -2 (down), 2023 +8 (up), 2024 +6 (up)
    expect(zeroRb.seasonSigns).toEqual(['up', 'down', 'up', 'up']);
  });

  it('gives the baseline no margin range and no season dots -- there is nothing to measure it against itself', () => {
    const ordered = orderedStrategiesFor(fixtureStrategies());
    const baseline = ordered.find((r) => r.key === 'bpa_consensus')!;
    expect(baseline.marginRange).toBeNull();
    expect(baseline.seasonSigns).toBeNull();
  });
});

describe('rosterShapeSummary', () => {
  it('describes starters, flex and kicker live from league.json:roster, not a hardcoded example league', () => {
    expect(
      rosterShapeSummary({ starters: { QB: 1, RB: 2, WR: 3, TE: 1, DEF: 1, FLEX: 2 }, kicker: false }),
    ).toBe('10 starters, 2 flex, no kicker');
    expect(rosterShapeSummary({ starters: { QB: 1, RB: 2, WR: 2, TE: 1, DEF: 1, FLEX: 1 }, kicker: true })).toBe(
      '8 starters, 1 flex, 1 kicker',
    );
  });
});
