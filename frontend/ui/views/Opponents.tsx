import { useEffect, useRef, useState } from 'react';
import { pickNumbersForSlot } from '../data/draft';
import { clearOpponentName, loadOpponentNames, saveOpponentName, type OpponentNameMap } from '../data/opponentNames';
import type { RawRoster, RawRosters } from '../data/types';
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
 * FR-036 (docs/founder-requests/FR-036-manual-team-name-entry-for-opponents-in-the-
 * draf.md): a typed name (ui/data/opponentNames.ts, `OpponentNameField` below) can now
 * cover that null, or override a real `opponents.json` name, for a live draft where
 * the founder is matching a real platform's team names to slots by eye. Local, per-
 * league storage, click-to-edit inline (no modal), names only -- nothing here reaches
 * the availability model, the recommendation, or `positional_tendencies`/etc.'s "NOT A
 * MODEL INPUT" context fields above. A typed name never renders through the same
 * styling as a sourced one (accent colour + a "typed" tag + a clear control that
 * reverts to the sourced name, never to blank) -- Principle #1/#2's supplied-vs-
 * derived rule, same as FR-034's slot override.
 *
 * Roster slot rows + STILL NEEDS chips (02-draft-opponents.md's card anatomy)
 * are wired from `rosters.json` (contract 1.8.0, docs/handoffs/016), added
 * 2026-07-26 as part of the frontend spec audit -- previously unreachable
 * because sync-exports.mjs was reading a stale shadow copy of data/export/, see
 * docs/frontend-audit-2026-07.md. `data.rosters` is null for any league export
 * older than 1.8.0 (this artifact isn't in the required per-league set); the
 * card then states plainly that roster data isn't available for this league,
 * rather than a blank section or an invented "0 of everything" row.
 *
 * `next #N` in the card header (02-draft-opponents.md's card anatomy, thread
 * 027) is pure snake-order arithmetic, not a prediction: rosters.json's
 * `picks_ingested` (how many real, is_mock=0 picks have been logged so far)
 * plus league.json's `teams`/`rounds` and the opponent's own `draft_slot_2026`
 * feed the same `pickNumbersForSlot` helper DraftRoom/PlayerDetail already use
 * for the user's own next pick (ui/data/draft.ts) -- imported read-only here,
 * not duplicated. Three distinct states, per Principle #2: no rosters.json for
 * this league renders no badge at all (the roster section below already says
 * why); rosters.json present but this team has no picks left within the
 * league's round count renders `next --`; otherwise the real upcoming overall
 * pick number. This is only "whose turn arithmetic says is next," which is
 * public schedule math, never an inference about what a team will do.
 */

const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
  DEF: 'var(--def)',
};

/** `QB, RB, WR, TE` order per the spec's slot order, up to FLEX. DEF and FLEX
 *  are rendered separately right after (see RosterSection) -- the spec's full
 *  order is `QB, RB, WR, TE, FLEX, DEF`, with FLEX BEFORE DEF, confirmed
 *  against both the written spec and the reference screenshot's row order,
 *  not after it as an earlier pass here had it. */
const STARTER_ORDER = ['QB', 'RB', 'WR', 'TE'];

/** Positions the STILL NEEDS chips can render for, per the spec's `want`
 *  formula (QB/RB/WR/TE/DEF -- FLEX is absorbed into the RB/WR +1, never its
 *  own chip). Kept separate from STARTER_ORDER above so moving DEF out of the
 *  row-rendering order doesn't silently drop its needs chip too. */
const CHIP_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'DEF'];

/** Pure arithmetic: the next overall pick number at which `slot` is on the
 *  clock, given how many real picks have been logged so far. `undefined`
 *  (distinct from `null`) means "no rosters.json for this league" -- see the
 *  module doc for the three-state trace. */
function nextPickForOpponent(
  rosters: RawRosters | null,
  teams: number,
  rounds: number,
  slot: number,
): number | null | undefined {
  if (!rosters) return undefined;
  const current = rosters.picks_ingested + 1;
  return pickNumbersForSlot(teams, slot, rounds).find((p) => p >= current) ?? null;
}

