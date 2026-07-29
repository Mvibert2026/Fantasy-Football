import { useEffect, useMemo, useState } from 'react';
import type { BoardRow } from '../data/board';
import { playerAvailabilityAtPick } from '../data/availability';
import {
  currentOverallPick,
  loadDraftState,
  nextPickForSlot,
  roundOfPick,
  saveDraftState,
  takenPlayerIds,
  type DraftState,
} from '../data/draft';
import { computeLiveAvailability, dotsFilled, freqText, type LiveAvailabilityResult } from '../data/liveAvailability';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { Value } from '../components/Value';
import { integer, percent } from '../lib/format';

/**
 * Predictions -- thread 028 (docs/handoffs/028-build-predictions-tab.md). Built for
 * the first time this pass; previously an explicit "not built" pane, and before
 * that reported complete against a screen that never existed at all
 * (docs/operating-model.md's evidence-standards table names this exact screen).
 *
 * The reference design (docs/design-reference/reference/03-draft-predictions.png,
 * docs/design-handoff/screens/03-draft-predictions.md) draws this table nested
 * inside Draft mode's own hub, as a third tab alongside Board and Opponents, with
 * pane 1 widening to hold it. This build does not do that: this round's dispatch
 * explicitly reserves DraftRoom.tsx for a sibling session, and DraftRoom.tsx's own
 * module doc already anticipates the alternative taken here -- "Opponents and a
 * standalone Predictions table exist as their own Prep-mode screens" -- so this
 * follows that precedent (and Opponents.tsx's own precedent: also drawn from a
 * "draft" screenshot, also shipped as a Prep-mode sidebar screen) rather than
 * inventing a third pattern. Folding this into the live Draft-mode hub as an actual
 * tab is a follow-up for whoever next owns DraftRoom.tsx, not done here.
 *
 * One consequence of being a Prep-mode screen: there is no pick-entry command bar
 * here, so "the pick to project availability at" is read from whatever draft state
 * is already sitting in localStorage under this league's key (ui/data/draft.ts,
 * `prep.draft.<leagueId>` -- the exact same store Draft mode's DraftRoom writes to)
 * rather than a live typeahead. That means this screen is read-only for picks (as
 * every other Prep screen is, per App.tsx's own module doc) but can still show a
 * genuinely live projection once a session has logged picks in Draft mode, because
 * both screens share one store. The "+ queue" toggle is the one write this screen
 * does perform -- queue is draft-scoped, not pick-scoped, and toggling it here uses
 * the exact same `DraftState.queue` field and `saveDraftState` call DraftRoom.tsx
 * uses, not a second queue.
 *
 * The live number itself is `computeLiveAvailability` (ui/data/liveAvailability.ts),
 * unmodified and already used by DraftRoom and PlayerDetail -- this screen adds no
 * new formula, only a new place to read the existing one from a full sorted list
 * instead of one row at a time.
 *
 * Two hard requirements from the thread, both because this is the screen that most
 * directly shows the product's differentiator and so is the one place an overclaim
 * would matter most:
 *
 *   - LIVE renders the literal text "not yet" when `computeLiveAvailability` reports
 *     signal 'none' -- never a `0%`/`—` that could be misread as "computed and
 *     zero" or "not computed" ambiguously. BASELINE is a separate `Cell<number>` and
 *     renders its own honest absence via `Value` when a player was never simulated.
 *   - The calibration caveat below is quoted, not authored here. The design spec
 *     (03-draft-predictions.md) does not carry any caveat about validation status,
 *     and thread 028 explicitly says to flag that gap rather than invent wording.
 *     The sentence used is copied verbatim (trimmed) from docs/CURRENT-STATE.md's
 *     "Validation status" section, the project's one canonical statement of this
 *     fact, so nothing on this screen is new copy -- flagged back to design/pm in
 *     the thread 028 reply for a permanent, designed treatment.
 *
 * Not built here, out of scope for this pass: the reference's position-scarcity and
 * roster side panels (panes 2/3) -- those are DraftRoom's own panes already, and
 * duplicating them is exactly the "follow-up, not core" work DraftRoom.tsx's doc
 * comment already defers.
 *
 * FR-035 (docs/founder-requests/FR-035-predictions-in-prep-must-be-scoped-to-the-
 * select.md): diagnosed live, in a real running app, switching between the primary
 * league (Westwood, 10 teams/16 rounds/slot 3) and Ethan's Expert League (10 teams/15
 * rounds/slot 1). The re-derivation itself was already correct -- the header line, the
 * "on the clock" text and every row's live-availability number all changed to match
 * the new league's teams/rounds/slot on switch, confirmed via a real Playwright
 * screenshot, not just reading the code. The actual defect was (1) from the dispatch,
 * not (2): nothing on this screen ever named which league it was predicting under, so
 * the founder had no way to *tell* it had re-scoped short of reading player names. The
 * `PredictingUnder` line below is the fix -- league name, team count, round count and
 * draft slot, all sourced (never invented when `data.league.league_name` is absent on
 * an older export), plus the FR-034 override marker when the slot in play is a local
 * override rather than league.json's own value.
 */

