import { useState, type ReactNode } from 'react';

/**
 * The assistant's home in the shell: an anchored, collapsed pill by default, ported
 * from the prototype (lines 1258-1274) -- expanding to a fixed-position panel with
 * the same header treatment (dot, "Assistant" label, close control).
 *
 * This component owns only position and open/closed state. Everything inside the
 * open panel is the existing <Assistant /> view, unmodified -- its routing,
 * tagging and retrieval logic are a separate concern from where it lives on screen.
 *
 * The prototype's open-panel header also has an "offline" simulation toggle, used
 * to demo the assistant's offline behaviour for design review. That is a prototype
 * convenience with no equivalent state in this app (offline here means the actual
 * network, not a simulated flag) and is not ported.
 */

export function AssistantDock({ where, children }: { where: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);

  if (!open) {
    return (
      <div
        onClick={() => setOpen(true)}
        style={{
          position: 'fixed',
          right: 18,
          bottom: 18,
          zIndex: 86,
          display: 'flex',
          alignItems: 'center',
          gap: 9,
          padding: '9px 14px',
          background: 'var(--panel)',
          border: '1px solid var(--line2)',
          borderRadius: 'var(--r-m)',
          cursor: 'pointer',
          boxShadow: 'var(--sh)',
        }}
      >
        <span style={{ width: 7, height: 7, background: 'var(--acc)' }} />
        <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap' }}>Assistant</span>
        <span style={{ fontFamily: 'var(--font-num)', fontSize: 11, color: 'var(--dim2)', whiteSpace: 'nowrap' }}>
          {where}
        </span>
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        right: 18,
        bottom: 18,
        width: 430,
        maxHeight: '72vh',
        zIndex: 86,
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--panel)',
        border: '1px solid var(--line2)',
        borderRadius: 'var(--r-m)',
        overflow: 'hidden',
        boxShadow: 'var(--sh)',
      }}
    >
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

      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', padding: 13 }}>
        {children}
      </div>
    </div>
  );
}
