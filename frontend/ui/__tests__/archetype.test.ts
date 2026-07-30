import { describe, expect, it } from 'vitest';
import {
  archetypeCovers,
  archetypeFor,
  archetypeLabel,
  archetypeShareOfPosition,
} from '../data/archetype';
import type { RawPlayerDescriptions } from '../data/types';

function pd(overrides: Partial<RawPlayerDescriptions> = {}): RawPlayerDescriptions {
  return {
    export_version: '1.0.0',
    license_tag: 'ai_generated',
    season: 2026,
    generated_utc: '2026-07-26T00:00:00Z',
    note: 'test fixture',
    players: [
      {
        player_id: 'gsis-1',
        player_name: 'Player One',
        season: 2026,
        position: 'RB',
        archetype: 'RB_COMMITTEE',
        confidence: 'high',
        description: 'Player One split carries last season.',
        license_tag: 'ai_generated',
        generated_at: '2026-07-26T00:00:00Z',
        source_stats: { carry_share: 0.4, target_share: 0.05, offense_pct: 0.5, adot: 0, games_qualified: 14 },
      },
      {
        player_id: 'gsis-2',
        player_name: 'Player Two',
        season: 2026,
        position: 'RB',
        archetype: 'RB_COMMITTEE',
        confidence: 'medium',
        description: 'Player Two also split carries.',
        license_tag: 'ai_generated',
        generated_at: '2026-07-26T00:00:00Z',
        source_stats: { carry_share: 0.35, target_share: 0.06, offense_pct: 0.45, adot: 0, games_qualified: 12 },
      },
      {
        player_id: 'gsis-3',
        player_name: 'Player Three',
        season: 2026,
        position: 'RB',
        archetype: 'RB_BELL_COW',
        confidence: 'high',
        description: 'Player Three carried the offense.',
        license_tag: 'ai_generated',
        generated_at: '2026-07-26T00:00:00Z',
        source_stats: { carry_share: 0.7, target_share: 0.1, offense_pct: 0.68, adot: 0, games_qualified: 16 },
      },
      {
        player_id: 'gsis-4',
        player_name: 'Player Four',
        season: 2026,
        position: 'WR',
        archetype: 'WR_ROTATIONAL',
        confidence: 'low',
        description: 'Player Four rotated snaps.',
        license_tag: 'ai_generated',
        generated_at: '2026-07-26T00:00:00Z',
        source_stats: { carry_share: 0, target_share: 0.1, offense_pct: 0.4, adot: 8, games_qualified: 10 },
      },
    ],
    ...overrides,
  };
}

describe('archetypeCovers', () => {
  it('covers RB, WR, TE and nothing else', () => {
    expect(archetypeCovers('RB')).toBe(true);
    expect(archetypeCovers('WR')).toBe(true);
    expect(archetypeCovers('TE')).toBe(true);
    expect(archetypeCovers('QB')).toBe(false);
  });
});

describe('archetypeFor', () => {
  it('is undefined when player_descriptions.json is not exported for this league (pd === null)', () => {
    expect(archetypeFor(null, 'gsis-1')).toBeUndefined();
  });

  it('is undefined when the board row has no gsis id to join on', () => {
    expect(archetypeFor(pd(), null)).toBeUndefined();
  });

  it('is undefined when the gsis id has no matching row (unclassified/undetermined)', () => {
    expect(archetypeFor(pd(), 'gsis-does-not-exist')).toBeUndefined();
  });

  it('finds the real row when the gsis id matches', () => {
    const entry = archetypeFor(pd(), 'gsis-3');
    expect(entry?.archetype).toBe('RB_BELL_COW');
  });
});

describe('archetypeLabel', () => {
  it('strips the position prefix and title-cases the rest', () => {
    expect(archetypeLabel('RB_COMMITTEE', 'RB')).toBe('Committee');
    expect(archetypeLabel('WR_FIELD_STRETCHER', 'WR')).toBe('Field Stretcher');
  });

  it('falls back to title-casing the whole string when the prefix does not match', () => {
    expect(archetypeLabel('SOME_OTHER_LABEL', 'RB')).toBe('Some Other Label');
  });
});

describe('archetypeShareOfPosition', () => {
  it('computes the live share among classified players at the same position, not all eligible players', () => {
    const share = archetypeShareOfPosition(pd(), 'RB', 'RB_COMMITTEE');
    // 2 of 3 classified RBs in the fixture carry RB_COMMITTEE.
    expect(share).toEqual({ n: 2, ofClassified: 3 });
  });

  it('is scoped to the position -- a WR row never pollutes an RB share', () => {
    const share = archetypeShareOfPosition(pd(), 'WR', 'WR_ROTATIONAL');
    expect(share).toEqual({ n: 1, ofClassified: 1 });
  });
});
