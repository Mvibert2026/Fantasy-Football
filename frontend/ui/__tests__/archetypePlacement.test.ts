import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { currentArchetypePlacement, DEFAULT_ARCHETYPE_PLACEMENT } from '../data/archetypePlacement';

/**
 * Design round-1 item 2 (thread 121): the archetype chip's placement is
 * dual-built behind this flag until the founder rules between FR-075's own
 * placement request (identity strip) and design's disclosed-section
 * amendment. These tests pin the resolution order (URL param > localStorage
 * > default) and, separately, that the default matches the founder's
 * standing instruction -- a regression here would silently ship the
 * un-ruled-on arrangement.
 */

function resetLocation() {
  window.history.pushState(null, '', '/');
}

describe('currentArchetypePlacement (thread 121 scaffolding)', () => {
  beforeEach(() => {
    localStorage.removeItem('prep.archetypePlacement');
    resetLocation();
  });
  afterEach(() => {
    localStorage.removeItem('prep.archetypePlacement');
    resetLocation();
  });

  it('defaults to identity-strip -- the founder\'s standing FR-075 instruction -- when untouched', () => {
    expect(currentArchetypePlacement()).toBe('identity-strip');
    expect(DEFAULT_ARCHETYPE_PLACEMENT).toBe('identity-strip');
  });

  it('honours a localStorage override', () => {
    localStorage.setItem('prep.archetypePlacement', 'disclosed');
    expect(currentArchetypePlacement()).toBe('disclosed');
  });

  it('ignores a garbage localStorage value and falls back to the default', () => {
    localStorage.setItem('prep.archetypePlacement', 'somewhere-else');
    expect(currentArchetypePlacement()).toBe('identity-strip');
  });

  it('honours a ?archetypePlacement= URL override', () => {
    window.history.pushState(null, '', '/?archetypePlacement=disclosed');
    expect(currentArchetypePlacement()).toBe('disclosed');
  });

  it('the URL param wins over a conflicting localStorage value', () => {
    localStorage.setItem('prep.archetypePlacement', 'disclosed');
    window.history.pushState(null, '', '/?archetypePlacement=identity-strip');
    expect(currentArchetypePlacement()).toBe('identity-strip');
  });

  it('ignores a garbage URL value and falls back to localStorage, then default', () => {
    window.history.pushState(null, '', '/?archetypePlacement=nonsense');
    expect(currentArchetypePlacement()).toBe('identity-strip');
    localStorage.setItem('prep.archetypePlacement', 'disclosed');
    expect(currentArchetypePlacement()).toBe('disclosed');
  });
});
