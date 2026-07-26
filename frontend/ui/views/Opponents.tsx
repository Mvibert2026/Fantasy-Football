import type { RawRoster } from '../data/types';
import type { Dataset } from '../data/load';

/**
 * Opponents, ported from the design handoff prototype's card layout (§7.3) --
 * built for the first time this pass; previously an explicit "not built" pane.
 *
 * The honest state, not a gap: opponents.json's own coverage_warning says 7 of 9
 * opponents have no behavioural data at all. This screen shows that plainly
 * rather than rendering three stacked null placeholders per card (§8's
 * multi-empty-section rule) -- each field that's null collapses into `data_status`,
 * which already names what's known and how, verbatim from the export.
 *
 * `positional_tendencies`, `first_pick_by_position` and `consensus_tracking_
 * behaviour` are marked "NOT A MODEL INPUT" where present, matching the
 * project's standing rule (docs/decisions.md, ADR-family on opponent modelling):
 * this is context a user can read and judge, never something the simulator
 * conditions on.
 *
 * `team_name` is null for 7 of the 9 real opponents -- caught writing this
 * file's test against the real export, not assumed from the shape sketched
 * earlier in this session. Rendered as "Slot N (no team name supplied)", never
 * a blank card or an invented name; `data_status` and (for 7 of 9) `team_name`
 * itself are identical strings repeated across several cards, which is a fact
 * about how little is known, not a rendering bug.
 *
 * Roster slot rows + STILL NEEDS chips (02-draft-opponents.md's card anatomy)
 * are wired from `rosters.json` (contract 1.8.0, docs/handoffs/016), added
 * 2026-07-26 as part of the frontend spec audit -- previously unreachable
 * because sync-exports.mjs was reading a stale shadow copy of data/export/, see
 * docs/frontend-audit-2026-07.md. `data.rosters` is null for any league export
 * older than 1.8.0 (this artifact isn't in the required per-league set); the
 * card then states plainly that roster data isn't available for this league,
 * rather than a blank section or an invented "0 of everything" row.
 */

const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
  DEF: 'var(--def)',
};

/** `QB×qb, RB×rb, WR×wr, TE×te, DEF×def` order per the spec's slot order --
 *  FLEX is rendered separately, right after, since its eligible-position set
 *  differs from a single-position starter row. */
const STARTER_ORDER = ['QB', 'RB', 'WR', 'TE', 'DEF'];

