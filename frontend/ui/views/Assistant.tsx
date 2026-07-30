import { useEffect, useRef, useState } from 'react';
import type { BoardRow } from '../data/board';
import type { LeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { ask, SUGGESTED_TEMPLATES, type Answer, type ContextItem, type ConversationTurn } from '../assistant';

/**
 * The query panel: a standing input, a persistent answer area showing the
 * running conversation, and a small set of starter questions.
 *
 * FR-077 ("it needs a clear standing chat box, and an answer area, shrink the
 * number of suggested or relevant questions to 3 tops"): the input itself was
 * already persistent -- it never disappeared after a question -- so the
 * founder's actual complaint was structural: no real conversation (every
 * question was answered in isolation, so a follow-up had nothing to refer
 * back to), too many suggested-question buttons, and no clear "this is one
 * ongoing chat" reading to the panel. All three are fixed here: turns render
 * oldest-first with the newest at the bottom (a chat reads top-to-bottom, the
 * previous newest-first stack read like a feed of unrelated answers), the
 * panel auto-scrolls to the newest turn, `history` is threaded into every
 * `ask()` call so the reasoning lane can resolve "what about him," and the
 * starter buttons are capped to `SUGGESTED_TEMPLATES` (3).
 *
 * Each answer still shows which lane handled it and why, and each claim still
 * carries its tag and its provenance -- FR-077 changes how the conversation is
 * held, not what an answer is allowed to claim.
 */

export function Assistant({
  data,
  rows,
  league,
  pageContext,
}: {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
  /** FR-076: the bounded page-context bundle for whatever screen the app is
   *  currently on -- `[]` outside an active draft. Passed straight through to
   *  `ask()`, which hands it to the reasoning lane alongside lexical
   *  retrieval. Nothing in this component reads its contents directly. */
  pageContext?: ContextItem[];
}) {
  const [question, setQuestion] = useState('');
  const [answers, setAnswers] = useState<Answer[]>([]);
  // FR-077: the actual fix. Without this, "standing chat box" was cosmetic --
  // every question still reached the reasoning lane with no memory of what was
  // just discussed. One turn per answer, oldest first, bounded before it ever
  // leaves this component (reasoning.ts's boundHistory trims it further).
  const [history, setHistory] = useState<ConversationTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const answersEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // jsdom (this app's own test environment) doesn't implement
    // scrollIntoView -- guarded rather than assumed, so a real browser still
    // gets the auto-scroll and the test suite doesn't need a polyfill for it.
    answersEndRef.current?.scrollIntoView?.({ block: 'end' });
  }, [answers.length]);

  async function submit(q: string) {
    const trimmed = q.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    try {
      const answer = await ask(trimmed, { data, rows, league, pageContext }, history);
      setAnswers((prev) => [...prev, answer]);
      setHistory((prev) => [...prev, { question: trimmed, answerText: flattenAnswer(answer) }]);
      setQuestion('');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="assistant">
      <div className="answers">
        {answers.length === 0 ? (
          <div className="empty">
            <strong>Nothing asked yet.</strong> Answers come only from the exports and, on the draft
            screen, what's currently on screen. Nothing is ever answered from general football
            knowledge.
          </div>
        ) : (
          answers.map((answer, i) => <AnswerBlock key={i} answer={answer} onAsk={submit} />)
        )}
        <div ref={answersEndRef} />
      </div>

      <div>
        <div className="templates" style={{ marginBottom: 'var(--pad-y)' }}>
          {SUGGESTED_TEMPLATES.map((t) => (
            <button key={t.id} title={t.description} onClick={() => submit(t.example)}>
              {t.example}
            </button>
          ))}
        </div>
        <form
          className="ask"
          onSubmit={(e) => {
            e.preventDefault();
            void submit(question);
          }}
        >
          <input
            aria-label={history.length === 0 ? 'Ask about the board' : 'Ask a follow-up'}
            placeholder={history.length === 0 ? 'Ask about the board' : 'Ask a follow-up'}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button type="submit" disabled={busy}>
            {busy ? 'Working' : 'Ask'}
          </button>
        </form>
      </div>
    </div>
  );
}

/**
 * The prior turn's answer, flattened to plain text for `ConversationTurn`.
 * Claims joined with the tag stripped (history is for referents, not for
 * re-citing) -- a notice (no claims) is flattened the same way so a follow-up
 * to "that wasn't in the exports" still has something to refer back to.
 */
function flattenAnswer(answer: Answer): string {
  if (answer.claims.length > 0) return answer.claims.map((c) => c.text).join(' ');
  return answer.notice ?? '';
}

function AnswerBlock({ answer, onAsk }: { answer: Answer; onAsk: (q: string) => void }) {
  return (
    <section>
      <h3>{answer.question}</h3>
      <p style={{ fontSize: 'var(--fs-xs)', color: 'var(--fg-faint)' }}>
        {`${answer.lane} lane — ${answer.rationale}`}
      </p>

      {answer.notice ? (
        <div className="empty" style={{ whiteSpace: 'pre-wrap' }}>
          {answer.notice}
        </div>
      ) : null}

      {answer.showTemplates ? (
        <div className="templates" style={{ marginTop: 'var(--pad-y)' }}>
          {SUGGESTED_TEMPLATES.map((t) => (
            <button key={t.id} title={t.description} onClick={() => onAsk(t.example)}>
              {t.example}
            </button>
          ))}
        </div>
      ) : null}

      {answer.claims.map((claim, i) => (
        <div className="claim" key={i}>
          <span className={`tag tag-${claim.tag}`}>{claim.tag}</span>
          {claim.age ? <span className="tag tag-SOURCE">{claim.age}</span> : null}
          <span>{claim.text}</span>
          <div className="provenance">
            {claim.provenance}
            {claim.confidence ? ` · confidence ${claim.confidence}` : ''}
          </div>
        </div>
      ))}
    </section>
  );
}
