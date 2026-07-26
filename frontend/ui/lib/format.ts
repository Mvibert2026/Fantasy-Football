/**
 * Formatting helpers. These shape values that came from an export; none of them
 * invents one. Anything that would need a number the exports do not contain belongs
 * nowhere in this file.
 */

const ONE_DP = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const INT = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 });

export function decimal(n: number): string {
  return ONE_DP.format(n);
}

export function integer(n: number): string {
  return INT.format(n);
}

/** Renders a delta with an explicit sign, since the sign carries the meaning. */
export function signed(n: number): string {
  const sign = n > 0 ? '+' : n < 0 ? '−' : '±';
  return `${sign}${INT.format(Math.abs(n))}`;
}

export function interval(low: number, high: number): string {
  return `${ONE_DP.format(low)} – ${ONE_DP.format(high)}`;
}

const PCT = new Intl.NumberFormat(undefined, { style: 'percent', maximumFractionDigits: 0 });

/**
 * `acceptance-checks.json#HON-05` / `nullStates`: "Availability < 0.5% renders
 * '<1%', not '0%'" -- a real, computed, very small probability is a different
 * claim from a genuine zero, and `Intl.NumberFormat`'s default rounding
 * collapses both to the same string. Found as a live defect in the 2026-07
 * frontend spec audit (docs/frontend-audit-2026-07.md): every caller of this
 * function was silently producing '0%' for the sub-half-percent case, which is
 * exactly the substitution Principle #2 forbids.
 */
export function percent(n: number): string {
  if (n > 0 && n < 0.005) return '<1%';
  return PCT.format(n);
}

/**
 * The staleness rule from the data contract: in-season, a SOURCE claim older than
 * about 48 hours renders with its age shown. Nothing can be stale yet -- there is no
 * feed -- but the rule ships with the contract so the lane cannot quietly start
 * presenting week-old news as current.
 */
export const STALE_AFTER_MS = 48 * 60 * 60 * 1000;

export function ageOf(publishedAt: string, now: number = Date.now()): string | null {
  const then = Date.parse(publishedAt);
  if (Number.isNaN(then)) return null;
  const delta = now - then;
  if (delta < STALE_AFTER_MS) return null;

  const hours = Math.floor(delta / (60 * 60 * 1000));
  if (hours < 48) return `${INT.format(hours)}h old`;
  return `${INT.format(Math.floor(hours / 24))}d old`;
}
