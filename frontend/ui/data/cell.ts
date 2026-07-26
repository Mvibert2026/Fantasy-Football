/**
 * A Cell is the only way a value from an export reaches the screen.
 *
 * Two things fall out of that. First, every rendered value carries the exact field
 * path it came from, so "where did this number come from" is answerable by pointing
 * at the artifact rather than by reading the component. Second, absence is a normal
 * variant of the same type rather than a null someone forgot to handle -- so the
 * sparse case is as easy to render as the dense one, and stays honest about *why*
 * the value is missing.
 *
 * 233 of the board's 378 players are sparse. Empty is the common case here, not an
 * error, and the type reflects that.
 */

export type Cell<T> =
  | {
      readonly kind: 'present';
      readonly value: T;
      readonly path: FieldPath;
      readonly runId: string;
    }
  | {
      /**
       * The export had no value here, or the contract says not to display the one it
       * has. `reason` comes from the export itself (a `*_note` sibling, or the
       * contract's own wording) -- it is never authored in the UI.
       */
      readonly kind: 'absent';
      readonly path: FieldPath;
      readonly runId: string;
      readonly reason: string;
    };

/** `artifact.json:dotted.path` -- the same form the narration layer's Fact.source_path uses. */
export type FieldPath = string;

export function present<T>(value: T, path: FieldPath, runId: string): Cell<T> {
  return { kind: 'present', value, path, runId };
}

export function absent<T>(path: FieldPath, runId: string, reason: string): Cell<T> {
  return { kind: 'absent', path, runId, reason };
}

/**
 * Lifts a raw export field into a Cell. A null becomes `absent` carrying the reason
 * the caller supplies -- callers are expected to pass the export's own note.
 */
export function fromNullable<T>(
  raw: T | null | undefined,
  path: FieldPath,
  runId: string,
  reason: string,
): Cell<T> {
  return raw === null || raw === undefined ? absent(path, runId, reason) : present(raw, path, runId);
}

export function isPresent<T>(cell: Cell<T>): cell is Extract<Cell<T>, { kind: 'present' }> {
  return cell.kind === 'present';
}

/** Maps a present value; an absent Cell passes through with its reason intact. */
export function mapCell<T, U>(cell: Cell<T>, fn: (value: T) => U): Cell<U> {
  return cell.kind === 'present'
    ? present(fn(cell.value), cell.path, cell.runId)
    : absent(cell.path, cell.runId, cell.reason);
}
