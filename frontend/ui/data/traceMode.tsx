import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

/**
 * The global "show data sources" switch (FR-114, `docs/design/PROVENANCE-DISCLOSURE.md`).
 *
 * The founder's own words, twice: first "remove the code and sourcing that's all over,"
 * then, refining it once he saw what it caught: "I like the idea about traceability, I
 * found a lot of things with those notes, I just want to be able to see a version with
 * and without them." So this never deletes anything -- it is a visibility condition on
 * three different things this app renders, sorted by what they actually are:
 *
 *   1. Field paths -- `board.json:players[].vbd`, `availability.json:by_player`, a
 *      structural-breakdown component's own path, the assistant's raw provenance line.
 *      Developer-facing. Goes behind this switch, default OFF, restored verbatim when ON.
 *   2. Caveats and "why is this absent" reasons -- e.g. the ADP-proxy caveat, a null
 *      cell's `reason`, an evaluative-note's plain-English explanation. These are the
 *      app's honesty layer (Principle #2: an explicit null is a real state) and this
 *      switch must NEVER hide them. If a component ever welds a reason and a field path
 *      into one string, split it at the point of rendering -- the reason renders
 *      unconditionally, only the trailing path is gated.
 *   3. Developer notes accidentally rendered as body text (e.g. the literal "SUPPRESS
 *      this row in the UI while evaluative_adjustment_available is false" string that
 *      used to print verbatim) -- not provenance at all, a straight bug. Those are fixed
 *      by obeying the instruction, not by hiding it behind this switch; see
 *      `PlayerDetail.tsx`'s evaluative-adjustment section.
 *
 * Labelled "Show data sources" everywhere a person sees it -- never "provenance",
 * "trace", or "field path" in user-visible copy (the founder does not use those words).
 * Internally this module and its variables may say "trace mode" freely; that is
 * implementation vocabulary, not product copy.
 *
 * Persisted as a bare boolean in localStorage. FR-103 (no assistant chat content in
 * storage) does not apply -- this is a UI preference, not question text.
 */

const STORAGE_KEY = 'prep.showDataSources';

function readStored(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1';
  } catch {
    return false;
  }
}

function writeStored(on: boolean): void {
  try {
    if (on) localStorage.setItem(STORAGE_KEY, '1');
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Persistence is a nicety; a failed write just means the default (off) returns next load.
  }
}

export interface TraceModeState {
  /** Whether field-path sourcing text should render right now. Default false. */
  on: boolean;
  setOn: (on: boolean) => void;
  toggle: () => void;
}

const DEFAULT_STATE: TraceModeState = { on: false, setOn: () => {}, toggle: () => {} };

/**
 * Default value is genuinely inert (setters are no-ops), so any component that reads
 * this context without a `TraceModeProvider` ancestor -- most of this app's many unit
 * tests render a single view in isolation, not the whole shell -- still gets the
 * correct default-off behaviour rather than a crash. Only the Settings checkbox, the
 * `Alt+T` shortcut, and the persistent indicator need a real provider above them.
 */
/** Exported for tests only, so a test can render a subtree with the switch
 *  forced on (`<TraceModeContext.Provider value={{ on: true, ... }}>`) without
 *  needing a real Settings-panel/keyboard-shortcut interaction just to assert
 *  the ON state renders correctly. Application code should use
 *  `TraceModeProvider`/`useTraceMode`, not this directly. */
export const TraceModeContext = createContext<TraceModeState>(DEFAULT_STATE);

/** Ignore the shortcut while the user is typing anywhere -- the assistant's own input,
 *  a search box, a future text field. `e.code` (not `e.key`) because Alt+T produces a
 *  layout-dependent character on some keyboards (e.g. a dagger on US Mac layouts) while
 *  `code` reports the physical key regardless of what character it produced. */
function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || target.isContentEditable;
}

export function TraceModeProvider({ children }: { children: ReactNode }) {
  const [on, setOnState] = useState<boolean>(readStored);

  useEffect(() => {
    writeStored(on);
  }, [on]);

  const setOn = useCallback((next: boolean) => setOnState(next), []);
  const toggle = useCallback(() => setOnState((v) => !v), []);

  // Alt+T (design's `⌥T`), a whole-screen audit gesture rather than a per-value
  // hover -- one keystroke answers "does this screen trace" instead of one gesture
  // per number. Alongside, not instead of, the Settings checkbox below: the founder
  // asked for the control to live in Settings, and this is a faster path to the
  // same single boolean, not a second, competing setting.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (!e.altKey || e.code !== 'KeyT' || isEditableTarget(e.target)) return;
      e.preventDefault();
      setOnState((v) => !v);
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, []);

  const value = useMemo<TraceModeState>(() => ({ on, setOn, toggle }), [on, setOn, toggle]);

  return <TraceModeContext.Provider value={value}>{children}</TraceModeContext.Provider>;
}

export function useTraceMode(): TraceModeState {
  return useContext(TraceModeContext);
}

/** Removes inline `[context.id]`-style citation tokens (e.g. `[page.next_pick_reference]`)
 *  the reasoning lane's own model sometimes echoes mid-sentence from the retrieved-context
 *  block it was shown (`server/proxy.ts`'s `contextBlock` formats each item as
 *  `[id] (confidence...)`) -- a field-path citation in the worst possible position, inside
 *  prose rather than in a labelled provenance line. Trace mode ON leaves the model's text
 *  untouched (verbatim is the rule for class 1); OFF strips the bracketed tokens and
 *  collapses the resulting double-spacing. Never touches brackets that aren't a bare
 *  dotted-identifier token, so ordinary bracketed prose (rare, but not this app's pattern)
 *  is not at risk. */
export function stripInlineCitations(text: string, on: boolean): string {
  if (on) return text;
  return text
    .replace(/\s*\[[a-z][\w]*(?:\.[a-z][\w]*)*\]\s*/gi, ' ')
    .replace(/ {2,}/g, ' ')
    .trim();
}
