import { useMemo } from 'react';
import type { BoardRow } from '../data/board';
import { currentOverallPick, nextPickForSlot, roundPickLabel, teamSlotAtPick, type DraftState } from '../data/draft';
import type { Dataset } from '../data/load';
import type { LeagueConfig } from '../data/league';
import { buildRosterSlots, type RosterSlot } from '../data/rosterSlots';

/**
 * FR-032 ("For opponents we will need to fix that.. make it functional for the
 * user"): the Prep-mode `Opponents.tsx` screen is real and correct, but it is
 * backed entirely by backend `rosters.json` -- real, non-mock completed-draft
 * data. During a *live* draft that file reflects nothing (no real 2026 draft
 * has been logged there yet), so mounting that screen inside Draft mode would
 * show a permanently-empty grid while picks are actively being entered a few
 * feet away in the same pane.
 *
 * This component is the fix: every team's roster and needs are computed from
 * `DraftState.picks` -- the exact same local pick log `DraftRoom.tsx`'s MY
 * ROSTER panel already reads -- run once per team slot instead of only the
 * user's. The roster-need arithmetic is not reimplemented here: it is the same
 * `buildRosterSlots` function MY ROSTER calls, imported from
 * `ui/data/rosterSlots.ts` (extracted from `DraftRoom.tsx`, which is where it
 * was originally written and where it still runs for the user's own slot).
 *
 * Mechanical arithmetic only, per the standing rule this app already applies
 * to the Prep-mode Opponents screen and to DraftRoom's own scarcity/next-pick
 * displays: what a team has drafted, what slots remain unfilled, and when they
 * pick next are all derivable from picks + league config with no judgment
 * call. Nothing here infers a team's strategy, tendencies, or likely next
 * pick -- there is no `positional_tendencies`/`first_pick_by_position` field on
 * this screen at all, unlike the Prep-mode card, because that context comes
 * from `opponents.json`'s behavioural profile (a different, sparser artifact)
 * and mixing it into a screen whose whole point is "picks entered this
 * session" would blur exactly the line FR-032 asked to keep clear.
 *
 * `opponents.json` IS read here, but only for `team_name` -- a static identity
 * label (the same two named primary-league slots the Prep-mode screen shows),
 * never for roster/needs numbers. `rosters.json` is not imported by this file
 * at all, so the two data sources -- real completed-draft data vs. this
 * session's in-progress picks -- can never silently blend into one number the
 * user can't attribute.
 */

const POSITION_COLOR: Record<string, string> = {
  QB: 'var(--qb)',
  RB: 'var(--rb)',
  WR: 'var(--wr)',
  TE: 'var(--te)',
  DEF: 'var(--def)',
};

/** Starter positions rendered as their own STILL NEEDS chip, in display order.
 *  Matches Opponents.tsx's CHIP_POSITIONS exactly (FLEX is not its own chip --
 *  the footer's starters/bench count already reflects it) so the two Opponents
 *  surfaces read as one visual language, not two competing ones. */
const CHIP_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'DEF'];
const STARTER_DISPLAY_ORDER = ['QB', 'RB', 'WR', 'TE', 'DEF'];

interface PositionGroup {
  position: string;
  required: number;
  filled: number;
  players: string[];
}

function groupStarters(rosterSlots: RosterSlot[]): PositionGroup[] {
  const byPosition = new Map<string, PositionGroup>();
  for (const s of rosterSlots) {
    if (s.kind !== 'starter' || !s.position) continue;
    const g = byPosition.get(s.position) ?? { position: s.position, required: 0, filled: 0, players: [] };
    g.required += 1;
    if (s.row) {
      g.filled += 1;
      if (s.row.name.kind === 'present') g.players.push(s.row.name.value);
    }
    byPosition.set(s.position, g);
  }
  return STARTER_DISPLAY_ORDER.filter((p) => byPosition.has(p)).map((p) => byPosition.get(p)!);
}

function Row({ label, color, required, filled, players }: { label: string; color: string; required: number; filled: number; players: string[] }) {
  const empty = filled === 0;
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
        {empty ? 'empty' : players.join(', ')}
      </span>
      <span className="num" style={{ fontSize: 10.5, color: 'var(--dim2)' }}>
        {filled}/{required}
      </span>
    </div>
  );
}

