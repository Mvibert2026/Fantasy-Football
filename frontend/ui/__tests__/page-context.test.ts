import { describe, expect, it } from 'vitest';
import { buildRows, type BoardRow } from '../data/board';
import type { DraftPageContextInput } from '../assistant/pageContext';
import { buildDraftPageContextItems } from '../assistant/pageContext';
import type { VbdOverride } from '../data/recommendation';
import type { PositionScarcity } from '../data/scarcity';
import { loadDatasetFromDisk } from './helpers';

/**
 * FR-076: "the chatbot should have access to that data to synthesize it
 * intelligently." `buildDraftPageContextItems` is the module that turns
 * whatever DraftRoom.tsx already computed into the bounded context bundle the
 * reasoning lane receives on every question. These tests check the properties
 * that matter: it never fabricates a value not already in its input, it says
 * plainly when there's nothing to report (draft complete), it always states
 * what it left out, and every item stays traceable to a real on-screen panel.
 */

const data = loadDatasetFromDisk();
const rows = buildRows(data);

function withVbd(pos: string): BoardRow {
  const row = rows.find((r) => r.raw.position === pos && r.vbd.kind === 'present');
  if (!row) throw new Error(`fixture expected a ${pos} row with a real VBD value`);
  return row;
}

function baseInput(overrides: Partial<DraftPageContextInput> = {}): DraftPageContextInput {
  return {
    currentPick: 7,
    currentRound: 1,
    userOnClock: true,
    nextUserPick: 7,
    picksUntilYou: 0,
    followingUserPick: 17,
    draftComplete: false,
    unfilledPositions: ['RB', 'TE'],
    rosterChips: [
      { label: 'QB', filled: 0, total: 1 },
      { label: 'RB', filled: 0, total: 2 },
    ],
    activeRecommendation: null,
    recommendationContext: { pick: null, isLookAhead: false },
    giveUp: null,
    vbdOverride: null,
    referencePoint: null,
    scarcity: [],
    data,
    ...overrides,
  };
}