export function Opponents({ data }: { data: Dataset }) {
  const o = data.opponents;
  const rostersBySlot = new Map((data.rosters?.rosters ?? []).map((r) => [r.team_slot, r]));
  const teams = data.league.teams;
  const rounds = data.league.rounds;

  // FR-036: typed opponent names, local and per-league. `data.league.league_id` is the
  // same field ui/data/load.ts already validates every artifact against, so this key
  // matches whichever league is actually loaded, not whichever league was loaded when
  // the component first mounted.
  const leagueId = data.league.league_id ?? 'default';
  const [names, setNames] = useState<OpponentNameMap>(() => loadOpponentNames(leagueId));
  useEffect(() => {
    setNames(loadOpponentNames(leagueId));
  }, [leagueId]);

  function setName(slot: number, name: string) {
    setNames(saveOpponentName(leagueId, slot, name));
  }
  function clearName(slot: number) {
    setNames(clearOpponentName(leagueId, slot));
  }

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
          const nextPick = nextPickForOpponent(data.rosters, teams, rounds, opp.draft_slot_2026);
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
                <OpponentNameField
                  slot={opp.draft_slot_2026}
                  sourcedName={opp.team_name}
                  typedName={names[opp.draft_slot_2026]}
                  onSave={(name) => setName(opp.draft_slot_2026, name)}
                  onClear={() => clearName(opp.draft_slot_2026)}
                />
                {nextPick === undefined ? null : (
                  <span
                    className="num"
                    style={{ fontSize: 11.5, letterSpacing: '.04em', color: 'var(--dim2)', whiteSpace: 'nowrap' }}
                  >
                    next{' '}
                    <span style={{ color: 'var(--txt)', fontWeight: 600 }}>
                      {nextPick === null ? '—' : `#${nextPick}`}
                    </span>
                  </span>
                )}
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

/**
 * FR-036: click-to-edit inline, never a modal -- the card stays fully visible the whole
 * time, so this works mid-draft without hiding the board. Three visually distinct
 * states, matching the project's supplied-vs-derived rule:
 *
 *   - Typed name present: accent-coloured, "typed" tag, an edit (pencil) control and a
 *     clear ("x") control that reverts to `sourcedName` -- never to blank, per FR-036.
 *   - No typed name, `sourcedName` present: unchanged from before this feature --
 *     normal weight/colour, a real `opponents.json` value.
 *   - Neither: the pre-existing italic "Slot N (no team name supplied)" placeholder,
 *     now also carrying an edit control so an unnamed slot in a league with no
 *     opponents.json at all (ESPN/Yahoo configs) is exactly as fast to name.
 */
function OpponentNameField({
  slot,
  sourcedName,
  typedName,
  onSave,
  onClear,
}: {
  slot: number;
  sourcedName: string | null;
  typedName: string | undefined;
  onSave: (name: string) => void;
  onClear: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  function startEdit() {
    setDraft(typedName ?? sourcedName ?? '');
    setEditing(true);
  }
  function commit() {
    onSave(draft);
    setEditing(false);
  }
  function cancel() {
    setEditing(false);
  }

  if (editing) {
    return (
      <span style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 4 }}>
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commit();
            if (e.key === 'Escape') cancel();
          }}
          onBlur={commit}
          placeholder={`Slot ${slot} team name`}
          aria-label={`Team name for slot ${slot}`}
          style={{
            flex: 1,
            minWidth: 0,
            fontSize: 14,
            fontWeight: 600,
            background: 'var(--panel2)',
            border: '1px solid var(--acc)',
            color: 'var(--txt)',
            padding: '2px 6px',
          }}
        />
      </span>
    );
  }

  const displayName = typedName ?? sourcedName;
  const isTyped = typedName !== undefined;

  return (
    <span style={{ flex: 1, display: 'flex', alignItems: 'baseline', gap: 5, minWidth: 0 }}>
      <span
        style={{
          fontSize: 15,
          fontWeight: 600,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: isTyped ? 'var(--acc)' : displayName === null ? 'var(--dim2)' : 'var(--txt)',
          fontStyle: displayName === null ? 'italic' : 'normal',
        }}
      >
        {displayName ?? `Slot ${slot} (no team name supplied)`}
      </span>
      {isTyped ? (
        <span
          title="Typed locally -- not from opponents.json"
          style={{ fontSize: 9, letterSpacing: '.06em', color: 'var(--acc)', flex: 'none' }}
        >
          TYPED
        </span>
      ) : null}
      <button
        onClick={startEdit}
        title={isTyped ? 'Edit typed name' : 'Type a team name for this slot'}
        aria-label={`Edit team name for slot ${slot}`}
        style={{
          flex: 'none',
          padding: '0 4px',
          background: 'transparent',
          border: 0,
          color: 'var(--dim2)',
          fontSize: 11,
          cursor: 'pointer',
        }}
      >
        ✎
      </button>
      {isTyped ? (
        <button
          onClick={onClear}
          title={sourcedName !== null ? `Clear typed name, back to "${sourcedName}"` : 'Clear typed name'}
          aria-label={`Clear typed team name for slot ${slot}`}
          style={{
            flex: 'none',
            padding: '0 4px',
            background: 'transparent',
            border: 0,
            color: 'var(--dim2)',
            fontSize: 11,
            cursor: 'pointer',
          }}
        >
          ×
        </button>
      ) : null}
    </span>
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
  // Rendering order is QB, RB, WR, TE, FLEX, DEF -- the spec's slot order
  // (02-draft-opponents.md) with FLEX before DEF, not after it. DEF is kept
  // out of STARTER_ORDER (QB/RB/WR/TE only) so it can be placed after FLEX
  // without a second, differently-ordered list to keep in sync.
  const preFlexRows = STARTER_ORDER.filter((pos) => starters[pos]).map((pos) => ({
    pos,
    ...starters[pos]!,
  }));
  const defGroup = starters['DEF'];
  const allStarterGroups = defGroup ? [...preFlexRows, { pos: 'DEF', ...defGroup }] : preFlexRows;
  const totalStarterSlots =
    allStarterGroups.reduce((sum, s) => sum + s.required, 0) + flex.required;
  const filledStarterSlots =
    allStarterGroups.reduce((sum, s) => sum + s.filled, 0) + flex.filled;

  const needsChips = Object.entries(roster.needs).filter(
    ([pos, n]) => CHIP_POSITIONS.includes(pos) && n > 0,
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {preFlexRows.map((s) => (
        <RosterSlotRow key={s.pos} label={s.pos} color={POSITION_COLOR[s.pos] ?? 'var(--txt)'} group={s} />
      ))}
      <RosterSlotRow label="FLEX" color="var(--dim2)" group={flex} />
      {defGroup ? (
        <RosterSlotRow label="DEF" color={POSITION_COLOR['DEF'] ?? 'var(--txt)'} group={defGroup} />
      ) : null}

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
