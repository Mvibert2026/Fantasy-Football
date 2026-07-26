import { useMemo, useState } from 'react';
import { CATEGORY_LABEL, CATEGORY_ORDER, categoryOf, fieldOf, type GlossaryCategory } from '../data/glossaryCategories';
import type { Dataset } from '../data/load';

/**
 * Glossary, categorised per FRONTEND-SPEC.md §7.3 ("Four categories, two-column
 * cards, backing field + Ask the assistant per term"). Previously a flat
 * definition list and unreachable from navigation -- both fixed here: it now has
 * a Sidebar entry (ui/components/shell/Sidebar.tsx) and groups by
 * ui/data/glossaryCategories.ts's editorial categorisation (glossary.json itself
 * carries no category field; see that module's doc for why grouping real
 * content is an IA decision, not invented data).
 *
 * "Ask the assistant" is visually present but inert, matching this app's
 * existing pattern for features not yet wired end-to-end (Export CSV/PDF,
 * League settings, PlayerDetail's Compare button) -- live-wiring a term straight
 * into the assistant dock's input is cross-cutting work shared with the inline
 * popover version of this same button, not specific to this screen.
 */
export function Glossary({ data }: { data: Dataset }) {
  const [open, setOpen] = useState<string | null>(null);
  const terms = Object.entries(data.glossary.terms);

  const byCategory = useMemo(() => {
    const groups = new Map<GlossaryCategory, Array<[string, (typeof terms)[number][1]]>>();
    for (const [term, def] of terms) {
      const cat = categoryOf(term);
      if (!groups.has(cat)) groups.set(cat, []);
      groups.get(cat)!.push([term, def]);
    }
    return groups;
  }, [terms]);

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

      {CATEGORY_ORDER.filter((cat) => byCategory.has(cat)).map((cat) => (
        <section key={cat}>
          <h3>{CATEGORY_LABEL[cat]}</h3>
          <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
            {byCategory.get(cat)!.map(([term, def]) => {
              const field = fieldOf(term);
              const expanded = open === term;
              return (
                <div key={term} style={{ padding: 14, border: '1px solid var(--line)', background: 'var(--panel)' }}>
                  <button
                    style={{ border: 'none', background: 'none', padding: 0, textAlign: 'left', font: 'inherit', fontSize: 15, fontWeight: 600, cursor: 'pointer' }}
                    aria-expanded={expanded}
                    onClick={() => setOpen(expanded ? null : term)}
                  >
                    {term}
                  </button>
                  <div style={{ marginTop: 8, fontSize: 13, lineHeight: 1.55, color: 'var(--dim)' }}>
                    {def.short_definition}
                  </div>
                  {expanded ? (
                    <p style={{ marginTop: 8, fontSize: 13, lineHeight: 1.55, color: 'var(--dim)' }}>
                      {def.long_explanation}
                    </p>
                  ) : null}
                  <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
                    {field ? <span className="num" style={{ fontSize: 9.5, color: 'var(--dim2)' }}>{field}</span> : null}
                    <span style={{ flex: 1 }} />
                    <button aria-disabled="true" style={{ padding: '3px 8px', background: 'transparent', border: '1px solid var(--line)', color: 'var(--dim2)', fontSize: 11 }}>
                      Ask the assistant
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
