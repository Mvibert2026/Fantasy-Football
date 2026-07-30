import type { ReactNode } from 'react';
import { randomSlot } from '../../data/draftSlot';
import type { LeagueConfig } from '../../data/league';
import type { SelectableLeague } from '../../data/league-registry';
import type { Theme } from './useTheme';

/**
 * The top bar, ported from the design handoff prototype
 * (design_handoff_draft_assistant/Draft Assistant.dc.html, lines 31-59) with its DOM
 * structure and inline styles kept as literally as JSX allows.
 *
 * Departures from the source markup, each noted:
 *   - `v0.9` is routed through a named constant rather than sitting in JSX text, so
 *     the no-invented-numbers guard (which flags any digit in rendered text) doesn't
 *     mistake a version string for an unsourced football claim.
 *   - The static "REAL LEAGUE · 10T · PICK 3" pill is now a switcher. The prototype
 *     has no multi-league concept at all (it has a settings panel that edits the one
 *     league away from "real", producing a `MODIFIED — COMPARISON` state this app
 *     still has no trigger for, since there's no settings editor). The switcher is
 *     new, driven by whatever public/data/_leagues.json actually lists -- today
 *     that's just the default league, so it renders as a single, honest option
 *     rather than a dropdown implying choices that don't exist yet.
 */

const WORDMARK_VERSION = 'v0.9';

export type Mode = 'prep' | 'draft' | 'season';

