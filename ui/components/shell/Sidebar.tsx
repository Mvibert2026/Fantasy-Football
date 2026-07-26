/**
 * Left sidebar, ported from the prototype (lines 61-97), Prep branch only.
 *
 * The prototype also has a Season-mode sidebar variant (manager chips, week nav).
 * Season mode has no content in this app yet -- per scope, that is later work -- so
 * this component only ever renders the Prep list. The mode switcher in the top bar
 * still exists and is fully clickable; Draft and Season just show a plain "not
 * built" pane instead of a sidebar, which is a smaller and more honest surface than
 * scaffolding a season nav with nothing behind any of its items.
 *
 * Main nav and "coming soon" items share one id space and one active-state rule,
 * matching the prototype's own `navItem` helper (line 2130): both lists are built
 * from the same function, and `S.screen === id` decides the highlighted row in
 * either list. A soon item is "active" the same way a main nav item is.
 */

export type ScreenId =
  | 'board'
  | 'availability'
  | 'opponents'
  | 'strategy'
  | 'method'
  | 'sync'
  | 'bottomup'
  | 'news'
  | 'inseason'
  | 'startability';

export interface SoonItem {
  key: ScreenId;
  label: string;
  body: string;
}

/** Verbatim from the prototype's `nav` array (line 2128), same order. */
export const NAV_MAIN: Array<{ key: ScreenId; label: string }> = [
  { key: 'board', label: 'Board' },
  { key: 'availability', label: 'Availability' },
  { key: 'opponents', label: 'Opponents' },
  { key: 'strategy', label: 'Strategy Guide' },
  { key: 'method', label: 'Methodology' },
];

/** Verbatim from the prototype's `soon` array (line 2129), same order. Bodies are
 *  plain descriptions of the planned feature, not claims about this app's data. */
export const SOON_ITEMS: SoonItem[] = [
  {
    key: 'sync',
    label: 'Live league sync',
    body: 'Auto-mark picks from your live draft room instead of typing them in.',
  },
  {
    key: 'bottomup',
    label: 'Bottom-up projections',
    body: 'Player-level projections built from usage and matchup data, not just consensus rank.',
  },
  {
    key: 'news',
    label: 'News & injuries',
    body: 'Practice reports and status changes, each with a source and a timestamp.',
  },
  {
    key: 'inseason',
    label: 'In-season tools',
    body: 'Lineup, waiver and trade tools for managing the roster once the season starts.',
  },
  {
    key: 'startability',
    label: 'Startability scores',
    body: "A weekly per-player score against this league's startable threshold.",
  },
];

/** Enter/Space activation for the nav rows, which are divs (matching the
 *  prototype's onClick-div pattern) rather than buttons. Role and tabIndex are
 *  added on the elements themselves -- an accessibility attribute, not a style
 *  change, so it doesn't touch the ported visual treatment. */
function onActivate(fn: () => void) {
  return (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fn();
    }
  };
}

function navItemStyle(active: boolean): React.CSSProperties {
  return {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '9px 16px',
    fontSize: 14,
    cursor: 'pointer',
    color: active ? 'var(--txt)' : 'var(--dim)',
    background: active ? 'var(--panel2)' : 'transparent',
    borderLeft: `2px solid ${active ? 'var(--acc)' : 'transparent'}`,
    fontWeight: active ? 600 : 400,
  };
}

export function Sidebar({ screen, onScreen }: { screen: ScreenId; onScreen: (s: ScreenId) => void }) {
  return (
    <div
      style={{
        width: 216,
        flex: 'none',
        borderRight: '1px solid var(--line)',
        background: 'var(--panel)',
        overflowY: 'auto',
        padding: '14px 0',
      }}
    >
      <div
        style={{
          padding: '6px 16px',
          fontFamily: 'var(--font-num)',
          fontSize: 12,
          letterSpacing: '.12em',
          color: 'var(--dim2)',
        }}
      >
        PREP
      </div>
      {NAV_MAIN.map((n) => (
        <div
          key={n.key}
          role="button"
          tabIndex={0}
          aria-pressed={screen === n.key}
          onClick={() => onScreen(n.key)}
          onKeyDown={onActivate(() => onScreen(n.key))}
          style={navItemStyle(screen === n.key)}
        >
          {n.label}
        </div>
      ))}

      <div
        style={{
          padding: '20px 16px 6px',
          fontFamily: 'var(--font-num)',
          fontSize: 12,
          letterSpacing: '.12em',
          color: 'var(--dim2)',
        }}
      >
        COMING SOON
      </div>
      {SOON_ITEMS.map((n) => {
        const active = screen === n.key;
        return (
          <div
            key={n.key}
            role="button"
            tabIndex={0}
            aria-pressed={active}
            onClick={() => onScreen(n.key)}
            onKeyDown={onActivate(() => onScreen(n.key))}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 8,
              padding: '9px 16px',
              fontSize: 13.5,
              cursor: 'pointer',
              color: active ? 'var(--txt)' : 'var(--dim)',
              background: active ? 'var(--panel2)' : 'transparent',
              borderLeft: `2px solid ${active ? 'var(--acc)' : 'transparent'}`,
            }}
          >
            <span>{n.label}</span>
            <span
              style={{
                fontFamily: 'var(--font-num)',
                fontSize: 12,
                color: 'var(--soon)',
                border: '1px solid var(--soon)',
                padding: '0 4px',
              }}
            >
              SOON
            </span>
          </div>
        );
      })}
    </div>
  );
}
