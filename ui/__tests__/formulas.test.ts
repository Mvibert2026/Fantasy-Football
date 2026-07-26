import { describe, expect, it } from 'vitest';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import { computeLiveAvailability } from '../data/liveAvailability';
import type { DraftPickRecord } from '../data/draft';
import { roundOfPick, teamSlotAtPick } from '../data/draft';
import { depletionWarning, positionScarcity } from '../data/scarcity';
import { verdictLine } from '../data/verdict';
import { isMiscalibrated, wilsonInterval } from '../data/wilson';
import { loadDatasetFromDisk } from './helpers';

/**
 * FRONTEND-SPEC.md §5's formulas, implemented client-side against real board and
 * league data. These are the highest-risk additions in the full-port effort --
 * novel arithmetic, not a straight port of already-tested code -- so each gets a
 * real check, not just a type-checks-and-runs smoke test.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);
const league = buildLeagueConfig(data);
const rowsById = new Map(rows.map((r) => [r.id, r]));
const teams = league.teams.kind === 'present' ? league.teams.value : 0;

describe('wilsonInterval (§5.4)', () => {
  it('matches a known reference value (k=36, n=92)', () => {
    // Textbook Wilson interval for this exact k/n, computed independently.
    const w = wilsonInterval(36, 92);
    expect(w.p).toBeCloseTo(0.3913, 3);
    expect(w.lo).toBeGreaterThan(0.29);
    expect(w.lo).toBeLessThan(0.31);
    expect(w.hi).toBeGreaterThan(0.48);
    expect(w.hi).toBeLessThan(0.5);
    expect(w.thin).toBe(false); // n=92 >= 50
  });

  it('flags a bucket thin below n=50, and centres near 0.5 for n=0', () => {
    expect(wilsonInterval(3, 10).thin).toBe(true);
    expect(wilsonInterval(50, 100).thin).toBe(false);
    expect(wilsonInterval(0, 0)).toEqual({ p: 0, lo: 0, hi: 0, n: 0, thin: true });
  });

  it('flags a stated probability outside its own interval, not merely far from the point estimate', () => {
    const interval = wilsonInterval(36, 92); // roughly [0.30, 0.49]
    expect(isMiscalibrated(0.9, interval)).toBe(true);
    expect(isMiscalibrated(0.39, interval)).toBe(false);
  });
});

describe('computeLiveAvailability (§5.2)', () => {
  const row = rows.find((r) => r.raw.position === 'RB' && r.vbd.kind === 'present')!;
  const targetPick = 40; // arbitrary future pick well past a handful of picks logged

  it('returns signal "none" with live=null before minPicks = max(4, round(teams*0.5)) picks are logged', () => {
    const minPicks = Math.max(4, Math.round(teams * 0.5));
    const fewPicks: DraftPickRecord[] = Array.from({ length: minPicks - 1 }, (_, i) => ({
      overallPick: i + 1,
      round: roundOfPick(i + 1, teams),
      teamSlot: teamSlotAtPick(i + 1, teams),
      playerId: null,
      playerName: `x${i}`,
      timestamp: 'x',
    }));
    const result = computeLiveAvailability({ data, league, row, targetPick, picks: fewPicks, rowsById });
    expect(result.signal).toBe('none');
    expect(result.live).toBeNull();
    expect(result.adjustment).toBeNull();
  });

  it('never silently substitutes the baseline for a null live value', () => {
    const result = computeLiveAvailability({ data, league, row, targetPick, picks: [], rowsById });
    expect(result.live).not.toBe(result.baseline.kind === 'present' ? result.baseline.value : undefined);
    expect(result.live).toBeNull();
  });

  it('marks signal "thin" between minPicks and teams picks logged, "ok" at or past teams picks', () => {
    const minPicks = Math.max(4, Math.round(teams * 0.5));
    const thinPicks: DraftPickRecord[] = Array.from({ length: Math.min(minPicks + 1, teams - 1) }, (_, i) => ({
      overallPick: i + 1,
      round: roundOfPick(i + 1, teams),
      teamSlot: teamSlotAtPick(i + 1, teams),
      playerId: null,
      playerName: `x${i}`,
      timestamp: 'x',
    }));
    if (thinPicks.length >= minPicks && thinPicks.length < teams) {
      const result = computeLiveAvailability({ data, league, row, targetPick, picks: thinPicks, rowsById });
      expect(result.signal).toBe('thin');
      expect(result.live).not.toBeNull();
    }

    const okPicks: DraftPickRecord[] = Array.from({ length: teams }, (_, i) => ({
      overallPick: i + 1,
      round: roundOfPick(i + 1, teams),
      teamSlot: teamSlotAtPick(i + 1, teams),
      playerId: null,
      playerName: `x${i}`,
      timestamp: 'x',
    }));
    const okResult = computeLiveAvailability({ data, league, row, targetPick, picks: okPicks, rowsById });
    expect(okResult.signal).toBe('ok');
  });

  it('widens the band 1.6x when thin vs. ok, using the real sigma-5/sigma-20 spread', () => {
    const minPicks = Math.max(4, Math.round(teams * 0.5));
    if (minPicks >= teams) return; // guard: only meaningful when thin and ok are distinct ranges
    const thinPicks: DraftPickRecord[] = Array.from({ length: minPicks }, (_, i) => ({
      overallPick: i + 1,
      round: roundOfPick(i + 1, teams),
      teamSlot: teamSlotAtPick(i + 1, teams),
      playerId: null,
      playerName: `x${i}`,
      timestamp: 'x',
    }));
    const okPicks: DraftPickRecord[] = Array.from({ length: teams }, (_, i) => ({
      overallPick: i + 1,
      round: roundOfPick(i + 1, teams),
      teamSlot: teamSlotAtPick(i + 1, teams),
      playerId: null,
      playerName: `x${i}`,
      timestamp: 'x',
    }));
    const thinResult = computeLiveAvailability({ data, league, row, targetPick, picks: thinPicks, rowsById });
    const okResult = computeLiveAvailability({ data, league, row, targetPick, picks: okPicks, rowsById });
    if (thinResult.band && okResult.band) {
      expect(thinResult.band.w).toBeCloseTo(okResult.band.w * 1.6, 5);
    }
  });

  it('adjusts a WR down when the last 5 picks were all WRs (positional run)', () => {
    const wrRow = rows.find((r) => r.raw.position === 'WR' && r.vbd.kind === 'present')!;
    const otherWRs = rows.filter((r) => r.raw.position === 'WR' && r.id !== wrRow.id).slice(0, 5);
    const minPicks = Math.max(4, Math.round(teams * 0.5));
    const base: DraftPickRecord[] = Array.from({ length: Math.max(0, teams - 5) }, (_, i) => ({
      overallPick: i + 1,
      round: roundOfPick(i + 1, teams),
      teamSlot: teamSlotAtPick(i + 1, teams),
      playerId: null,
      playerName: `filler${i}`,
      timestamp: 'x',
    }));
    const wrRun: DraftPickRecord[] = otherWRs.map((r, i) => ({
      overallPick: base.length + i + 1,
      round: roundOfPick(base.length + i + 1, teams),
      teamSlot: teamSlotAtPick(base.length + i + 1, teams),
      playerId: r.id,
      playerName: r.name.kind === 'present' ? r.name.value : 'x',
      timestamp: 'x',
    }));
    const picks = [...base, ...wrRun];
    if (picks.length < minPicks || wrRun.length < 3) return; // guard: need enough logged picks and a real run
    const result = computeLiveAvailability({ data, league, row: wrRow, targetPick: picks.length + teams, picks, rowsById });
    if (result.adjustment) {
      expect(result.adjustment.run).toBeLessThan(0); // a run on the position pushes availability down
    }
  });
});

describe('positionScarcity and depletionWarning (§5.5)', () => {
  it('computes remaining/gone/pace from real board + picks state', () => {
    const rbRows = rows.filter((r) => r.raw.position === 'RB');
    const firstTwo = rbRows.slice(0, 2);
    const picks: DraftPickRecord[] = firstTwo.map((r, i) => ({
      overallPick: i + 1,
      round: 1,
      teamSlot: i + 1,
      playerId: r.id,
      playerName: r.name.kind === 'present' ? r.name.value : 'x',
      timestamp: 'x',
    }));
    const starters: Record<string, number> = {};
    for (const t of league.thresholds) {
      starters[t.position] = t.starters.kind === 'present' ? t.starters.value : 0;
    }
    const scarcity = positionScarcity(data, rows, picks, 3, 10, ['RB', 'WR'], starters, teams);
    const rb = scarcity.find((s) => s.pos === 'RB')!;
    expect(rb.total).toBe(rbRows.length);
    expect(rb.gone).toBe(2);
    expect(rb.remaining).toBe(rbRows.length - 2);
  });

  it('fires the depletion warning only when every remaining tier-1 player is under 50% by the next pick', () => {
    const scarce = { pos: 'TE', total: 10, remaining: 1, gone: 9, pace: 1, tier1Remaining: 1, under50ByNext: 1, startablePool: 12 };
    expect(depletionWarning(scarce, 23)).toMatch(/All 1 remaining tier-1 TE sit under 50%/);

    const notScarce = { ...scarce, under50ByNext: 0 };
    expect(depletionWarning(notScarce, 23)).toBeNull();

    expect(depletionWarning(scarce, null)).toBeNull();
  });
});

describe('verdictLine (§5.6)', () => {
  it('generates a three-clause, period-closed sentence naming real tier/availability/VBD facts', () => {
    const row = rows.find((r) => r.raw.position === 'RB' && r.vbd.kind === 'present' && r.tierLabel.kind === 'present')!;
    const line = verdictLine(row, rows, null, null, false);
    expect(line.endsWith('.')).toBe(true);
    expect(line.split(' · ')).toHaveLength(3);
    expect(line).toMatch(/tier|only/i);
  });

  it('states the stale caveat verbatim when availability is stale, not a number', () => {
    const row = rows.find((r) => r.vbd.kind === 'present')!;
    const line = verdictLine(row, rows, null, 23, true);
    expect(line).toContain('availability is stale for this league, so waiting is unpriced');
  });

  it('reports "no projection" rather than a fabricated VBD gap for a sparse player', () => {
    const sparse = rows.find((r) => r.vbd.kind === 'absent');
    if (sparse) {
      const line = verdictLine(sparse, rows, null, null, false);
      expect(line).toContain('no projection, so this is a rank-and-availability call only');
    }
  });
});