const DEFAULT_MODES: Array<{ key: Mode; label: string }> = [
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
  leagues,
  leagueId,
  onSelectLeague,
  onSelectSlot,
  onClearSlot,
  refreshSlot,
  modes = DEFAULT_MODES,
}: {
  mode: Mode;
  onModeChange: (m: Mode) => void;
  theme: Theme;
  onToggleTheme: () => void;
  /** Null while a league is (re)loading, or after a load error -- the switcher
   *  itself must keep working in both cases, so it can't require this to be present. */
  league: LeagueConfig | null;
  leagues: SelectableLeague[];
  leagueId: string;
  onSelectLeague: (id: string) => void;
  /** FR-034: sets a local draft-slot override for the current league. Optional so the
   *  standalone build (ui/StandaloneApp.tsx) can render this bar with no override
   *  affordance at all rather than a control that silently does nothing. */
  onSelectSlot?: (slot: number) => void;
  onClearSlot?: () => void;
  refreshSlot?: ReactNode;
  /**
   * Which mode buttons render, defaulting to all three. The standalone build
   * (ui/StandaloneApp.tsx) passes just Prep -- Draft mode is the live-draft
   * loop and Season mode has no content, and neither can work from a frozen
   * static file, so they are absent there rather than present-but-inert.
   */
  modes?: Array<{ key: Mode; label: string }>;
}) {
  // Thread 058 section C3: a fuller identity string -- platform and draft
  // type, both real league.json fields (confirmed against the export;
  // ui/data/league.ts now plumbs them), placed ahead of the team/pick detail
  // that was already here. Each piece renders only when present rather than
  // guessing a value for an older export.
  const leagueDetail =
    league && league.teams.kind === 'present' && league.userSlot.kind === 'present'
      ? [
          league.platform.kind === 'present' ? league.platform.value : null,
          league.draftType.kind === 'present' ? league.draftType.value : null,
          `${league.teams.value}T · PICK ${league.userSlot.value}`,
        ]
          .filter((part): part is string => part !== null)
          .join(' · ')
      : league
        ? 'CONFIG UNAVAILABLE'
        : 'LOADING…';

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

      {/* Thread 058 section C2: a DRAFT LIVE badge, matching the design's
          `isDraft` gate (docs/design-reference/prototype.dc.html line 41) --
          shown whenever Draft mode is the active mode. The prototype has no
          further state than this (no separate "dormant board" distinction
          within Draft mode -- confirmed by reading its source: `isDraft:S.draft`
          is the only condition gating this badge), so this is the one state
          that exists to build, not a partial port of a richer state machine. */}
      {mode === 'draft' ? (
        <div
          style={{
            display: 'flex',
            flex: 'none',
            whiteSpace: 'nowrap',
            alignItems: 'center',
            gap: 7,
            padding: '3px 9px',
            border: '1px solid var(--live)',
            color: 'var(--live)',
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: '.08em',
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--live)', animation: 'ffpulse 1.6s infinite' }} />
          DRAFT LIVE
        </div>
      ) : null}

      <div style={{ flex: 1 }} />

      {refreshSlot}

      <div
        title="Switch which league's data is loaded"
        style={{
          display: 'flex',
          minWidth: 0,
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
        <span style={{ flex: 'none', width: 6, height: 6, borderRadius: '50%', background: 'var(--acc)' }} />
        {/* A native <select> sizes its closed box to its widest <option>, not the
            selected value -- with league names like "ESPN-default, 14 teams,
            standard scoring" in the list, that blew this pill out past 500px wide
            regardless of which league was actually selected. Capping the width and
            eliding the rest keeps the box tied to what's showing, not to the
            longest thing that could show. */}
        <select
          aria-label="Select league"
          value={leagueId}
          onChange={(e) => onSelectLeague(e.target.value)}
          style={{
            flex: 'none',
            maxWidth: 130,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            background: 'transparent',
            border: 0,
            color: 'var(--dim)',
            fontFamily: 'var(--font-num)',
            fontSize: 11,
            textTransform: 'uppercase',
          }}
        >
          {leagues.map((l) => (
            <option key={l.id} value={l.id}>
              {l.label}
            </option>
          ))}
        </select>
        <span
          style={{
            color: 'var(--dim2)',
            minWidth: 0,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {leagueDetail}
        </span>
      </div>

      {onSelectSlot && onClearSlot ? <DraftSlotControl league={league} onSelectSlot={onSelectSlot} onClearSlot={onClearSlot} /> : null}

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
        {modes.map((m) => {
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

/**
 * FR-034: draft-slot selector, present in both Prep and Draft since this bar is mounted
 * for every mode (App.tsx only swaps the body below it). Minimal clicks by design -- one
 * select, one optional clear, one optional randomise -- and nothing here ever hides the
 * board behind a modal, matching FR-036's same "usable during a live draft" requirement.
 *
 * Range is strictly `1..teams` from the loaded league, never a hardcoded fallback (e.g.
 * 1-12) -- when `teams` isn't a present Cell yet (loading, or an export that predates
 * it), this renders a disabled placeholder that says so instead of guessing a range.
 *
 * Overridden vs. sourced is never the same visual treatment (Principle #1/#2, and the
 * same rule FR-036 states explicitly for typed opponent names): the accent colour and
 * the "· sourced N" suffix only appear when `league.userSlotOverridden` is true, and the
 * clear ("x") button only exists in that state, since "clear" is meaningless otherwise.
 */
function DraftSlotControl({
  league,
  onSelectSlot,
  onClearSlot,
}: {
  league: LeagueConfig | null;
  onSelectSlot: (slot: number) => void;
  onClearSlot: () => void;
}) {
  if (!league || league.teams.kind !== 'present') {
    return (
      <div
        title="Draft slot selection needs league.json:teams, which isn't loaded yet."
        style={{
          display: 'flex',
          flex: 'none',
          alignItems: 'center',
          gap: 6,
          padding: '4px 10px',
          border: '1px solid var(--line2)',
          color: 'var(--dim2)',
          fontFamily: 'var(--font-num)',
          fontSize: 11,
        }}
      >
        SLOT — (no team count yet)
      </div>
    );
  }

  const teams = league.teams.value;
  const effective = league.userSlot.kind === 'present' ? league.userSlot.value : null;
  const overridden = league.userSlotOverridden;
  const sourced = league.userSlotSourced.kind === 'present' ? league.userSlotSourced.value : null;
  const options = Array.from({ length: teams }, (_, i) => i + 1);

  return (
    <div
      title={
        overridden
          ? `Draft slot overridden locally. league.json's own value is ${sourced ?? '—'}.`
          : "Your draft slot for this league. Overriding it here doesn't touch league.json -- it's local to this browser."
      }
      style={{
        display: 'flex',
        flex: 'none',
        whiteSpace: 'nowrap',
        alignItems: 'center',
        gap: 6,
        padding: '4px 10px',
        // SUPPLIED-VALUES.md: the border no longer turns --acc on override --
        // green already means "good, positive, better than baseline" on this
        // board (the delta colour), and a slot you set yourself is neither.
        // Supplied-ness now reads through the dotted underline on the value
        // and the "set by you" marker below, never a semantic accent.
        border: '1px solid var(--line2)',
        background: 'var(--panel2)',
        fontFamily: 'var(--font-num)',
        fontSize: 11,
      }}
    >
      <span style={{ color: 'var(--dim2)', letterSpacing: '.05em' }}>SLOT</span>
      <select
        aria-label="Your draft slot"
        value={effective ?? ''}
        onChange={(e) => onSelectSlot(Number(e.target.value))}
        style={{
          flex: 'none',
          background: 'transparent',
          // Dotted underline is the one and only "you put this here" signal
          // in this app (SUPPLIED-VALUES.md) -- applied to the select itself
          // since there's no separate span to underline around a live control.
          border: 0,
          borderBottom: overridden ? '1px dotted var(--line2)' : '1px solid transparent',
          color: 'var(--txt)',
          fontFamily: 'var(--font-num)',
          fontSize: 11,
          fontWeight: 600,
        }}
      >
        {options.map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
      {overridden ? (
        <>
          {/* "set by you" -- the lowercase marker naming how this value got
              here, replacing the accent-coloured "· sourced N" text. The
              sourced value itself stays visible (kept, per the spec: "where a
              supplied value overrides a sourced one, the sourced value stays
              visible in the same control"). */}
          <span style={{ color: 'var(--dim2)', fontSize: 10 }}>· set by you, league file says {sourced ?? '—'}</span>
          <button
            onClick={onClearSlot}
            title="Clear override, back to league.json's value"
            aria-label="Clear draft slot override"
            style={{
              flex: 'none',
              width: 16,
              height: 16,
              lineHeight: '14px',
              padding: 0,
              background: 'transparent',
              border: '1px solid var(--line2)',
              color: 'var(--dim2)',
              fontSize: 10,
            }}
          >
            ×
          </button>
        </>
      ) : null}
      <button
        onClick={() => onSelectSlot(randomSlot(teams))}
        title="Rehearse prep from a random slot"
        aria-label="Randomise draft slot"
        style={{
          flex: 'none',
          padding: '1px 6px',
          background: 'transparent',
          border: '1px solid var(--line2)',
          color: 'var(--dim)',
          fontSize: 10,
        }}
      >
        rand
      </button>
    </div>
  );
}
