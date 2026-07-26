/**
 * Wilson score interval, FRONTEND-SPEC.md §5.4. Takes counts (k successes of n),
 * never a bare percentage -- percentages lose the sample size an interval needs.
 */

const Z = 1.96;
export const THIN_BUCKET_N = 50;

export interface WilsonInterval {
  p: number;
  lo: number;
  hi: number;
  n: number;
  thin: boolean;
}

export function wilsonInterval(k: number, n: number): WilsonInterval {
  if (n === 0) return { p: 0, lo: 0, hi: 0, n: 0, thin: true };
  const p = k / n;
  const d = 1 + (Z * Z) / n;
  const centre = (p + (Z * Z) / (2 * n)) / d;
  const half = (Z * Math.sqrt((p * (1 - p)) / n + (Z * Z) / (4 * n * n))) / d;
  return {
    p,
    lo: Math.max(0, centre - half),
    hi: Math.min(1, centre + half),
    n,
    thin: n < THIN_BUCKET_N,
  };
}

/** A stated probability is flagged when it falls outside its own bucket's Wilson interval. */
export function isMiscalibrated(statedMid: number, interval: WilsonInterval): boolean {
  return statedMid < interval.lo || statedMid > interval.hi;
}
