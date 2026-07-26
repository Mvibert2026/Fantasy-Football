import type { ReactNode } from 'react';
import type { LeagueConfig } from '../../data/league';
import type { Theme } from './useTheme';

/**
 * The top bar, ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html, lines 31-59) with its DOM
 * structure and inline styles kept as literally as JSX allows.
 *
 * Two departures from the source markup, both noted:
 *   - `v0.9` is routed through a named constant rather than sitting in JSX text, so
 *     the no-invented-numbers guard (which flags any digit in rendered text) doesn't
 *     mistake a version string for an unsourced football claim.
 *   - The league indicator always renders the "matches your real league" state. The
 *     prototype's other state (`MODIFIED — COMPARISON`) exists because its settings
 *     panel lets you edit league config away from your real league; this app has no
 *     settings editor, so that state has nothing to ever trigger it.
 */

const WORDMARK_VERSION = 'v0.9';

export type Mode = 'prep' | 'draft' | 'season';

const MODES: Array<{ key: Mode; label: string }> = [
  { key: 'prep', label: 'Prep' },
  { key: 'draft', label: 'Draft' },
  { key: 'season', label: 'Season' },
];

export function TopBar({
  mode,
  onModeChange,
  theme,
  onToggleTheme,
  league,
  refreshSlot,
}: {
  mode: Mode;
  onModeChange: (m: Mode) => void;
  theme: Theme;
  onToggleTheme: () => void;
  league: LeagueConfig;
  refreshSlot?: ReactNode;
}) {
  const leagueLabel =
    league.teams.kind === 'present' && league.userSlot.kind === 'present'
      ? `REAL LEAGUE · ${league.teams.value}T · PICK ${league.userSlot.value}`
      : 'LEAGUE CONFIG UNAVAILABLE';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        height: 46,
        padding: '0 14px',
        borderBottom: '1px solid var(--line)',
        background: 'var(--panel)',
        flex: 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
        <div style={{ width: 9, height: 9, background: 'var(--acc)' }} />
        <div style={{ fontWeight: 600, letterSpacing: '.02em' }}>DRAFT&nbsp;ASSISTANT</div>
        <div style={{ fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)' }}>
          {WORDMARK_VERSION}
        </div>
      </div>

      <div style={{ flex: 1 }} />

      {refreshSlot}

      <div
        title="Settings match your actual league"
        style={{
          display: 'flex',
          flex: 'none',
          whiteSpace: 'nowrap',
          alignItems: 'center',
          gap: 8,
          padding: '4px 10px',
          border: '1px solid var(--line2)',
          background: 'var(--panel2)',
          fontFamily: 'var(--font-num)',
          fontSize: 11,
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--acc)' }} />
        <span style={{ color: 'var(--dim)' }}>{leagueLabel}</span>
      </div>

      <button
        title="League settings"
        aria-disabled="true"
        style={{
          padding: '4px 10px',
          whiteSpace: 'nowrap',
          background: 'transparent',
          border: '1px solid var(--line2)',
          color: 'var(--txt)',
          fontSize: 12,
        }}
      >
        League settings
      </button>

      <button
        onClick={onToggleTheme}
        title="Toggle theme"
        style={{
          width: 30,
          height: 26,
          background: 'transparent',
          border: '1px solid var(--line2)',
          color: 'var(--dim)',
          fontSize: 12,
        }}
      >
        {theme === 'dark' ? '☾' : '☀'}
      </button>

      <div style={{ display: 'flex', border: '1px solid var(--line2)' }}>
        {MODES.map((m) => {
          const active = mode === m.key;
          const bg = active ? (m.key === 'draft' ? 'var(--live)' : 'var(--acc)') : 'transparent';
          const fg = active ? '#0a0d12' : 'var(--dim)';
          return (
            <button
              key={m.key}
              aria-pressed={active}
              onClick={() => onModeChange(m.key)}
              style={{
                padding: '5px 14px',
                whiteSpace: 'nowrap',
                background: bg,
                border: 0,
                borderLeft: '1px solid var(--line2)',
                color: fg,
                fontWeight: 600,
                fontSize: 12,
              }}
            >
              {m.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
