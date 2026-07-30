import type { Cell } from '../data/cell';
import { traceTooltip } from '../data/trace-fields';
import { useTraceMode } from '../data/traceMode';

/**
 * Renders a Cell. This is the only component that puts an export value on screen.
 *
 * When the Cell is absent it renders the placeholder with the export's own reason as
 * its tooltip -- so a missing projection reads as "the contract says not to show one,
 * here's why" rather than as a gap. That is the common case on this board, not the
 * exception. That reason is Principle #2's honesty layer, never gated by the "show
 * data sources" switch below -- only the present-cell tooltip's raw field path is.
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
  const { on: showSources } = useTraceMode();
  if (cell.kind === 'absent') {
    return (
      <span className="val-absent" title={cell.reason} aria-label={cell.reason}>
        {ABSENT_MARK}
      </span>
    );
  }
  // The tooltip is user-visible product text, not a debug affordance -- it pairs the
  // field's meaning with the path so the number can actually be checked. See
  // ui/data/trace-fields.ts before changing any of these names. The path half is the
  // "show data sources" switch's business; the meaning half stays either way.
  const title = traceTooltip(cell.path, showSources);
  return (
    <span className={className} title={title || undefined}>
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
