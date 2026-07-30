import { describe, expect, it } from 'vitest';
import { classify } from '../assistant/intent';
import { matchTemplate } from '../assistant/templates';

/**
 * FR-076 root-cause finding: the founder's own reported failing question --
 * "what are my likely choices and trade-offs at my next pick" -- matched
 * `defineTerm`'s regex before this session (any "what ... " question, no
 * length limit on the captured "term"), so it never reached the reasoning
 * lane at all. It was answered with the export lane's "not in the glossary"
 * message, not the reasoning lane's context-based answer. This is a sharper,
 * more literal explanation of the exact complaint than "the reasoning lane
 * lacked page context" -- confirmed here directly, and fixed in
 * `templates.ts`'s `defineTerm.match`. Without this fix, FR-076's whole
 * page-context feature would be unreachable for the literal question that
 * motivated it.
 */

describe('defineTerm no longer swallows open-ended "what ..." questions (FR-076 root cause)', () => {
  it('routes the founder\'s exact reported question to the reasoning lane, not the glossary template', () => {
    const q = 'what are my likely choices and trade-offs at my next pick';
    expect(matchTemplate(q)).toBeNull();
    expect(classify(q).lane).toBe('reasoning');
  });

  it('still matches genuine short glossary questions', () => {
    expect(matchTemplate('what is VBD')?.template.id).toBe('define_term');
    expect(matchTemplate('what is a confidence interval')?.template.id).toBe('define_term');
    expect(classify('what is VBD').lane).toBe('export');
  });

  it('rejects other long "what ..." questions the same way, not just the one reported question', () => {
    expect(matchTemplate('what should I do if my best running back gets hurt this week')).toBeNull();
    expect(classify('what should I do if my best running back gets hurt this week').lane).toBe('news');
  });
});