export function Opponents({ data }: { data: Dataset }) {
  const o = data.opponents;
  const rostersBySlot = new Map((data.rosters?.rosters ?? []).map((r) => [r.team_slot, r]));

  return (
    <div className="stack">
      <section>
        <h2>Opponents</h2>
        <p className="notice">{o.coverage_warning}</p>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(232px, 1fr))', gap: 12 }}>
        {o.opponents.map((opp, i) => {
          const hasContext =
            opp.positional_tendencies || opp.first_pick_by_position || opp.consensus_tracking_behaviour;
          return (
            <div
              key={`${opp.draft_slot_2026}-${i}`}
              style={{
                border: `1px solid ${opp.holds_picks_19_to_22 ? 'var(--acc)' : 'var(--line)'}`,
                background: 'var(--panel)',
                padding: '14px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span
                  style={{
                    fontSize: 15,
                    fontWeight: 600,
                    flex: 1,
                    color: opp.team_name === null ? 'var(--dim2)' : 'var(--txt)',
                    fontStyle: opp.team_name === null ? 'italic' : 'normal',
                  }}
                >
                  {opp.team_name ?? `Slot ${opp.draft_slot_2026} (no team name supplied)`}
                </span>
                <span className="num" style={{ fontSize: 12, color: 'var(--dim2)' }}>
                  slot {opp.draft_slot_2026}
                </span>
              </div>
              {opp.holds_picks_19_to_22 ? (
                <span
                  style={{
                    alignSelf: 'flex-start',
                    fontSize: 10,
                    letterSpacing: '.08em',
                    color: 'var(--acc)',
                    border: '1px solid var(--acc)',
                    padding: '1px 6px',
                  }}
                >
                  BETWEEN YOUR PICKS
                </span>
              ) : null}

              <div className="num" style={{ fontSize: 11, color: 'var(--dim2)' }}>
                known picks: {opp.known_picks_2026.join(', ')}
              </div>

              <RosterSection roster={rostersBySlot.get(opp.draft_slot_2026) ?? null} />

              {hasContext ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {opp.positional_tendencies ? (
                    <Field label="TENDENCIES" value={opp.positional_tendencies} />
                  ) : null}
                  {opp.first_pick_by_position ? (
                    <Field label="FIRST PICK BY POSITION" value={opp.first_pick_by_position} />
                  ) : null}
                  {opp.consensus_tracking_behaviour ? (
                    <Field label="CONSENSUS ADHERENCE" value={opp.consensus_tracking_behaviour} />
                  ) : null}
                  <div style={{ fontSize: 9.5, letterSpacing: '.06em', color: 'var(--dim2)' }}>
                    NOT A MODEL INPUT -- context only
                  </div>
                </div>
              ) : null}

              <div style={{ marginTop: 2, paddingTop: 8, borderTop: '1px solid var(--line)' }}>
                <div style={{ fontSize: 10, letterSpacing: '.08em', color: 'var(--dim2)' }}>DATA STATUS</div>
                <div style={{ marginTop: 4, fontSize: 12.5, lineHeight: 1.5, color: 'var(--dim)' }}>
                  {opp.data_status}
                </div>
                {opp.notes ? (
                  <div style={{ marginTop: 6, fontSize: 12, lineHeight: 1.5, color: 'var(--dim)' }}>{opp.notes}</div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={{ fontSize: 9.5, letterSpacing: '.06em', color: 'var(--dim2)' }}>{label}</div>
      <div style={{ fontSize: 12.5, color: 'var(--txt)' }}>{value}</div>
    </div>
  );
}

/** Starter slot rows + FLEX + a "N/M starters · K on bench" footer, then the
 *  STILL NEEDS chips -- 02-draft-opponents.md's card anatomy. `roster` is null
 *  when this league predates rosters.json (contract 1.8.0): render the honest
 *  absence rather than a blank section or an invented all-zero roster. */
function RosterSection({ roster }: { roster: RawRoster | null }) {
  if (!roster) {
    return (
      <div style={{ fontSize: 11.5, color: 'var(--dim2)' }}>
        Roster data not available for this league — rosters.json (contract 1.8.0+) was not exported
        for it.
      </div>
    );
  }

  const { starters, flex, bench } = roster.roster_slots;
  const starterRows = STARTER_ORDER.filter((pos) => starters[pos]).map((pos) => ({
    pos,
    ...starters[pos]!,
  }));
  const totalStarterSlots =
    starterRows.reduce((sum, s) => sum + s.required, 0) + flex.required;
  const filledStarterSlots =
    starterRows.reduce((sum, s) => sum + s.filled, 0) + flex.filled;

  const needsChips = Object.entries(roster.needs).filter(
    ([pos, n]) => STARTER_ORDER.includes(pos) && n > 0,
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {starterRows.map((s) => (
        <RosterSlotRow key={s.pos} label={s.pos} color={POSITION_COLOR[s.pos] ?? 'var(--txt)'} group={s} />
      ))}
      <RosterSlotRow label="FLEX" color="var(--dim2)" group={flex} />

      <div style={{ marginTop: 2, fontSize: 11, color: 'var(--dim2)' }}>
        <span className="num">
          {filledStarterSlots} / {totalStarterSlots}
        </span>{' '}
        starters ·{' '}
        <span className="num">
          {bench.filled} / {bench.required}
        </span>{' '}
        on bench
      </div>

      {needsChips.length > 0 ? (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 2 }}>
          <span style={{ fontSize: 9.5, letterSpacing: '.06em', color: 'var(--dim2)', alignSelf: 'center' }}>
            STILL NEEDS
          </span>
          {needsChips.map(([pos, n]) => (
            <span
              key={pos}
              className="num"
              style={{
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: '.045em',
                color: POSITION_COLOR[pos] ?? 'var(--txt)',
                border: `1px solid ${POSITION_COLOR[pos] ?? 'var(--line2)'}`,
                borderRadius: 6,
                padding: '1px 7px',
              }}
            >
              {pos} ×{n}
            </span>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: 11, color: 'var(--dim2)', marginTop: 2 }}>Starters complete.</div>
      )}
    </div>
  );
}

function RosterSlotRow({
  label,
  color,
  group,
}: {
  label: string;
  color: string;
  group: { required: number; filled: number; players: string[] };
}) {
  const empty = group.filled === 0;
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        paddingLeft: 8,
        borderLeft: `2px solid ${empty ? 'var(--line)' : color}`,
      }}
    >
      <span style={{ width: 34, fontSize: 10.5, fontWeight: 600, letterSpacing: '.045em', color }}>{label}</span>
      <span
        className={empty ? undefined : 'num'}
        style={{ flex: 1, fontSize: 12, color: empty ? 'var(--dim2)' : 'var(--txt)', fontStyle: empty ? 'italic' : 'normal' }}
      >
        {empty ? 'empty' : group.players.join(', ')}
      </span>
      <span className="num" style={{ fontSize: 10.5, color: 'var(--dim2)' }}>
        {group.filled}/{group.required}
      </span>
    </div>
  );
}
