import { Fragment, useState } from 'react';
import type { Dataset } from '../data/load';

/** The glossary, straight from glossary.json. Short definition inline, long one on demand. */
export function Glossary({ data }: { data: Dataset }) {
  const [open, setOpen] = useState<string | null>(null);
  const terms = Object.entries(data.glossary.terms);

  if (terms.length === 0) {
    return (
      <div className="stack">
        <h2>Glossary</h2>
        <div className="empty">
          <strong>No terms in the export.</strong> glossary.json carries an empty term list.
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <section>
        <h2>Glossary</h2>
        <p style={{ color: 'var(--fg-muted)' }}>
          Written for a reader who is not a statistician. Select a term for the longer explanation.
        </p>
      </section>
      <dl className="defs">
        {terms.map(([term, def]) => (
          <Fragment key={term}>
            <dt>
              <button
                style={{ border: 'none', background: 'none', padding: 0, textAlign: 'left', font: 'inherit' }}
                aria-expanded={open === term}
                onClick={() => setOpen(open === term ? null : term)}
              >
                {term}
              </button>
            </dt>
            <dd>
              {def.short_definition}
              {open === term ? (
                <p style={{ marginTop: 'var(--pad-y)', color: 'var(--fg-muted)' }}>
                  {def.long_explanation}
                </p>
              ) : null}
            </dd>
          </Fragment>
        ))}
      </dl>
    </div>
  );
}
