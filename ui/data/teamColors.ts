/**
 * NFL team brand colours, FRONTEND-SPEC.md §6.9. Used only for the identity chip
 * and the initials-on-team-colour placeholder where a headshot would go -- never
 * as a data colour, so it can't collide with the app's two reserved accents.
 */
export const TEAM_COLOR: Record<string, string> = {
  ARI: '#97233f',
  ATL: '#a71930',
  BAL: '#241773',
  BUF: '#00338d',
  CAR: '#0085ca',
  CHI: '#0b162a',
  CIN: '#fb4f14',
  CLE: '#ff3c00',
  DAL: '#041e42',
  DEN: '#fb4f14',
  DET: '#0076b6',
  GB: '#203731',
  HOU: '#03202f',
  IND: '#002c5f',
  JAX: '#006778',
  KC: '#e31837',
  LV: '#a5acaf',
  LAC: '#0080c6',
  LAR: '#003594',
  MIA: '#008e97',
  MIN: '#4f2683',
  NE: '#002244',
  NO: '#d3bc8d',
  NYG: '#0b2265',
  NYJ: '#125740',
  PHI: '#004c54',
  PIT: '#ffb612',
  SF: '#aa0000',
  SEA: '#69be28',
  TB: '#d50a0a',
  TEN: '#4b92db',
  WAS: '#5a1414',
};

export function teamColorOf(team: string): string {
  return TEAM_COLOR[team] ?? 'var(--dim2)';
}

/** First letters of up to the first two words, uppercased -- the initials-on-
 *  team-colour fallback for a headshot that doesn't exist (§6.9: no player in
 *  this board has a real ESPN id, so every card renders this state, not a
 *  fabricated image). */
export function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/);
  return parts
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('');
}
