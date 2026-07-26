import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * Fails if a component renders a literal number that did not come from an export.
 *
 * The rule this enforces: every number on screen traces to a named field in the data
 * contract. A hardcoded threshold, a placeholder projection, a "12 teams" typed into
 * JSX -- each is a number the user cannot check and that silently goes stale when the
 * export moves. This board has already had its replacement levels change once
 * (RB28/WR41/TE11 -> RB30/WR40/TE10); anything hardcoded then would be wrong now.
 *
 * What it catches: numeric literals in JSX text content, and numeric literals inside
 * JSX expression containers such as `{12}`.
 *
 * What it does not catch, stated plainly: a number computed in a .ts module and passed
 * in, or a number assembled from string concatenation. This is a lint, not a proof.
 * It catches the realistic mistake -- typing a number into markup -- and it is
 * deliberately scoped to the files that produce markup.
 */

const ROOTS = ['ui/views', 'ui/components'];

/**
 * Numbers that are markup mechanics rather than claims about football. Each needs a
 * reason; the list is meant to stay short.
 */
const ALLOWED: Array<{ pattern: RegExp; why: string }> = [
  { pattern: /^[\s·—–-]+$/, why: 'punctuation and separators, no digits of meaning' },
];

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (entry.endsWith('.tsx')) out.push(full);
  }
  return out;
}

/** Strips comments and CSS-ish style objects, which legitimately contain numbers. */
function stripNonMarkup(source: string): string {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/(^|[^:])\/\/.*$/gm, '$1')
    // style={{ ... }} and className strings are presentation, not claims.
    .replace(/style=\{\{[^}]*\}\}/g, 'style={{}}')
    .replace(/className="[^"]*"/g, 'className=""');
}

/**
 * Blanks the contents of every JSX expression container so the text scan does not read
 * JavaScript as markup. Without this, a comparison like `{list.length > 0 ? (` looks
 * like the text run "0 ? (" sitting after a `>`.
 *
 * Expression containers are checked separately, by the `{12}` scan.
 */
function blankExpressions(source: string): string {
  const out = source.split('');
  let depth = 0;
  for (let i = 0; i < out.length; i++) {
    const ch = out[i];
    if (ch === '{') {
      depth++;
      continue;
    }
    if (ch === '}') {
      depth = Math.max(0, depth - 1);
      continue;
    }
    // Keep newlines so reported line numbers stay accurate.
    if (depth > 0 && ch !== '\n') out[i] = ' ';
  }
  return out.join('');
}

interface Finding {
  file: string;
  line: number;
  text: string;
  kind: 'jsx-text' | 'jsx-expression';
}

function findLiteralNumbers(file: string): Finding[] {
  const source = stripNonMarkup(readFileSync(file, 'utf8'));
  const findings: Finding[] = [];
  const lineOf = (index: number) => source.slice(0, index).split('\n').length;

  // JSX text content: the run of characters between a > and the next <, with all
  // expression containers blanked so JavaScript is not mistaken for markup.
  const markup = blankExpressions(source);
  const textRun = />([^<>{}]*?)</g;
  for (let m = textRun.exec(markup); m; m = textRun.exec(markup)) {
    const text = m[1] ?? '';
    if (!/\d/.test(text)) continue;
    if (ALLOWED.some((a) => a.pattern.test(text))) continue;
    findings.push({ file, line: lineOf(m.index), text: text.trim(), kind: 'jsx-text' });
  }

  // Numeric literal in an expression container: {12}, {3.5}, {-1}
  const expr = /\{\s*-?\d+(?:\.\d+)?\s*\}/g;
  for (let m = expr.exec(source); m; m = expr.exec(source)) {
    findings.push({ file, line: lineOf(m.index), text: m[0], kind: 'jsx-expression' });
  }

  return findings;
}

describe('no invented numbers in components', () => {
  const files = ROOTS.flatMap(walk);

  it('finds component files to scan', () => {
    expect(files.length).toBeGreaterThan(0);
  });

  it.each(files)('%s renders no literal number', (file) => {
    const findings = findLiteralNumbers(file);
    const report = findings
      .map((f) => `  ${f.file}:${f.line} [${f.kind}] ${JSON.stringify(f.text)}`)
      .join('\n');

    expect(
      findings,
      findings.length
        ? `Literal number(s) rendered without an export behind them:\n${report}\n\n` +
            `Every number on screen must come from a Cell, so it carries a field path and a run id. ` +
            `If this number really is presentation (a grid span, an index), move it out of markup.`
        : '',
    ).toEqual([]);
  });

  it('the scanner actually detects a planted literal', () => {
    // Positive control. Without this, a broken regex would make the suite pass silently.
    const planted = `export const X = () => <td className="n">28</td>;`;
    const findings: Finding[] = [];
    const stripped = stripNonMarkup(planted);
    const textRun = />([^<>{}]*?)</g;
    for (let m = textRun.exec(stripped); m; m = textRun.exec(stripped)) {
      if (/\d/.test(m[1] ?? '')) {
        findings.push({ file: 'planted', line: 1, text: m[1] ?? '', kind: 'jsx-text' });
      }
    }
    expect(findings).toHaveLength(1);
    expect(findings[0]?.text).toBe('28');
  });
});
