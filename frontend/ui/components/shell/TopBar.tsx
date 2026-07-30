import { useEffect, useState, type ReactNode } from 'react';
import { randomSlot } from '../../data/draftSlot';
import type { LeagueConfig } from '../../data/league';
import type { SelectableLeague } from '../../data/league-registry';
import type { LeagueTrack } from '../../data/types';
import { useTraceMode } from '../../data/traceMode';
import { SettingsPanel } from './SettingsPanel';
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

/**
 * design/TWO-TRACK-EXPRESSION.md: plain-text (never colour-coded -- `--acc`
 * already means "good, better than baseline" elsewhere in this system, see
 * SUPPLIED-VALUES.md) description of which track a league is on, shown before
 * the league is ever loaded. Two real tracks exist today; a third ("not yet")
 * is named in the design spec but reserved -- no league in this export is in
 * that state, so there is no branch for it here.
 *
 * Two forms of the same fact: the full sentence design's mockup shows (used in
 * the title, and anywhere with room to spare -- see Methodology's own scoring-
 * ruleset section for the full `scoring_ruleset_note` prose), and a short label
 * for the top bar itself, which was already tight before this existed (a real
 * export's freshness note and league-detail string both already truncate at
 * this app's usual screenshot width). Principle #4 -- density is the product --
 * cuts against spending that little remaining width on a second full sentence
 * next to information already on screen; the short label plus the option-list
 * markers below carry the same distinction, and the full sentence is one hover
 * away rather than gone.
 */
function trackFullDescriptor(track: LeagueTrack): string {
  return track.isPrimary
    ? `primary track · full ruleset · ${track.opponentsModelledCount ?? '—'} opponents modelled`
    : 'generic track · standard scoring · opponents not modelled';
}

function trackBadgeLabel(track: LeagueTrack): string {
  return track.isPrimary ? 'PRIMARY' : 'GENERIC';
}

/** Short marker prefixed to each option's own text, so the distinction is visible
 *  inside the dropdown itself before a selection is made -- not only after. */
function trackMarker(track: LeagueTrack | undefined): string {
  if (!track) return '';
  return track.isPrimary ? '● ' : '○ ';
}

/** Full text for the badge's title attribute -- the sourced field and its
 *  verbatim value, never just the compact label with nothing behind it. The
 *  field-path lines are gated by the "show data sources" switch; the plain
 *  descriptor sentence is not sourcing text and stays either way. */
