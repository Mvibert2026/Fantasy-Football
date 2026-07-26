import type { BoardRow } from '../data/board';
import type { LeagueConfig } from '../data/league';
import { integer } from '../lib/format';

/**
 * The round grid: the draft laid out as rounds by slot, with your picks marked.
 *
 * Every cell is derived from league.json -- teams, rounds and the user's pick sequence.
 * Nothing about who will actually be taken is shown, because nothing in scope models
 * that. The grid answers "when do I pick again", which is arithmetic, not a forecast.
 */

export function RoundGrid({ league, rows }: { league: LeagueConfig; rows: BoardRow[] }) {
  if (league.teams.kind !== 'present' || league.rounds.kind !== 'present') {
    return (
      <section>
        <h3>Round grid</h3>
        <div className="empty">
          <strong>No draft structure in league.json.</strong> The grid needs team and round
          counts; neither is present in the export.
        </div>
      </section>
    );
  }

  const teams = league.teams.value;
  const rounds = league.rounds.value;
  const mine = new Set(league.pickSequence.kind === 'present' ? league.pickSequence.value : []);
  const byRank = new Map(
    rows.map((r) => [r.overallRank.kind === 'present' ? r.overallRank.value : -1, r]),
  );

  const cells = [];
  for (let round = 1; round <= rounds; round++) {
    for (let slot = 1; slot <= teams; slot++) {
      // Snake order: even rounds run right to left.
      const positionInRound = round % 2 === 1 ? slot : teams - slot + 1;
      const pick = (round - 1) * teams + positionInRound;
      const isMine = mine.has(pick);
      // The board player at that rank, shown only as a reference point for where the
      // board sits at this pick. It is not a prediction that this player will be there.
      const ref = byRank.get(pick);
      cells.push(
        <div key={`${round}-${slot}`} className={isMine ? 'round-cell mine' : 'round-cell'}>
          <div className="pick-no">{integer(pick)}</div>
          {isMine ? (
            <div>
              <strong>Your pick</strong>
              {ref?.positionalLabel.kind === 'present' ? (
                <div style={{ color: 'var(--fg-muted)' }}>board {ref.positionalLabel.value}</div>
              ) : null}
            </div>
          ) : null}
        </div>,
      );
    }
  }

  return (
    <section>
      <h3>Round grid</h3>
      <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--fg-muted)' }}>
        Snake order from league.json. Your slot is{' '}
        <span className="num">
          {league.userSlot.kind === 'present' ? integer(league.userSlot.value) : '—'}
        </span>
        . The board label on your picks is where this board stands at that overall rank — not a
        claim that the player will still be there.
      </p>
      <div
        className="round-grid"
        style={{ gridTemplateColumns: `repeat(${teams}, minmax(6ch, 1fr))` }}
      >
        {cells}
      </div>
    </section>
  );
}
