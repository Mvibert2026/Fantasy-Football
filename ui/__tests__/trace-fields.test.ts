import { describe, expect, it } from 'vitest';
import {
  BOARD_TRACE_FIELDS,
  TRACE_CHANGELOG,
  TRACE_CONTRACT,
  boardFieldOf,
} from '../data/trace-fields';
import { loadDatasetFromDisk } from './helpers';

/**
 * Guards the trace surface.
 *
 * Field paths are rendered as user-visible text -- in value tooltips, in the
 * assistant's provenance lines, in the methodology view. Renaming one changes what the
 * user reads and invalidates anything they wrote down, so it is a product change
 * requiring a contract bump and a heads-up to Design, not a refactor.
 *
 * These tests make that unmissable: a rename in the export surfaces as a failing build
 * carrying the process, rather than as a tooltip that quietly says something different
 * than it did last week.
 */

const data = loadDatasetFromDisk();

describe('trace-field registry', () => {
  it('is pinned to the contract version the exports actually carry', () => {
    expect(
      data.board.contract_version,
      `TRACE_CONTRACT is ${TRACE_CONTRACT} but board.json is ${data.board.contract_version}. ` +
        `If the export moved, bump TRACE_CONTRACT, add a TRACE_CHANGELOG entry, and tell Design — ` +
        `a change to displayed values or names is a product change, not a code diff.`,
    ).toBe(TRACE_CONTRACT);
  });

  it('records every version it has been pinned to', () => {
    expect(TRACE_CHANGELOG[0]?.version).toBe(TRACE_CONTRACT);
  });

  it('knows every field the board export carries', () => {
    const exported = Object.keys(data.board.players[0] ?? {});
    const registered = new Set(BOARD_TRACE_FIELDS.map((f) => f.path));
    const unregistered = exported.filter((k) => !registered.has(k));

    expect(
      unregistered,
      `board.json carries field(s) the trace registry does not know: ${unregistered.join(', ')}. ` +
        `If these are displayed, register them with a user-facing label. If the export renamed a ` +
        `field, move the old name into renamedFrom, bump TRACE_CONTRACT, and send Design a heads-up.`,
    ).toEqual([]);
  });

  it('registers no field the board export has dropped', () => {
    const exported = new Set(Object.keys(data.board.players[0] ?? {}));
    // Nested paths are registered flat; check only the top-level segment.
    const missing = BOARD_TRACE_FIELDS.map((f) => f.path.split('.')[0]!).filter(
      (top) => !exported.has(top),
    );

    expect(
      [...new Set(missing)],
      `The registry names field(s) board.json no longer exports: ${missing.join(', ')}. ` +
        `A dropped field means a tooltip is pointing at nothing — treat as a product change.`,
    ).toEqual([]);
  });

  it('gives every registered field a user-facing label', () => {
    for (const field of BOARD_TRACE_FIELDS) {
      expect(field.label.trim(), `${field.path} has no label`).not.toBe('');
      expect(field.since.trim(), `${field.path} has no since version`).not.toBe('');
    }
  });

  it('resolves an indexed display path back to its field', () => {
    const found = boardFieldOf('board.json:players[42].vbd');
    expect(found?.path).toBe('vbd');
    expect(found?.label).toContain('replacement');
  });
});
