import { describe, expect, it } from 'vitest';
import { historyScoringNote } from '../components/PlayerDetail';

/**
 * Contract 1.16.0 fix: `weekly_finishes.json` / `season_stats.json` used to carry a
 * hardcoded caveat claiming "standard PPR, not this league's own ruleset" -- true
 * before the backend's FR-079/FR-083 fix, false now that both files are re-scored
 * under the exporting league's real `cfg.scoring`. `historyScoringNote` replaces
 * that hardcoded claim with one built from the fetched file's own envelope fields.
 */

describe('historyScoringNote', () => {
  const envelope = {
    league_id: 'primary',
    scoring_ruleset_note: "Westwood's verified custom ruleset (stacking yardage bonuses, ADR-052).",
  };

  it('states the real ruleset with no mismatch caveat when the fetched file matches the loaded league', () => {
    const note = historyScoringNote(envelope, 'primary');
    expect(note).toContain("Westwood's verified custom ruleset");
    expect(note).not.toContain('not the currently-selected league');
  });

  it('never claims "standard PPR" unconditionally -- the old, now-false caveat text', () => {
    expect(historyScoringNote(envelope, 'primary')).not.toContain('standard PPR');
    expect(historyScoringNote(envelope, null)).not.toContain('standard PPR');
  });

  it('flags a real mismatch honestly when the fetched envelope is a different league than the one on screen', () => {
    const note = historyScoringNote(envelope, 'espn_10_standard');
    expect(note).toContain('primary');
    expect(note).toContain('espn_10_standard');
    expect(note).toContain('not the currently-selected league');
  });

  it('flags the unknown case (currentLeagueId not yet resolved) rather than assuming a match', () => {
    const note = historyScoringNote(envelope, null);
    expect(note).toContain('not the currently-selected league');
  });
});
