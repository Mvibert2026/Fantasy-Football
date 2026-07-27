import { useEffect } from 'react';

/**
 * Shared dismiss behaviour for popups/overlays/toasts/modals: close on a click
 * (mousedown) anywhere outside `ref`'s subtree, AND on Escape from anywhere on
 * the page. Every dismissible surface in this app must support both -- a
 * surface that only wires a "Dismiss" button is a confirmed regression class
 * (thread 073: the refresh-data popover had exactly this gap, and the founder
 * could not clear it because neither escape hatch existed, only the button).
 *
 * Listens on `document`, not the ref itself, because "outside" is defined by
 * what is NOT inside the ref -- the classic clickaway pattern (same approach
 * DraftRoom.tsx's search suggester already uses, thread 051/063; this hook
 * generalises it instead of re-deriving it a third time).
 *
 * Subscribed only while `active`, so a closed surface costs nothing.
 */
export function useDismissOnOutsideOrEscape(
  ref: { current: HTMLElement | null },
  active: boolean,
  onDismiss: () => void,
): void {
  useEffect(() => {
    if (!active) return;
    function onDocMouseDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onDismiss();
      }
    }
    function onDocKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onDismiss();
    }
    document.addEventListener('mousedown', onDocMouseDown);
    document.addEventListener('keydown', onDocKeyDown);
    return () => {
      document.removeEventListener('mousedown', onDocMouseDown);
      document.removeEventListener('keydown', onDocKeyDown);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);
}
