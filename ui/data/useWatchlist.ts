import { useCallback, useState } from 'react';
import { loadWatchlist, saveWatchlist, toggleWatchlist } from './watchlist';

export function useWatchlist(): [string[], (name: string) => void] {
  const [watchlist, setWatchlist] = useState<string[]>(loadWatchlist);

  const toggle = useCallback((name: string) => {
    setWatchlist((current) => {
      const next = toggleWatchlist(current, name);
      saveWatchlist(next);
      return next;
    });
  }, []);

  return [watchlist, toggle];
}