function TeamCard({
  slot,
  teamName,
  isUser,
  isOnClock,
  next,
  teams,
  rosterSlots,
}: {
  slot: number;
  teamName: string | null;
  isUser: boolean;
  isOnClock: boolean;
  next: number | null;
  /** FR-087: teams count, only for formatting `next` as a round.pick label
   *  alongside the raw overall pick number -- not used for any arithmetic
   *  here (that's `nextPickForSlot`, already done by the caller). */
  teams: number;
  rosterSlots: RosterSlot[];
}) {
  const starterGroups = groupStarters(rosterSlots);
  const flexSlots = rosterSlots.filter((s) => s.kind === 'flex');
  const benchSlots = rosterSlots.filter((s) => s.kind === 'bench');
  const flexFilled = flexSlots.filter((s) => s.row).length;
  const flexPlayers = flexSlots.filter((s) => s.row?.name.kind === 'present').map((s) => s.row!.name.kind === 'present' ? s.row!.name.value : '');
  const benchFilled = benchSlots.filter((s) => s.row).length;

  const totalStarterSlots = starterGroups.reduce((sum, g) => sum + g.required, 0) + flexSlots.length;
  const filledStarterSlots = starterGroups.reduce((sum, g) => sum + g.filled, 0) + flexFilled;

  const needsChips = starterGroups
    .filter((g) => CHIP_POSITIONS.includes(g.position) && g.required - g.filled > 0)
    .map((g) => [g.position, g.required - g.filled] as const);

  return (
    <div
      data-testid={`live-opponent-slot-${slot}`}
      style={{
        border: `1px solid ${isOnClock ? 'var(--acc)' : 'var(--line)'}`,
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
            color: teamName === null ? 'var(--dim2)' : 'var(--txt)',
            fontStyle: teamName === null ? 'italic' : 'normal',
          }}
        >
          {teamName ?? `Slot ${slot} (no team name supplied)`}
          {isUser ? <span style={{ color: 'var(--acc)', fontStyle: 'normal' }}> (you)</span> : null}
        </span>
        <span className="num" style={{ fontSize: 11.5, letterSpacing: '.04em', color: 'var(--dim2)', whiteSpace: 'nowrap' }}>
          next{' '}
          <span style={{ color: 'var(--txt)', fontWeight: 600 }}>
            {next === null ? '—' : `#${next} (${roundPickLabel(next, teams)})`}
          </span>
        </span>
      </div>
      {isOnClock ? (
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
          ON THE CLOCK
        </span>
      ) : null}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {starterGroups.map((g) => (
          <Row key={g.position} label={g.position} color={POSITION_COLOR[g.position] ?? 'var(--txt)'} required={g.required} filled={g.filled} players={g.players} />
        ))}
        {flexSlots.length > 0 ? (
          <Row label="FLEX" color="var(--dim2)" required={flexSlots.length} filled={flexFilled} players={flexPlayers} />
        ) : null}

        <div style={{ marginTop: 2, fontSize: 11, color: 'var(--dim2)' }}>
          <span className="num">
            {filledStarterSlots} / {totalStarterSlots}
          </span>{' '}
          starters ·{' '}
          <span className="num">
            {benchFilled} / {benchSlots.length}
          </span>{' '}
          on bench
        </div>

        {needsChips.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 2 }}>
            <span style={{ fontSize: 9.5, letterSpacing: '.06em', color: 'var(--dim2)', alignSelf: 'center' }}>STILL NEEDS</span>
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
    </div>
  );
}

export function LiveOpponents({
  data,
  league,
  draft,
  rowsById,
}: {
  data: Dataset;
  league: LeagueConfig;
  draft: DraftState;
  rowsById: Map<number, BoardRow>;
}) {
  const teams = league.teams.kind === 'present' ? league.teams.value : 0;
  const rounds = league.rounds.kind === 'present' ? league.rounds.value : 0;
  const userSlot = league.userSlot.kind === 'present' ? league.userSlot.value : 0;

  const teamNameBySlot = useMemo(
    () => new Map(data.opponents.opponents.map((o) => [o.draft_slot_2026, o.team_name])),
    [data.opponents],
  );

  // Principle #2: before any pick is entered there is nothing to derive --
  // rendering a full grid of ten "everyone needs everything" cards would look
  // like a finding (every team is short every position) rather than what it
  // actually is (no draft data exists yet). One honest sentence, no cards.
  if (draft.picks.length === 0) {
    return (
      <div style={{ padding: 20 }}>
        <p className="notice">
          No picks yet. Mark picks on the Board tab and each team&apos;s roster will fill in here as
          the draft happens. This view is built from picks entered in this session (this browser's
          local draft log), separate from and never merged with backend <code>rosters.json</code> --
          the Prep-mode Opponents screen's data source, which reflects only real, completed drafts on
          file.
        </p>
      </div>
    );
  }

  const currentPick = currentOverallPick(draft.picks);
  const onClockSlot = teams > 0 ? teamSlotAtPick(currentPick, teams) : 0;
  const teamSlots = Array.from({ length: teams }, (_, i) => i + 1);

  return (
    <div className="stack" style={{ padding: 20 }}>
      <section>
        <h2>Opponents — live</h2>
        <p className="notice">
          {draft.picks.length} pick{draft.picks.length === 1 ? '' : 's'} entered this session. Rosters
          and needs below are computed from this session's local pick log, not backend{' '}
          <code>rosters.json</code>.
        </p>
      </section>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(232px, 1fr))', gap: 12 }}>
        {teamSlots.map((slot) => {
          const teamPicks = draft.picks.filter((p) => p.teamSlot === slot);
          const rosterSlots = buildRosterSlots(teamPicks, league, data, rowsById);
          const next = nextPickForSlot(draft.picks, teams, slot, rounds);
          return (
            <TeamCard
              key={slot}
              slot={slot}
              teamName={teamNameBySlot.get(slot) ?? null}
              isUser={slot === userSlot}
              isOnClock={slot === onClockSlot}
              next={next}
              teams={teams}
              rosterSlots={rosterSlots}
            />
          );
        })}
      </div>
    </div>
  );
}