function trackTitle(track: LeagueTrack, showSources: boolean): string {
  if (!showSources) return trackFullDescriptor(track);
  const idNote = track.isPrimary ? 'league.json:league_id === "primary"' : 'league.json:league_id !== "primary"';
  const noteText = track.scoringRulesetNote ?? '(this export predates league.json:scoring_ruleset_note)';
  return `${trackFullDescriptor(track)}\n${idNote}\nleague.json:scoring_ruleset_note: ${noteText}`;
}

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

  // design/TWO-TRACK-EXPRESSION.md: undefined on a manifest written before the
  // `track` field existed, or for the standalone build's single static entry --
  // the badge simply doesn't render then, exactly today's UI.
  const activeTrack = leagues.find((l) => l.id === leagueId)?.track;

  // FR-114 (docs/design/PROVENANCE-DISCLOSURE.md): the "show data sources" switch's
  // persistent on-screen indicator -- so a screenshot is never ambiguous about which
  // mode produced it -- plus the value this bar's own field-path tooltip (trackTitle)
  // is gated on.
  const { on: showSources } = useTraceMode();

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

      {/* FR-114: persistent indicator, shown only while the switch is on, so a
          screenshot (the founder's own primary review method, per
          docs/operating-model.md) is never ambiguous about which view produced it.
          Deliberately not `--acc`/`--live` -- this is a mode, not a "good" signal or
          a live-data state, so it gets its own neutral, unmissable-but-quiet treatment. */}
      {showSources ? (
        <div
          data-testid="show-data-sources-indicator"
          title="Field paths and export citations are visible. Alt+T or Settings to turn off."
          style={{
            display: 'flex',
            flex: 'none',
            whiteSpace: 'nowrap',
            alignItems: 'center',
            gap: 6,
            padding: '3px 9px',
            border: '1px solid var(--dim)',
            color: 'var(--dim)',
            fontSize: 10.5,
            fontWeight: 600,
            letterSpacing: '.08em',
          }}
        >
          DATA SOURCES SHOWN
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
            // See the slot <select> below for why this is a token and not
            // `transparent`: an author background of `transparent` makes Chrome
            // draw the popup list in the system default rather than following
            // :root's `color-scheme`.
            background: 'var(--panel2)',
            border: 0,
            color: 'var(--dim)',
            fontFamily: 'var(--font-num)',
            fontSize: 11,
            textTransform: 'uppercase',
          }}
        >
          {leagues.map((l) => (
            <option key={l.id} value={l.id} style={{ background: 'var(--panel2)', color: 'var(--txt)' }}>
              {trackMarker(l.track)}
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
        {activeTrack ? (
          <span
            className="num"
            data-testid="league-track"
            title={trackTitle(activeTrack, showSources)}
            style={{
              flex: 'none',
              letterSpacing: '.06em',
              color: activeTrack.isPrimary ? 'var(--txt)' : 'var(--dim2)',
              borderLeft: '1px solid var(--line2)',
              paddingLeft: 8,
              whiteSpace: 'nowrap',
            }}
          >
            {trackBadgeLabel(activeTrack)}
          </span>
        ) : null}
      </div>

      {onSelectSlot && onClearSlot ? <DraftSlotControl league={league} onSelectSlot={onSelectSlot} onClearSlot={onClearSlot} /> : null}

      {/* FR-069 / FR-040 / LEAGUE-SETTINGS-BOUNDARY.md: this used to render
          "Settings — not built" per design/INERT-CONTROLS.md's rule for a
          control that cannot act. It can act now -- see SettingsPanel.tsx for
          the editable/read-only boundary it enforces, and its own doc comment
          for where it deliberately departs from the written spec and why. */}
      {onSelectSlot && onClearSlot ? (
        <SettingsButton league={league} onSelectSlot={onSelectSlot} onClearSlot={onClearSlot} />
      ) : (
        <span
          title="Settings needs a draft-slot override handler, which the standalone build does not wire up."
          style={{ padding: '4px 2px', whiteSpace: 'nowrap', color: 'var(--dim2)', fontSize: 12 }}
        >
          Settings — not available in this build
        </span>
      )}

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
          // NOT `transparent`. Chrome renders a <select>'s popup list using the
          // author background when one is set, and a transparent author
          // background resolves to the system default -- a white list on a dark
          // page, which is what the founder reported 2026-07-30 (light mode
          // looked correct, which is the tell: :root's `color-scheme: dark` was
          // being overridden by the author background, not missing). An explicit
          // panel token makes the closed control read the same as before and the
          // popup follow the theme.
          background: 'var(--panel2)',
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
          // Options need the background too: Chrome inherits the select's, but
          // Firefox does not and falls back to the system list colours.
          <option key={n} value={n} style={{ background: 'var(--panel2)', color: 'var(--txt)' }}>
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

/**
 * FR-069 / FR-040 / LEAGUE-SETTINGS-BOUNDARY.md: opens SettingsPanel.tsx.
 * Escape and a click on the transparent backdrop both close it, same dismiss
 * pattern as PlayerDetail's side sheet (`ui/components/PlayerDetail.tsx`) --
 * one convention for "how a floating panel closes" in this app, not a second one.
 */
function SettingsButton({
  league,
  onSelectSlot,
  onClearSlot,
}: {
  league: LeagueConfig | null;
  onSelectSlot: (slot: number) => void;
  onClearSlot: () => void;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open]);

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-pressed={open}
        aria-label="Settings"
        title="League settings -- what's editable here and what isn't (LEAGUE-SETTINGS-BOUNDARY.md)"
        style={{
          padding: '4px 10px',
          whiteSpace: 'nowrap',
          background: open ? 'var(--panel2)' : 'transparent',
          border: `1px solid ${open ? 'var(--line2)' : 'transparent'}`,
          color: 'var(--dim)',
          fontSize: 12,
        }}
      >
        Settings
      </button>
      {open ? (
        <SettingsPanel
          league={league}
          onClose={() => setOpen(false)}
          DraftSlotControl={() => <DraftSlotControl league={league} onSelectSlot={onSelectSlot} onClearSlot={onClearSlot} />}
        />
      ) : null}
    </>
  );
}
