/**
 * The account-wide watchlist, FRONTEND-SPEC.md §6.10 -- distinct from the
 * draft-scoped queue in ui/data/draft.ts. Persists across seasons and leagues;
 * never disappears on its own. Keyed by player name (this app's stable identity
 * for a board row; see ui/data/board.ts), not by league, so a player watched
 * while looking at one league's board is still watched after switching leagues.
 */

const STORAGE_KEY = 'prep.watchlist';

export function loadWatchlist(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

export function saveWatchlist(names: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(names));
  } catch {
    // Persistence is a nicety; a failed write just means the list resets next load.
  }
}

export function toggleWatchlist(current: string[], name: string): string[] {
  return current.includes(name) ? current.filter((n) => n !== name) : [...current, name];
}
