import { useCallback, useEffect, useState } from 'react';

/**
 * Theme state, ported from the prototype's own mechanism: a `data-theme` attribute
 * set directly on the root element (no `prefers-color-scheme` involvement -- the
 * prototype's toggle is the sole source of truth, and default is dark).
 */

export type Theme = 'dark' | 'light';

const STORAGE_KEY = 'prep.theme';

function readStored(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === 'light' ? 'light' : 'dark';
  } catch {
    return 'dark';
  }
}

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(readStored);

  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Persistence is a nicety; a failed write just means the default returns next load.
    }
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((t) => (t === 'dark' ? 'light' : 'dark'));
  }, []);

  return [theme, toggle];
}
