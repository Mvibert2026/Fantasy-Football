import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Draft-screen layout modes (item 7 of the 2026-07-31 design round,
 * `docs/design/PANE-LAYOUT-MODES.md`) and the Grid Expand sheet (item 3,
 * `docs/design/PERIODIC-TABLE-GRID.md`). Built together on purpose -- design
 * specified the grid's Expand and the three layout presets as **the same
 * gesture** (one keystroke, no continuous drag, no "notice it's too narrow and
 * fix it by hand"), so this module owns both rather than inventing the
 * mechanism twice.
 *
 * Design's own words on why there is no drag handle: "a drag handle only works
 * once the user notices a pane is too narrow and fixes it by hand ... that is
 * not a layout, it is homework, and the price of forgetting is drafting the
 * wrong RB10." Three presets, one keystroke each, plus Expand for the one
 * view that cannot be squeezed into any preset at all.
 */

export type LayoutMode = 'board' | 'balanced' | 'decide';

export interface LayoutPreset {
  /** Percent width for the rankings/board column. */
  boardPct: number;
  /** Percent width for the centre pane (Recommend/Scarcity/Queue/Insights/Grid). */
  centerPct: number;
  label: string;
  /** Physical key (`e.code`) for the Alt-combo shortcut. */
  code: string;
  shortcut: string;
}

/**
 * `balanced` is deliberately identical to the pre-existing hardcoded call
 * `paneColumns()` (boardPct 35, centerPct 40, DraftRoom.tsx) -- "today's
 * layout," per the spec table, unchanged as the default.
 */
export const LAYOUT_PRESETS: Record<LayoutMode, LayoutPreset> = {
  board: { boardPct: 52, centerPct: 26, label: 'Board', code: 'Digit1', shortcut: '⌥1' },
  balanced: { boardPct: 35, centerPct: 40, label: 'Balanced', code: 'Digit2', shortcut: '⌥2' },
  decide: { boardPct: 22, centerPct: 56, label: 'Decide', code: 'Digit3', shortcut: '⌥3' },
};

export const LAYOUT_MODE_ORDER: LayoutMode[] = ['board', 'balanced', 'decide'];

const STORAGE_KEY = 'prep.draftLayoutMode';
const GRID_SHORTCUT_CODE = 'KeyG';

function readStoredMode(): LayoutMode {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === 'board' || v === 'balanced' || v === 'decide') return v;
  } catch {
    // Persistence is a nicety; fall through to the default below.
  }
  return 'balanced';
}

function writeStoredMode(mode: LayoutMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    // Best-effort only.
  }
}

/** Same guard `traceMode.tsx`'s `Alt+T` and DraftRoom's own global `/` shortcut
 *  already use: ignore the shortcut while the user is typing anywhere on this
 *  screen (the player-name filter, the assistant input). Duplicated rather
 *  than imported -- three lines, not worth a cross-module dependency for. */
function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || target.isContentEditable;
}

export interface DraftLayoutState {
  layoutMode: LayoutMode;
  setLayoutMode: (mode: LayoutMode) => void;
  gridExpanded: boolean;
  setGridExpanded: (v: boolean) => void;
  toggleGridExpanded: () => void;
}

/**
 * `escBlocked`: true while something that should win Escape over the grid
 * sheet is open (the player detail card, today -- see DraftRoom's Esc
 * precedence comment). When blocked, this hook's own Escape handling is a
 * no-op for that keypress so exactly one thing closes per press, never two.
 */
export function useDraftLayout(escBlocked: boolean): DraftLayoutState {
  const [layoutMode, setLayoutModeState] = useState<LayoutMode>(readStoredMode);
  const [gridExpanded, setGridExpandedState] = useState(false);

  const escBlockedRef = useRef(escBlocked);
  useEffect(() => {
    escBlockedRef.current = escBlocked;
  }, [escBlocked]);

  const gridExpandedRef = useRef(gridExpanded);
  useEffect(() => {
    gridExpandedRef.current = gridExpanded;
  }, [gridExpanded]);

  const setLayoutMode = useCallback((mode: LayoutMode) => {
    setLayoutModeState(mode);
    writeStoredMode(mode);
  }, []);

  const setGridExpanded = useCallback((v: boolean) => setGridExpandedState(v), []);
  const toggleGridExpanded = useCallback(() => setGridExpandedState((v) => !v), []);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (isEditableTarget(e.target)) return;

      if (e.altKey && (e.code === 'Digit1' || e.code === 'Digit2' || e.code === 'Digit3')) {
        e.preventDefault();
        const mode = LAYOUT_MODE_ORDER.find((m) => LAYOUT_PRESETS[m].code === e.code);
        if (mode) setLayoutMode(mode);
        return;
      }

      if (e.altKey && e.code === GRID_SHORTCUT_CODE) {
        e.preventDefault();
        setGridExpandedState((v) => !v);
        return;
      }

      // Esc precedence (documented in DraftRoom.tsx alongside the player-card
      // listener): editable field > player detail card > the grid sheet.
      // isEditableTarget already returned above for the first case. escBlocked
      // covers the second -- PlayerDetail.tsx owns its own unconditional
      // Escape listener and this hook must not also act on the same press.
      if (e.key === 'Escape' && gridExpandedRef.current && !escBlockedRef.current) {
        setGridExpandedState(false);
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [setLayoutMode]);

  return { layoutMode, setLayoutMode, gridExpanded, setGridExpanded, toggleGridExpanded };
}

/**
 * §3.2's pane-width formula (moved here from DraftRoom.tsx so the layout-mode
 * presets and the column math they drive live in one file), using the spec's
 * own defaults. Returns a grid-template-columns value with each pane as a
 * normalised percentage.
 */
export function paneColumns(boardPct = 35, centerPct = 40): string {
  const board = Math.min(60, Math.max(20, boardPct));
  const center = Math.min(65, Math.max(20, centerPct));
  const right = Math.max(14, 100 - board - center);
  const total = board + center + right;
  return `minmax(0,${((board / total) * 100).toFixed(2)}%) minmax(0,${((center / total) * 100).toFixed(2)}%) minmax(0,${((right / total) * 100).toFixed(2)}%)`;
}
