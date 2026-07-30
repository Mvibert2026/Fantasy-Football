import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { AssistantDock } from '../components/shell/AssistantDock';

/**
 * Thread 073 dismissible-surface audit, one enumerated surface: the expanded
 * assistant dock. Previously only collapsed via its own "-" button -- no
 * click-outside, no Escape, same gap class as the refresh-data popover.
 * Collapsing (not destroying) on dismiss matches the existing minimize
 * button's own behaviour -- there is no other state to lose.
 *
 * FR-077-followup (ASSISTANT-WINDOW.md item 4): the dock body is now ALWAYS
 * mounted (see AssistantDock.tsx's module doc) so the conversation state it
 * holds survives a collapse -- only its `display` toggles. So "collapsed"
 * assertions below check `.not.toBeVisible()`, not `.not.toBeInTheDocument()`:
 * the body is still in the DOM, just hidden, and a test asserting it is gone
 * entirely would fail against the very behaviour this fix exists to produce.
 */

function renderDock() {
  render(
    <AssistantDock where="Draft room · pick 24">
      <div>assistant body</div>
    </AssistantDock>,
  );
}

describe('AssistantDock dismissal', () => {
  it('opens on click and shows the panel', async () => {
    renderDock();
    await userEvent.click(screen.getByText('Assistant'));
    expect(screen.getByText('assistant body')).toBeInTheDocument();
  });

  it('collapses on Escape', async () => {
    renderDock();
    await userEvent.click(screen.getByText('Assistant'));
    expect(screen.getByText('assistant body')).toBeVisible();

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(screen.getByText('assistant body')).not.toBeVisible();
  });

  it('collapses on a click outside the panel', async () => {
    renderDock();
    await userEvent.click(screen.getByText('Assistant'));
    expect(screen.getByText('assistant body')).toBeVisible();

    fireEvent.mouseDown(document.body);
    expect(screen.getByText('assistant body')).not.toBeVisible();
  });

  it('does not collapse on a click inside the panel body', async () => {
    renderDock();
    await userEvent.click(screen.getByText('Assistant'));
    fireEvent.mouseDown(screen.getByText('assistant body'));
    expect(screen.getByText('assistant body')).toBeInTheDocument();
  });
});
