import type { LeagueConfig } from '../../data/league';
import { Value } from '../Value';
import { integer } from '../../lib/format';

/**
 * FR-069 / FR-040 / `docs/design/LEAGUE-SETTINGS-BOUNDARY.md`.
 *
 * The spec's absolute rule: "the screen must not accept a setting it cannot apply."
 * Two classes, not two sections of one form -- one is a form (editable, applies on
 * change, no save button), the other is a read-only statement (no inputs at all).
 *
 * Where this build genuinely diverges from the spec's own assumption, and why (a
 * real conflict between the written spec and what this app can do, resolved by
 * following the code per this session's dispatch instructions, not by silently
 * building to the stale assumption):
 *
 * The spec's "applies immediately" class names THREE fields as editable and
 * "recomputable in the browser from what the board already ships": roster shape,
 * team count, draft slot. That is true of draft slot alone. `board.json`'s VBD and
 * `league.json`'s replacement levels are computed server-side against this league's
 * real season data (`src/scoring.py`, `src/replacement_levels` -- see
 * `league.replacementLevelsNote`) -- they are NOT pure arithmetic over team count, so
 * there is nothing for a changed team count or roster shape to recompute against in
 * the browser. Accepting an edit to either would be exactly the failure this spec's
 * absolute rule exists to prevent: a setting that looks live but cannot actually
 * apply. So both render read-only here too, next to the genuinely-editable draft
 * slot, not as disabled form fields (a disabled field still says "this is a thing you
 * set here" -- the spec's own reasoning for why scoring gets a statement, not a
 * greyed-out form). Flagged to design/backend via a handoff thread rather than
 * silently deviating from the written spec.
 *
 * FR-069's own further ask -- collapsing the league dropdown to "my three leagues
 * plus Custom" and retiring the 24-preset matrix -- is a separate, larger,
 * backend-dependent change (`src/generate_config_matrix.py`, `src/league_builder.py`
 * becoming the primary path) and is NOT built here; this panel is scoped to
 * LEAGUE-SETTINGS-BOUNDARY.md's boundary rule for whichever league is already
 * selected in the switcher above it.
 */

function fieldLabel(position: string): string {
  return position === 'FLEX' ? 'FLEX' : position;
}

export function SettingsPanel({
  league,
  onClose,
  DraftSlotControl,
}: {
  league: LeagueConfig | null;
  onClose: () => void;
  /** DraftSlotControl is TopBar's own private component, already bound to its
   *  onSelectSlot/onClearSlot handlers -- passed in as a closure rather than
   *  duplicated, so there is exactly one implementation of "the editable draft slot
   *  control" and this panel and the top bar's own pill can never disagree about
   *  what it looks like or how it behaves. */
  DraftSlotControl: () => JSX.Element;
}) {
  return (
    <>
      <div
        data-testid="settings-backdrop"
        onClick={onClose}
        style={{ position: 'fixed', inset: 0, zIndex: 95, background: 'transparent' }}
      />
      <div
        role="dialog"
        aria-label="Settings"
        style={{
          position: 'fixed',
          top: 46,
          right: 14,
          width: 380,
          maxWidth: '92vw',
          maxHeight: 'calc(100vh - 60px)',
          overflowY: 'auto',
          zIndex: 96,
          background: 'var(--panel)',
          border: '1px solid var(--line2)',
          boxShadow: 'var(--sh)',
          padding: 16,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 700, letterSpacing: '.04em' }}>SETTINGS</span>
          <span style={{ flex: 1 }} />
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: '1px solid var(--line2)', color: 'var(--dim)', padding: '2px 8px', fontSize: 12 }}
          >
            esc
          </button>
        </div>

        {!league ? (
          <p className="notice" style={{ marginTop: 12, fontSize: 12 }}>
            League configuration is not loaded yet.
          </p>
        ) : (
          <>
            {/* Applies immediately -- the one genuinely editable field. */}
            <div style={{ marginTop: 14, fontSize: 10, letterSpacing: '.1em', color: 'var(--dim2)' }}>
              DRAFT SLOT — applies immediately
            </div>
            <p style={{ marginTop: 4, fontSize: 11, color: 'var(--dim2)', lineHeight: 1.4 }}>
              No save button, no confirmation -- nothing is submitted anywhere. Recomputed in the browser
              from league.json:pick_sequence's own snake-order arithmetic.
            </p>
            <div style={{ marginTop: 8 }}>
              <DraftSlotControl />
            </div>

            {/* Read-only facts -- team count and roster shape, per this file's own
                doc comment on why they are NOT editable here despite the spec. */}
            <div style={{ marginTop: 16, fontSize: 10, letterSpacing: '.1em', color: 'var(--dim2)' }}>
              LEAGUE — read-only
            </div>
            <div style={{ marginTop: 6, fontSize: 12.5, lineHeight: 1.6 }}>
              <div>
                Teams <Value cell={league.teams} render={integer} /> · Rounds{' '}
                <Value cell={league.rounds} render={integer} />
              </div>
              <div>
                {league.platform.kind === 'present' ? league.platform.value : '—'} ·{' '}
                {league.draftType.kind === 'present' ? league.draftType.value : '—'}
              </div>
              <div>
                Roster:{' '}
                {league.thresholds
                  .map((t) => `${fieldLabel(t.position)} ${t.starters.kind === 'present' ? integer(t.starters.value) : '—'}`)
                  .join(' · ')}
              </div>
              <div>
                Playoffs: top <Value cell={league.playoffTeams} render={integer} /> ·{' '}
                {league.playoffReseeding ? 'reseeding' : 'no reseeding'}
              </div>
            </div>
            <p className="notice" style={{ marginTop: 8, fontSize: 10.5, lineHeight: 1.5 }}>
              Team count and roster shape are not editable here. Changing them would require rebuilding
              the board's VBD and replacement levels against real season data -- both are computed
              server-side, not arithmetic over team count alone -- so nothing here could actually apply a
              change. Draft slot above is the one field this build can genuinely recompute client-side.
            </p>

            {/* Cannot apply when hosted -- a statement, not a form. No inputs. */}
            <div style={{ marginTop: 16, fontSize: 10, letterSpacing: '.1em', color: 'var(--dim2)' }}>
              SCORED UNDER
            </div>
            <p style={{ marginTop: 6, fontSize: 12.5, lineHeight: 1.5 }}>
              <Value cell={league.scoringRulesetNote} render={(v) => v} />
            </p>
            <p className="notice" style={{ marginTop: 6, fontSize: 10.5 }}>
              The board ships final points, not the components underneath, so scoring cannot be changed
              here. It changes when the board is rebuilt.
            </p>
          </>
        )}
      </div>
    </>
  );
}
