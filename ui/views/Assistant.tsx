import { useState } from 'react';
import type { BoardRow } from '../data/board';
import type { LeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { ask, TEMPLATES, type Answer } from '../assistant';

/**
 * The query panel: one input, one entry point, three lanes behind it.
 *
 * Each answer shows which lane handled it and why, and each claim carries its tag and
 * its provenance. A user should never have to guess whether a sentence is arithmetic
 * over their own board, a reporter's words, or a model's prose.
 */

export function Assistant({
  data,
  rows,
  league,
}: {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
}) {
  const [question, setQuestion] = useState('');
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [busy, setBusy] = useState(false);

  async function submit(q: string) {
    const trimmed = q.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    try {
      const answer = await ask(trimmed, { data, rows, league });
      setAnswers((prev) => [answer, ...prev]);
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
            <strong>Nothing asked yet.</strong> This panel answers from the exports only. Questions
            that match a template are computed deterministically; player-news questions go to the
            feed lane; anything else goes to the reasoning lane, which works over retrieved context
            and stops when there is none. It will not answer from general football knowledge.
          </div>
        ) : (
          answers.map((answer, i) => <AnswerBlock key={i} answer={answer} onAsk={submit} />)
        )}
      </div>

      <div>
        <div className="templates" style={{ marginBottom: 'var(--pad-y)' }}>
          {TEMPLATES.map((t) => (
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
            aria-label="Ask about the board"
            placeholder="Ask about the board"
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
          {TEMPLATES.map((t) => (
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
