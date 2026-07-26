/**
 * The placeholder screen, ported from the prototype's "Coming soon" screen header
 * (lines 746-753) -- title, badge, one line of body copy. The prototype's version
 * also renders an illustrative sample-data grid beneath the header for the
 * Consistency screen specifically; that is content work (sample data, a heat-map
 * component) rather than shell, so it is not ported here.
 *
 * Reused for every screen this app does not implement yet: the sidebar's five
 * COMING SOON items, Availability and Opponents (out of scope per the project
 * brief, but not permanently ruled out), and Draft/Season mode.
 */

export function NotBuilt({ title, body, badge = 'COMING SOON' }: { title: string; body: string; badge?: string }) {
  return (
    <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
      <div
        style={{
          padding: '20px 23px',
          borderBottom: '1px solid var(--line)',
          background: 'var(--panel)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 16, fontWeight: 600 }}>{title}</span>
            <span
              style={{
                fontFamily: 'var(--font-num)',
                fontSize: 12,
                whiteSpace: 'nowrap',
                color: 'var(--soon)',
                border: '1px solid var(--soon)',
                padding: '1px 8px',
              }}
            >
              {badge}
            </span>
          </div>
          <div style={{ marginTop: 7, fontSize: 14, lineHeight: 1.6, color: 'var(--dim)', maxWidth: 720 }}>
            {body}
          </div>
        </div>
      </div>
    </div>
  );
}