const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
};

/** docs/design-handoff/screens/03-draft-predictions.md's Grid section, verbatim. */
const GRID_TEMPLATE = 'minmax(120px,1.5fr) 46px 64px 64px 44px 108px 96px';

/** Quoted verbatim (trimmed) from docs/CURRENT-STATE.md's "Validation status"
 *  section -- see the module doc above for why this is quoted rather than authored
 *  fresh for this screen. */
const CALIBRATION_CAVEAT =
  "The signature claim on this screen is calibrated availability. It is currently not calibrated: " +
  "1 of ~30 required mock drafts is logged, and that one is the real 2025 draft, not a mock. Until " +
  "that number moves, every probability below is an honest estimate, not a validated probability.";

export function Predictions({ data, rows, league }: { data: Dataset; rows: BoardRow[]; league: LeagueConfig }) {
  const leagueId = data.manifest.artifacts.board?.league_id ?? 'default';
  const [draft, setDraft] = useState<DraftState>(() => loadDraftState(leagueId));

  // Re-read from storage whenever the league changes underneath this screen (the
  // top bar's league switcher) or whenever this screen (re)mounts, so a session
  // that logged picks in Draft mode and then navigated here sees them -- matching
  // DraftRoom.tsx's own reload-on-leagueId-change effect.
  useEffect(() => {
    setDraft(loadDraftState(leagueId));
  }, [leagueId]);

  const rowsById = useMemo(() => new Map(rows.map((r) => [r.id, r])), [rows]);
  const teams = league.teams.kind === 'present' ? league.teams.value : 0;
  const rounds = league.rounds.kind === 'present' ? league.rounds.value : 0;
  const userSlot = league.userSlot.kind === 'present' ? league.userSlot.value : 0;

  const taken = useMemo(() => takenPlayerIds(draft.picks), [draft.picks]);
  const available = useMemo(() => {
    return rows
      .filter((r) => !taken.has(r.id))
      .slice()
      .sort((a, b) => {
        const ra = a.overallRank.kind === 'present' ? a.overallRank.value : Number.POSITIVE_INFINITY;
        const rb = b.overallRank.kind === 'present' ? b.overallRank.value : Number.POSITIVE_INFINITY;
        return ra - rb;
      });
  }, [rows, taken]);

  const currentPick = currentOverallPick(draft.picks);
  const draftComplete = teams > 0 && rounds > 0 && currentPick > teams * rounds;
  const nextUserPick =
    teams > 0 && rounds > 0 && userSlot > 0 ? nextPickForSlot(draft.picks, teams, userSlot, rounds) : null;

  function toggleQueue(id: number) {
    const has = draft.queue.includes(id);
    const next: DraftState = { ...draft, queue: has ? draft.queue.filter((q) => q !== id) : [...draft.queue, id] };
    setDraft(next);
    saveDraftState(next);
  }

  if (teams === 0 || rounds === 0 || userSlot === 0) {
    return (
      <div className="view" style={{ flex: 1, minHeight: 0 }}>
        <div className="empty">
          <strong>Predictions needs league.json:teams, rounds and user_draft_slot.</strong> One or more is
          missing for this league.
        </div>
      </div>
    );
  }

  // Computed once against an arbitrary available row purely to read the aggregate
  // signal state (picksLogged/picksRequired/signal never depend on which player is
  // passed in -- only on picksLogged, teams and the target pick, see
  // ui/data/liveAvailability.ts) -- this is the exact same source of truth every
  // row below calls again for its own baseline/live pair, not a second formula.
  const headerAvail: LiveAvailabilityResult | null =
    nextUserPick !== null && available.length > 0
      ? computeLiveAvailability({
          data,
          league,
          row: available[0]!,
          targetPick: nextUserPick,
          picks: draft.picks,
          rowsById,
        })
      : null;

  const header = headerMessage({ draftComplete, currentPick, nextUserPick, teams, headerAvail });

  return (
    <div className="stack" style={{ display: 'flex', flexDirection: 'column', minHeight: 0, flex: 1 }}>
      <section>
        <h2>Predictions</h2>
        <PredictingUnder data={data} league={league} teams={teams} rounds={rounds} userSlot={userSlot} />
        <p className="notice" style={{ borderColor: 'var(--down)', color: 'var(--down)' }}>
          {CALIBRATION_CAVEAT}
        </p>
      </section>

      <div style={{ flex: 'none' }}>
        <div style={{ fontSize: 15, fontWeight: 600 }}>
          {nextUserPick !== null ? `Live availability at pick ${nextUserPick}` : 'Live availability'}
        </div>
        <div style={{ marginTop: 4, fontSize: 12.5, color: header.warn ? 'var(--down)' : 'var(--dim)' }}>
          {header.text}
        </div>
      </div>

      {nextUserPick === null ? (
        <div className="empty" style={{ marginTop: 12 }}>
          Nothing to project -- there is no further pick on record for you in this draft.
        </div>
      ) : (
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', marginTop: 10 }}>
          <div
            style={{
              flex: 'none',
              display: 'grid',
              gridTemplateColumns: GRID_TEMPLATE,
              gap: 10,
              padding: '6px 14px',
              borderBottom: '1px solid var(--line)',
              fontFamily: 'var(--font-num)',
              fontSize: 10,
              letterSpacing: '.08em',
              color: 'var(--dim2)',
            }}
          >
            <span>PLAYER</span>
            <span>POS</span>
            <span style={{ textAlign: 'right' }}>BASELINE</span>
            <span style={{ textAlign: 'right' }}>LIVE</span>
            <span style={{ textAlign: 'right' }}>Δ</span>
            <span>IN 10 DRAFTS</span>
            <span style={{ textAlign: 'right' }}>RANGE</span>
          </div>

          <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
            {available.length === 0 ? (
              <div className="empty" style={{ margin: 12 }}>
                No players remain on the board.
              </div>
            ) : (
              available.map((row) => (
                <PredictionRow
                  key={row.id}
                  row={row}
                  data={data}
                  league={league}
                  targetPick={nextUserPick}
                  picks={draft.picks}
                  rowsById={rowsById}
                  queued={draft.queue.includes(row.id)}
                  onToggleQueue={() => toggleQueue(row.id)}
                />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** docs/design-handoff/screens/03-draft-predictions.md's "Composition" section,
 *  implemented against real state instead of the spec's placeholder counts. The
 *  fourth branch (nextUserPick === currentPick, "you're on the clock") is not in
 *  the spec's three -- it is a real, distinct null state the spec's own three
 *  messages would misdescribe (there being zero picks between now and your turn
 *  is not the same fact as "too few picks logged"), so it gets its own honest
 *  wording rather than being folded into one of the other three. */
function headerMessage({
  draftComplete,
  currentPick,
  nextUserPick,
  teams,
  headerAvail,
}: {
  draftComplete: boolean;
  currentPick: number;
  nextUserPick: number | null;
  teams: number;
  headerAvail: LiveAvailabilityResult | null;
}): { text: string; warn: boolean } {
  if (draftComplete) {
    return { text: 'Draft complete -- no further picks to project availability for.', warn: false };
  }
  if (nextUserPick === null) {
    return {
      text: 'You have no further picks on record in this draft -- nothing to project availability against.',
      warn: false,
    };
  }
  if (nextUserPick === currentPick) {
    return {
      text:
        `You're on the clock at pick ${currentPick}. No picks separate now from your turn, so there is no ` +
        'roster-need or run signal to project -- baseline probabilities only.',
      warn: true,
    };
  }
  if (!headerAvail) {
    return { text: 'Nothing left on the board to project.', warn: false };
  }
  const { picksLogged, picksRequired, signal } = headerAvail;
  if (signal === 'none') {
    return {
      text:
        `Roster-need and run signals need ${picksRequired} picks before they say anything. ${picksLogged} logged ` +
        '-- the live column is an explicit null, not the baseline repeated.',
      warn: true,
    };
  }
  if (signal === 'thin') {
    return {
      text:
        `Only ${picksLogged} picks logged, under one full round. The adjustment is computed but its band is ` +
        'widened and every row is marked thin.',
      warn: true,
    };
  }
  const roundsLogged = roundOfPick(picksLogged, teams);
  return {
    text: `${picksLogged} picks logged across ${roundsLogged} rounds. Roster-need arithmetic and run detection are both in play.`,
    warn: false,
  };
}

/**
 * FR-035's actual fix: states what this screen is predicting under, so a league switch
 * is *visible on this screen* rather than something you have to infer from which
 * players appear. League name falls back to the raw `league_id` when
 * `league.json:league_name` is absent (older export, contract < 1.7.0) -- never a
 * blank or invented name. Team/round counts read the same Cells the rest of the
 * screen's math already uses, not a second source. The slot clause is deliberately not
 * a `<Value>` render when overridden (FR-034): an override does not trace to a backend
 * field, and Principle #1/#2 require that to stay visually distinct rather than folded
 * into the same "sourced" treatment as everything else on this line.
 */
function PredictingUnder({
  data,
  league,
  teams,
  rounds,
  userSlot,
}: {
  data: Dataset;
  league: LeagueConfig;
  teams: number;
  rounds: number;
  userSlot: number;
}) {
  const leagueName = data.league.league_name ?? data.league.league_id ?? 'this league';
  const overridden = league.userSlotOverridden;
  const sourcedSlot = league.userSlotSourced.kind === 'present' ? league.userSlotSourced.value : null;

  return (
    <div
      className="num"
      style={{
        marginTop: 4,
        marginBottom: 8,
        fontSize: 11.5,
        letterSpacing: '.02em',
        color: 'var(--dim)',
      }}
    >
      Predicting for <span style={{ color: 'var(--txt)', fontWeight: 600 }}>{leagueName}</span>
      {' · '}
      {teams > 0 ? `${teams} teams` : 'team count unavailable'}
      {' · '}
      {rounds > 0 ? `${rounds} rounds` : 'round count unavailable'}
      {' · '}
      {userSlot > 0 ? (
        <>
          your slot{' '}
          <span style={{ color: overridden ? 'var(--acc)' : 'var(--txt)', fontWeight: 600 }}>{userSlot}</span>
          {overridden ? (
            <span style={{ color: 'var(--acc)' }} title="Set locally via the SLOT control in the top bar, not from league.json.">
              {' '}
              (overridden{sourcedSlot !== null ? `, sourced ${sourcedSlot}` : ''})
            </span>
          ) : null}
        </>
      ) : (
        'draft slot unavailable'
      )}
    </div>
  );
}

function liveColor(p: number): string {
  return p >= 0.5 ? 'var(--up)' : p >= 0.15 ? 'var(--txt)' : 'var(--down)';
}

function PredictionRow({
  row,
  data,
  league,
  targetPick,
  picks,
  rowsById,
  queued,
  onToggleQueue,
}: {
  row: BoardRow;
  data: Dataset;
  league: LeagueConfig;
  targetPick: number;
  picks: DraftState['picks'];
  rowsById: Map<number, BoardRow>;
  queued: boolean;
  onToggleQueue: () => void;
}) {
  const avail = computeLiveAvailability({ data, league, row, targetPick, picks, rowsById });
  const name = row.name.kind === 'present' ? row.name.value : '';
  const position = row.position.kind === 'present' ? row.position.value : '';

  // Same honesty rule as DraftRoom's own RowDots (HON-02): only plot the dot array
  // when there is a real number behind it -- live if computed, else the baseline --
  // never a zero-filled array standing in for "never simulated".
  const dotsValue = avail.live ?? (avail.baseline.kind === 'present' ? avail.baseline.value : null);

  const deltaPts =
    avail.live !== null && avail.baseline.kind === 'present' ? (avail.live - avail.baseline.value) * 100 : null;

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: GRID_TEMPLATE,
        gap: 10,
        padding: '6px 14px',
        alignItems: 'center',
        borderBottom: '1px solid var(--line)',
      }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <span className="num" style={{ fontSize: 11, color: 'var(--dim2)', width: 22, textAlign: 'right', flex: 'none' }}>
          <Value cell={row.overallRank} render={integer} />
        </span>
        <span
          style={{
            fontWeight: 600,
            fontSize: 13,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            flex: 'none',
            maxWidth: '60%',
          }}
        >
          {name}
        </span>
        <span
          role="button"
          tabIndex={0}
          onClick={onToggleQueue}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onToggleQueue();
            }
          }}
          style={{
            fontFamily: 'var(--font-num)',
            fontSize: 10,
            color: queued ? 'var(--acc)' : 'var(--dim2)',
            cursor: 'pointer',
            flex: 'none',
          }}
        >
          {queued ? 'queued' : '+ queue'}
        </span>
      </span>

      <span style={{ fontSize: 11, letterSpacing: '.045em', fontWeight: 600, color: POSITION_COLOR[position] ?? 'var(--dim2)' }}>
        <Value cell={row.positionalLabel} render={(v) => v} />
      </span>

      <span className="num" style={{ fontSize: 12, textAlign: 'right', color: 'var(--dim2)' }}>
        <Value cell={avail.baseline} render={percent} />
      </span>

      <span
        className="num"
        title={
          avail.live !== null
            ? 'Baseline adjusted by roster-need and positional-run signals at your next pick.'
            : `Live not yet computed -- ${avail.picksLogged} of ${avail.picksRequired} picks logged.`
        }
        style={{ fontSize: 13, fontWeight: 600, textAlign: 'right', color: avail.live !== null ? liveColor(avail.live) : 'var(--dim2)' }}
      >
        {avail.live !== null ? percent(avail.live) : <span style={{ fontStyle: 'italic' }}>not yet</span>}
      </span>

      <span className="num" style={{ fontSize: 11, textAlign: 'right' }}>
        {deltaPts === null ? (
          <span style={{ color: 'var(--dim2)' }}>—</span>
        ) : deltaPts > 2 ? (
          <span style={{ color: 'var(--acc)' }}>▲{integer(deltaPts)}</span>
        ) : deltaPts < -2 ? (
          <span style={{ color: 'var(--down)' }}>▼{integer(Math.abs(deltaPts))}</span>
        ) : (
          <span style={{ color: 'var(--dim2)' }}>·</span>
        )}
      </span>

      {dotsValue !== null ? <PredictionDots value={dotsValue} /> : <span />}

      <RangeCell data={data} name={name} pick={targetPick} />
    </div>
  );
}

/** docs/design-handoff/screens/03-draft-predictions.md's "Why the dots exist":
 *  10 dots, 6px, filled = round(p*10) -- the same frequency-array idiom as
 *  DraftRoom's RowDots and Availability.tsx's SpotlightDots, sized per this
 *  screen's own spec rather than either sibling's. */
function PredictionDots({ value }: { value: number }) {
  const filled = dotsFilled(value);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 2, flex: 'none' }} title={freqText(value)}>
      {Array.from({ length: 10 }, (_, i) => (
        <span
          key={i}
          style={{ width: 6, height: 6, borderRadius: '50%', background: i < filled ? 'var(--acc)' : 'var(--line2)' }}
        />
      ))}
    </div>
  );
}

