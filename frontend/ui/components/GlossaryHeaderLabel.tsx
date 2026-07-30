import type { Dataset } from '../data/load';
import { glossaryShortDefinitionFor } from '../data/glossaryAliases';

/**
 * A column-header label that hovers to the glossary's own short_definition
 * when one exists for `abbreviation` (`docs/design/PROVENANCE-DISCLOSURE.md`'s
 * "class 2" caveat -- one short human sentence, ungated by trace mode, never a
 * field path). The dotted underline is the app's one existing "there's more
 * here" affordance (`docs/design/SUPPLIED-VALUES.md`), reused rather than
 * inventing a second marker -- it does not carry that spec's "you supplied
 * this" meaning here, only its visual "hover me" signal.
 *
 * `overrideTitle` lets a caller keep an existing, more specific tooltip (e.g.
 * ADP's source-and-date note, or DraftRoom's VBD "what the board is ranked
 * on" line) instead of the bare glossary sentence -- the dotted underline
 * still renders, since there is still something to hover. Pass nothing and a
 * column with no glossary entry (MFL, POS, TM, BYE) renders as plain text,
 * same as before this existed.
 */
export function GlossaryHeaderLabel({
  data,
  abbreviation,
  text,
  overrideTitle,
}: {
  data: Dataset;
  abbreviation: string;
  /** The rendered text, when it differs from the bare abbreviation (e.g. "ADP (MFL)"). */
  text?: string;
  overrideTitle?: string;
}) {
  const glossaryTitle = glossaryShortDefinitionFor(data, abbreviation);
  const title = overrideTitle ?? glossaryTitle;
  if (!title) return <>{text ?? abbreviation}</>;
  return (
    <span title={title} style={{ borderBottom: '1px dotted var(--line2)' }}>
      {text ?? abbreviation}
    </span>
  );
}
