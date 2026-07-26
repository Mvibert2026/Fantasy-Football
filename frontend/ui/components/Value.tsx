import type { Cell } from '../data/cell';
import { traceTooltip } from '../data/trace-fields';

/**
 * Renders a Cell. This is the only component that puts an export value on screen.
 *
 * When the Cell is absent it renders the placeholder with the export's own reason as
 * its tooltip -- so a missing projection reads as "the contract says not to show one,
 * here's why" rather than as a gap. That is the common case on this board, not the
 * exception.
 */

const ABSENT_MARK = '—';

export function Value<T>({
  cell,
  render,
  className,
}: {
  cell: Cell<T>;
  render: (value: T) => string;
  className?: string;
}) {
  if (cell.kind === 'absent') {
    return (
      <span className="val-absent" title={cell.reason} aria-label={cell.reason}>
        {ABSENT_MARK}
      </span>
    );
  }
  // The tooltip is user-visible product text, not a debug affordance -- it pairs the
  // field's meaning with the path so the number can actually be checked. See
  // ui/data/trace-fields.ts before changing any of these names.
  return (
    <span className={className} title={traceTooltip(cell.path)}>
      {render(cell.value)}
    </span>
  );
}

/** A Cell rendered into a table cell, right-aligned with the numeric column styling. */
export function NumCell<T>({
  cell,
  render,
  className,
}: {
  cell: Cell<T>;
  render: (value: T) => string;
  className?: string;
}) {
  return (
    <td className="n">
      <Value cell={cell} render={render} className={className} />
    </td>
  );
}