/** RANGE: "lo–hi%", the real sigma-5/sigma-20 spread -- same idiom as
 *  Availability.tsx's SigmaSpread (duplicated in miniature here rather than
 *  imported, since Availability.tsx is not part of this screen and the two are
 *  small enough not to be worth a shared module for). Explicit "—" when neither
 *  sigma reading exists for this player/pick, never an invented range. */
function RangeCell({ data, name, pick }: { data: Dataset; name: string; pick: number }) {
  const cell = playerAvailabilityAtPick(data, name, pick);
  const vals = [cell.sigma5, cell.sigma10, cell.sigma20].filter((c) => c.kind === 'present') as Array<{
    kind: 'present';
    value: number;
  }>;
  if (vals.length === 0) {
    return (
      <span className="num val-absent" style={{ fontSize: 10.5, textAlign: 'right' }} title="No sigma sweep recorded for this player at this pick.">
        —
      </span>
    );
  }
  const lo = Math.min(...vals.map((v) => v.value));
  const hi = Math.max(...vals.map((v) => v.value));
  return (
    <span
      className="num"
      style={{ fontSize: 10.5, textAlign: 'right', color: 'var(--dim2)' }}
      title="Range across sigma 5, 10 and 20"
    >
      {percent(lo)}–{percent(hi)}
    </span>
  );
}
