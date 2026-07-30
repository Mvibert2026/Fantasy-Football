import { useRef, useState, type ReactNode } from 'react';
import { useDismissOnOutsideOrEscape } from '../../lib/dismiss';

/**
 * The assistant's home in the shell: an anchored, collapsed pill by default, ported
 * from the prototype (lines 1258-1274) -- expanding to a fixed-position panel with
 * the same header treatment (dot, "Assistant" label, close control).
 *
 * This component owns only position, sizing and open/closed state. Everything inside
 * the open panel is the existing <Assistant /> view, unmodified -- its routing,
 * tagging and retrieval logic are a separate concern from where it lives on screen.
 *
 * The prototype's open-panel header also has an "offline" simulation toggle, used
 * to demo the assistant's offline behaviour for design review. That is a prototype
 * convenience with no equivalent state in this app (offline here means the actual
 * network, not a simulated flag) and is not ported.
 *
 * FR-077-followup (docs/design/ASSISTANT-WINDOW.md, design round 2026-07-31 item 4):
 * the founder's actual complaint -- "needs to have a constant window to be able to
 * continue the conversation, it also doesn't allow for scrolling" -- was two container
 * defects, not a behaviour gap (the behaviour, per the same complaint, had already
 * improved):
 *
 *   1. `children` (the <Assistant/> instance, which owns the conversation's
 *      question/answer/history state) was only ever rendered while `open` was true.
 *      Collapsing set `open=false`, which made this component return the pill markup
 *      alone -- `children` fell out of the reconciled tree and React unmounted it,
 *      destroying the conversation. "Continuing" a conversation requires the state
 *      that holds it to survive a collapse, so `children` is now ALWAYS rendered;
 *      only its visibility (`display`) toggles. Never conditionally return before
 *      `children` -- that is the one invariant this file exists to protect.
 *   2. The open panel sized itself with `maxHeight: '72vh'` and no `top`, so its
 *      flex children's `flex: 1` had no definite height to distribute against --
 *      content grew past the visual max and the outer `overflow: hidden` clipped it
 *      silently, with `.answers`' own `overflow: auto` (base.css) never engaging
 *      because it was never given a bounded box to overflow within. Setting both
 *      `top` and `bottom` on a `position: fixed` element gives the browser a
 *      DEFINITE height (viewport height minus both margins) with no `vh` fraction
 *      involved -- exactly the fix, and it is why the container now fills "to a
 *      bottom margin" rather than a viewport fraction.
 */

/** 46px TopBar (TopBar.tsx) + 18px gap, so the panel never sits under the bar. */
const TOP_OFFSET = 64;
const BOTTOM_MARGIN = 18;

/**
 * 520px, the spec's floor, not its 720px ceiling. Measured against the app after
 * item 1 (trace mode) shipped: that change already removed the six inline
 * `[page.*]` citation tokens and the raw provenance footer from assistant prose
 * (`stripInlineCitations`, `ui/data/traceMode.tsx`) -- the actual source of the
 * cramped feeling the design brief diagnosed. What's left at 520px (verified by
 * screenshot, `frontend/e2e/artifacts/`) wraps a three-player answer onto lines
 * that hold a name and a number together without truncation. 720px would cost
 * real board on a 1180px laptop screen for a legibility problem the cleanup
 * already mostly solved; ship the floor, not the ceiling.
 */
const PANEL_WIDTH = 520;

export function AssistantDock({ where, children }: { where: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement | null>(null);

  // Thread 073 dismissible-surface audit: the expanded dock previously only
  // collapsed via its own "—" button -- no click-outside, no Escape. Collapses
  // to the pill (not a destructive close -- there is no other state to lose)
  // matching the existing minimize affordance exactly.
  useDismissOnOutsideOrEscape(panelRef, open, () => setOpen(false));

  return (
    <div
      ref={panelRef}
      style={{
        position: 'fixed',
        right: 18,
        zIndex: 86,
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--panel)',
        border: '1px solid var(--line2)',
        borderRadius: 'var(--r-m)',
        boxShadow: 'var(--sh)',
        ...(open
          ? { top: TOP_OFFSET, bottom: BOTTOM_MARGIN, width: PANEL_WIDTH, overflow: 'hidden' }
          : { bottom: 18, width: 'auto', maxWidth: '92vw' }),
      }}
    >
      {open ? (
        <>
          <div
            style={{
              flex: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: 9,
              padding: '10px 13px',
              borderBottom: '1px solid var(--line)',
            }}
          >
            <span style={{ width: 7, height: 7, background: 'var(--acc)' }} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Assistant</span>
            <span style={{ flex: 1 }} />
            <span
              onClick={() => setOpen(false)}
              role="button"
              aria-label="Collapse assistant"
              style={{
                cursor: 'pointer',
                fontFamily: 'var(--font-num)',
                fontSize: 11,
                color: 'var(--dim2)',
                border: '1px solid var(--line2)',
                padding: '1px 7px',
              }}
            >
              —
            </span>
          </div>

          <div
            style={{
              flex: 'none',
              padding: '7px 13px',
              borderBottom: '1px solid var(--line)',
              background: 'var(--panel2)',
              fontFamily: 'var(--font-num)',
              fontSize: 10,
              color: 'var(--dim2)',
            }}
          >
            {where}
          </div>
        </>
      ) : (
        <div
          onClick={() => setOpen(true)}
          role="button"
          aria-label="Open assistant"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 9,
            padding: '9px 14px',
            cursor: 'pointer',
          }}
        >
          <span style={{ width: 7, height: 7, background: 'var(--acc)' }} />
          <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap' }}>Assistant</span>
          <span style={{ fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)', whiteSpace: 'nowrap' }}>
            {where}
          </span>
        </div>
      )}

      {/*
       * `children` -- the <Assistant/> view and the question/answer/history state
       * it owns -- is rendered on every render of this component, collapsed or
       * open. Only `display` changes. This is the one line "never unmounts" comes
       * down to: remove this from the tree in either branch above instead, and
       * the conversation is destroyed on every collapse, silently, with no error
       * and no test failure unless something asserts the state survived.
       */}
      <div
        style={{
          display: open ? 'flex' : 'none',
          flexDirection: 'column',
          flex: 1,
          minHeight: 0,
          padding: open ? 13 : 0,
        }}
      >
        {children}
      </div>
    </div>
  );
}
