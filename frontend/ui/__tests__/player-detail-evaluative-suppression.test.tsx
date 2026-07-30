import { render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';
import { describe, expect, it, vi } from 'vitest';
import { PlayerDetail } from '../components/PlayerDetail';
import { buildRows } from '../data/board';
import { buildLeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import type { RawBoardPlayer } from '../data/types';
import { loadDatasetFromDisk, withTraceOn } from './helpers';

/**
 * FR-121 / `docs/design/PROVENANCE-DISCLOSURE.md`'s "class 3" finding: the
 * export's own `evaluative_adjustment_note` used to render verbatim, including
 * a literal instruction to the UI it was not obeying -- "SUPPRESS this row in
 * the UI while evaluative_adjustment_available is false." Founder's own read,
 * relayed via the dispatching task: this is a straight bug, not a provenance-
 * disclosure case. Fixed by obeying the field, unconditionally -- this must
 * hold in BOTH states of the "show data sources" switch, since the switch only
 * ever governs field-path *sourcing* text, never a developer note that should
 * never render at all.
 */

const data = loadDatasetFromDisk();
const league = buildLeagueConfig(data);

function withEvaluativeOverride(overrides: Partial<RawBoardPlayer>): Dataset {
  return {
    ...data,
    board: {
      ...data.board,
      players: data.board.players.map((p, i) => (i === 0 ? { ...p, ...overrides } : p)),
    },
  } as Dataset;
}

function renderFirst(dataset: Dataset, wrapper: (el: ReactElement) => ReactElement = (el) => el) {
  const rows = buildRows(dataset);
  const first = rows[0];
  if (!first) throw new Error('Real board export has zero players -- fixture assumption broken.');
  return render(
    wrapper(
      <PlayerDetail
        row={first}
        rows={rows}
        data={dataset}
        league={league}
        picks={[]}
        watchlist={[]}
        onToggleWatch={() => {}}
        onClose={vi.fn()}
      />,
    ),
  );
}

const SUPPRESS_TEXT = 'SUPPRESS this row';
const REAL_NOTE = withEvaluativeOverride({}).board.players[0]!.evaluative_adjustment_note;

describe('PlayerDetail evaluative-adjustment suppression (FR-121, class 3)', () => {
  it('the real export note actually contains the literal UI instruction -- confirms this test is not vacuous', () => {
    expect(REAL_NOTE).toContain(SUPPRESS_TEXT);
  });

  it('never renders the note (or the instruction inside it) when evaluative_adjustment_available is false -- default view', () => {
    renderFirst(withEvaluativeOverride({ evaluative_adjustment_available: false }));
    expect(document.body.textContent).not.toContain(SUPPRESS_TEXT);
    expect(document.body.textContent).not.toContain('Zero by construction');
  });

  it('never renders it even with "show data sources" on -- this is not a provenance case, obeying the field is unconditional', () => {
    renderFirst(withEvaluativeOverride({ evaluative_adjustment_available: false }), withTraceOn);
    expect(document.body.textContent).not.toContain(SUPPRESS_TEXT);
    expect(document.body.textContent).not.toContain('Zero by construction');
  });

  it('renders the note normally once evaluative_adjustment_available is true -- the suppression is conditional on the real field, not a blanket removal', () => {
    renderFirst(
      withEvaluativeOverride({
        evaluative_adjustment_available: true,
        evaluative_adjustment_note: 'A real evaluative note that should render.',
      }),
    );
    expect(screen.getByText('A real evaluative note that should render.')).toBeTruthy();
  });
});
