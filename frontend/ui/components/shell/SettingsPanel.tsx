import type { LeagueConfig } from '../../data/league';
import { useTraceMode } from '../../data/traceMode';
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
 * team count, draft slot. That is unambiguously true of draft slot. It is NOT simply
 * true or false of team count/roster shape -- and an earlier draft of this file
 * claimed it was flatly impossible ("VBD needs server-side season data"), which
 * FR-040's own analysis already refutes: replacement level for a different team
 * count is just reading a different rank off the SAME per-player `projected_points`
 * the board already ships, and VBD from there is arithmetic. That correction is
 * recorded here, not silently fixed, because getting it wrong once already cost a
 * false claim in this exact file.
 *
 * The REAL blocker is narrower and specific: `league.json:flex_split_assumption` /
 * `flex_split_note` -- how many of this league's flex slots each position actually
 * wins -- is a MEASURED quantity (26-season simulation, ADR-029), tied to THIS
 * league's exact roster shape (2 flex slots among RB/WR/TE). A different team count
 * or flex count needs that measurement re-run, not a formula; a naive recompute that
 * just moves the replacement-level cutoff would silently drop the measured
 * assumption and produce a number that reads as this league's methodology while not
 * being it. Building this honestly needs either a written, labelled approximation
 * rule or a real re-simulation -- neither exists yet, so neither field is editable
 * here. Both render read-only next to the genuinely-editable draft slot, not as
 * disabled form fields (a disabled field still says "this is a thing you set here"
 * -- the spec's own reasoning for why scoring gets a statement, not a greyed-out
 * form). Flagged to design/backend via a handoff thread rather than silently
 * deviating from the written spec.
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
  const { on: showSources, setOn: setShowSources } = useTraceMode();
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

        {/* FR-114 (docs/design/PROVENANCE-DISCLOSURE.md): the global "show data
            sources" switch. App-wide, not per-league, so it sits above the
            league-scoped sections below. Default off -- the clean view is the one
            used live during a draft; this is the one turned on when a number looks
            wrong. `Alt+T` is the faster path to the same boolean (ui/data/traceMode.tsx);
            this checkbox is the discoverable one. Founder's own words for the label,
            never "provenance"/"trace"/"field path". */}
        <div style={{ marginTop: 14, fontSize: 10, letterSpacing: '.1em', color: 'var(--dim2)' }}>
          DISPLAY
        </div>
        <label
          style={{
            marginTop: 8,
            display: 'flex',
            alignItems: 'flex-start',
            gap: 8,
            cursor: 'pointer',
          }}
        >
          <input
            type="checkbox"
            checked={showSources}
            onChange={(e) => setShowSources(e.target.checked)}
            style={{ marginTop: 2 }}
          />
          <span>
            <span style={{ fontSize: 12.5 }}>Show data sources</span>
            <p className="notice" style={{ marginTop: 2, fontSize: 10.5, lineHeight: 1.4 }}>
              Shows exactly which export field each number on screen came from. Off by default; turn
              it on when a number looks wrong and you want to check it. Nothing that explains why a
              value is missing is ever hidden by this -- only the field citations are. Also toggled by{' '}
              <span className="num">Alt+T</span>.
            </p>
          </span>
        </label>

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
              Team count and roster shape are not editable here. Not because VBD itself is unreachable
              client-side -- it isn't, a different replacement-level cutoff is arithmetic on the
              projected points already shipped -- but because how many flex slots each position wins
              (league.json:flex_split_note) was MEASURED for this league's own shape (26 seasons, ADR-029),
              not derived from a formula. A different roster shape needs that measurement re-run, not
              guessed, so nothing here changes it yet. Draft slot above is the one field this build can
              genuinely recompute client-side today.
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