describe('buildDraftPageContextItems', () => {
  it('always includes the pick-clock state, roster needs, and a scope note saying what was excluded', () => {
    const items = buildDraftPageContextItems(baseInput());
    const ids = items.map((i) => i.id);
    expect(ids).toContain('page.draft_state');
    expect(ids).toContain('page.roster_needs');
    expect(ids).toContain('page.scope_note');
    const scope = items.find((i) => i.id === 'page.scope_note')!;
    expect(scope.text).toMatch(/does not include the full available-player board/i);
    // Every item is honestly traceable to a real place, not a board.json path
    // pretending to be a field this session doesn't actually have.
    for (const item of items) {
      expect(item.source_path).toMatch(/^(live draft session \(this browser\)|assistant page-context)/);
      expect(item.confidence).toBe('high');
      expect(item.text.trim()).not.toBe('');
    }
  });

  it('states the draft is complete and includes no recommendation content once it is', () => {
    const items = buildDraftPageContextItems(baseInput({ draftComplete: true, activeRecommendation: null }));
    const state = items.find((i) => i.id === 'page.draft_state')!;
    expect(state.text).toMatch(/draft is complete/i);
    expect(items.some((i) => i.id === 'page.recommendation')).toBe(false);
  });

  it('describes who is on the clock vs. how many picks until the user is on the clock', () => {
    const onClock = buildDraftPageContextItems(baseInput({ userOnClock: true }));
    expect(onClock.find((i) => i.id === 'page.draft_state')!.text).toMatch(/on the clock right now/i);

    const waiting = buildDraftPageContextItems(
      baseInput({ userOnClock: false, nextUserPick: 17, picksUntilYou: 10 }),
    );
    const text = waiting.find((i) => i.id === 'page.draft_state')!.text;
    expect(text).toMatch(/not on the clock/i);
    expect(text).toContain('17');
    expect(text).toContain('10');
  });

  it('states the current, on-the-clock recommendation with its reason and honest points range, never a look-ahead label', () => {
    const rb = withVbd('RB');
    const name = rb.name.kind === 'present' ? rb.name.value : '';
    const items = buildDraftPageContextItems(
      baseInput({
        activeRecommendation: {
          playerName: name,
          position: rb.raw.position,
          reason: 'Best value by VBD — 42 points over replacement in your format.',
          pointsRange: { low: 100, high: 130 },
        },
        recommendationContext: { pick: 7, isLookAhead: false },
      }),
    );
    const rec = items.find((i) => i.id === 'page.recommendation')!;
    expect(rec.text).toContain(name);
    expect(rec.text).toMatch(/for the pick happening right now/i);
    expect(rec.text).not.toMatch(/today's board/i);
    expect(rec.text).toContain('100');
    expect(rec.text).toContain('130');
  });

  it('labels a look-ahead recommendation as evaluated on today\'s board, not a forecast', () => {
    const wr = withVbd('WR');
    const name = wr.name.kind === 'present' ? wr.name.value : '';
    const items = buildDraftPageContextItems(
      baseInput({
        userOnClock: false,
        activeRecommendation: {
          playerName: name,
          position: wr.raw.position,
          reason: 'Best value by VBD.',
          pointsRange: null,
        },
        recommendationContext: { pick: 17, isLookAhead: true },
      }),
    );
    const rec = items.find((i) => i.id === 'page.recommendation')!;
    expect(rec.text).toMatch(/today's board/i);
    expect(rec.text).toMatch(/not a forecast/i);
    expect(rec.text).toContain('17');
  });

  it('carries the exact on-screen give-up trade-off text verbatim, not a re-derived one', () => {
    const items = buildDraftPageContextItems(
      baseInput({ giveUp: { text: 'Player X (WR) is 12 over replacement vs Player Y\'s 20.' } }),
    );
    const item = items.find((i) => i.id === 'page.recommendation_tradeoff')!;
    expect(item.text).toContain("Player X (WR) is 12 over replacement vs Player Y's 20.");
  });

  it('explains a VBD override with the displaced player, the exact gap, and every firing term', () => {
    const top = withVbd('TE');
    const displaced = rows.find((r) => r.raw.position !== top.raw.position && r.vbd.kind === 'present')!;
    const override: VbdOverride = {
      displaced,
      vbdGap: 18,
      firing: [
        { term: { key: 'tier1_te', points: 18, reason: 'this is the last tier-1 tight end left on the board' }, appliesTo: 'top' },
      ],
    };
    const items = buildDraftPageContextItems(baseInput({ vbdOverride: override }));
    const item = items.find((i) => i.id === 'page.recommendation_override')!;
    const displacedName = displaced.name.kind === 'present' ? displaced.name.value : '';
    expect(item.text).toContain(displacedName);
    expect(item.text).toContain('18');
    expect(item.text).toMatch(/last tier-1 tight end/);
    expect(item.text).toMatch(/unbacktested stopgap constant, not a finding/);
  });

  it('reports the next-pick reference point exactly as CONSIDERING / LIKELY THERE, including "no player clears 50%"', () => {
    const considering = withVbd('QB');
    const withCandidate = buildDraftPageContextItems(
      baseInput({
        referencePoint: {
          consideringName: considering.name.kind === 'present' ? considering.name.value : '',
          consideringPosition: considering.raw.position,
          pick: 17,
          likelyThere: { name: 'Some Player', position: 'RB' },
        },
      }),
    );
    const withCandidateText = withCandidate.find((i) => i.id === 'page.next_pick_reference')!.text;
    expect(withCandidateText).toContain('Some Player');
    expect(withCandidateText).toMatch(/display only/i);

    const withoutCandidate = buildDraftPageContextItems(
      baseInput({
        referencePoint: {
          consideringName: considering.name.kind === 'present' ? considering.name.value : '',
          consideringPosition: considering.raw.position,
          pick: 17,
          likelyThere: null,
        },
      }),
    );
    const withoutCandidateText = withoutCandidate.find((i) => i.id === 'page.next_pick_reference')!.text;
    expect(withoutCandidateText).toMatch(/no available player has even odds/i);
  });

  it('summarises position scarcity from PositionScarcity values, honestly marking a position with no board data', () => {
    const scarcity: PositionScarcity[] = [
      {
        pos: 'RB',
        total: 40,
        remaining: 30,
        gone: 10,
        dataAvailable: true,
        expected: 8,
        pace: 2,
        paceSuppressedReason: null,
        tier1Remaining: 1,
        tier2Remaining: 3,
        under50ByNext: 1,
        startablePool: 20,
      },
      {
        pos: 'DEF',
        total: 0,
        remaining: 0,
        gone: 0,
        dataAvailable: false,
        expected: null,
        pace: null,
        paceSuppressedReason: null,
        tier1Remaining: null,
        tier2Remaining: null,
        under50ByNext: null,
        startablePool: 0,
      },
    ];
    const items = buildDraftPageContextItems(baseInput({ scarcity }));
    const item = items.find((i) => i.id === 'page.scarcity')!;
    expect(item.text).toMatch(/RB \(30 of 40 left/);
    expect(item.text).toMatch(/DEF: no board data for this position/);
  });

  it('never includes a recommendation item when there is nothing to recommend', () => {
    const items = buildDraftPageContextItems(baseInput({ activeRecommendation: null }));
    expect(items.some((i) => i.id === 'page.recommendation')).toBe(false);
    expect(items.some((i) => i.id === 'page.recommendation_tradeoff')).toBe(false);
    expect(items.some((i) => i.id === 'page.recommendation_override')).toBe(false);
  });
});
