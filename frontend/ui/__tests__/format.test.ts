import { describe, expect, it } from 'vitest';
import { percent } from '../lib/format';

/**
 * `acceptance-checks.json#HON-05` and `nullStates`: "Availability < 0.5% renders
 * '<1%', not '0%'" -- a real, computed, very small probability is a different
 * claim from a genuine zero (Principle #2). Found as a live defect in the 2026-07
 * frontend spec audit (docs/frontend-audit-2026-07.md): `percent()` had no
 * sub-half-percent branch, so every caller silently rendered '0%' for values in
 * (0, 0.005) -- collapsing two of the five null-vocabulary states into one glyph.
 */
describe('percent (HON-05)', () => {
  it('renders a genuine zero as 0%', () => {
    expect(percent(0)).toBe('0%');
  });

  it('renders anything under half a percent as <1%, never 0%', () => {
    expect(percent(0.001)).toBe('<1%');
    expect(percent(0.004)).toBe('<1%');
    expect(percent(0.0049)).toBe('<1%');
  });

  it('renders 0.5% and above with normal rounding, not the <1% form', () => {
    expect(percent(0.005)).toBe('1%');
    expect(percent(0.006)).toBe('1%');
  });

  it('rounds ordinary values as before', () => {
    expect(percent(0.34)).toBe('34%');
    expect(percent(1)).toBe('100%');
  });
});
