import { ciTargetFor, type BoardRow } from '../data/board';
import { GLOSSARY_ALIASES } from '../data/glossaryAliases';
import type { Dataset } from '../data/load';
import { decimal, integer, percent, signed } from '../lib/format';
import type { ContextItem } from './reasoning';

/**
 * Lexical retrieval over the shipped export artifacts, for questions that match
 * none of the seven deterministic templates in `templates.ts`.
 *
 * FR-048's "real bottleneck" finding: before this file existed, an unmatched
 * question reached the reasoning lane with either a hand-written substring match
 * on player names/glossary terms/nulls keywords, or -- when even that found
 * nothing -- an unconditional dump of every strategy and every nulls finding
 * regardless of relevance. The first was too narrow (missed anything not phrased
 * as a name); the second was too wide (retrieval that always returns something is
 * indistinguishable, from the model's perspective, from no retrieval at all --
 * it is just a fixed prompt). Both violate the same rule from opposite directions.
 *
 * What replaces them: a small BM25-style scorer over one corpus built from every
 * artifact `frontend/public/data/` ships (board rows, glossary terms, strategies,
 * league.json, nulls.json, player_descriptions.json). No embedding model, no
 * dependency -- the corpus is a few hundred short documents, comfortably within
 * what keyword scoring handles well, and a browser can score all of them in
 * microseconds. Two things this scorer is responsible for keeping honest:
 *
 *   1. Nothing is retrieved below a relevance floor. A query that shares no
 *      distinctive vocabulary with anything in the corpus gets an empty result,
 *      not the fallback dump. Rule 3 (the assistant refuses rather than answers
 *      from general football knowledge) depends on retrieval being able to
 *      truthfully report "nothing found."
 *   2. Confidence tracks match quality, not the shape of the underlying data. An
 *      exact player-name or glossary-term match is 'high'; a real but partial
 *      keyword overlap is 'medium'; a single generic shared word is 'low'. A row
 *      with a precise number in it is not 'high' confidence if the reason it was
 *      retrieved is a weak lexical accident.
 */

interface RetrievalDoc {
  id: string;
  text: string;
  source_path: string;
  /**
   * Strings that, if the user's question contains one verbatim (case-insensitive
   * substring), mark this as an exact rather than a lexical match -- a player's
   * full name, a glossary term. Forces 'high' confidence the same way the old
   * narrow name matcher did, without gating retrieval on it being the only path.
   */
  identifiers: string[];
  /**
   * When any *other* doc of this `kindOf(...)` value is retrieved on lexical
   * merit, attach this doc too, even if it scored below the relevance floor on
   * its own. For a caveat that must travel with a result whenever that result's
   * *kind* is shown -- e.g. strategies.json's power-floor and not-compositional
   * notes, which are short and share little vocabulary with most strategy
   * questions but are dishonest to omit whenever a strategy comparison is
   * actually being shown. Never fires on a bare, unrelated query -- only when
   * lexical retrieval already surfaced something of that kind.
   */
  attachWhenKindPresent?: string;
}

interface IndexedDoc extends RetrievalDoc {
  termFreqs: Map<string, number>;
  length: number;
}

function tokenize(text: string): string[] {
  return (text.toLowerCase().match(/[a-z0-9]+/g) ?? []).filter((t) => t.length >= 2);
}

// BM25 defaults (Robertson/Sparck Jones). Not tuned against a labelled set --
// there isn't one -- but these are the standard textbook values, not invented.
const K1 = 1.4;
const B = 0.75;

/** log(1 + (N-df+0.5)/(df+0.5)) -- the BM25+ variant, always non-negative, so a
 *  token that appears in literally every document scores 0 rather than negative
 *  and cannot drag a real match's score down. */
function idf(df: number, N: number): number {
  return Math.log(1 + (N - df + 0.5) / (df + 0.5));
}

/** A token counts as "distinctive" -- able to justify a retrieval on its own --
 *  only once it's absent from a solid majority of the corpus. Below this idf, a
 *  shared token is common English or common domain vocabulary ("points", "the",
 *  "player"), not evidence the two texts are actually about the same thing. */
const DISTINCTIVE_IDF_MIN = 2.0;

/** Minimum BM25 score to retrieve at all. Below this, even a distinctive-token
 *  hit is too weak to hand to the model -- e.g. one incidental shared word in an
 *  otherwise long, unrelated document. */
const MIN_SCORE = 0.6;

/**
 * A non-exact match needs at least this many *distinct* distinctive tokens
 * shared with the query, not just one. One rare shared word is often a false
 * friend rather than real topical overlap -- e.g. "wide" in "wide means we are
 * guessing" (the glossary's confidence-interval entry) lexically matching "wide
 * receivers" in a draft-strategy question. A single word carries no context to
 * disambiguate; two independently-distinctive words sharing a document is much
 * harder to get from an unrelated topic by accident.
 */
const MIN_DISTINCTIVE_MATCHES = 2;

/** Score at or above which a non-exact match is worth calling 'medium' rather
 *  than 'low' confidence. */
const MEDIUM_SCORE = 2.2;

const TOP_K = 8;

/**
 * Per-artifact cap on non-exact matches in one result set. `player_descriptions.json`
 * templates its prose per archetype ("a secondary receiving option at tight end..."),
 * so dozens of unrelated bench players can share the exact same distinctive phrase --
 * without a cap, a positional question ("when should I take a tight end") returns
 * eight near-duplicate archetype blurbs and crowds out the one nulls.json finding
 * that actually answers it. Exact identifier matches (a named player, a named
 * glossary term) bypass this: a deliberate lookup is never capped away.
 */
const MAX_PER_KIND = 3;

/** The artifact a doc id belongs to, e.g. "board.6.identity" -> "board". */
function kindOf(id: string): string {
  return id.split('.')[0] ?? id;
}

function buildIndex(docs: readonly RetrievalDoc[]): {
  docs: IndexedDoc[];
  df: Map<string, number>;
  avgdl: number;
  N: number;
} {
  const indexed: IndexedDoc[] = docs.map((d) => {
    const tokens = tokenize(d.text);
    const termFreqs = new Map<string, number>();
    for (const t of tokens) termFreqs.set(t, (termFreqs.get(t) ?? 0) + 1);
    return { ...d, termFreqs, length: tokens.length };
  });

  const df = new Map<string, number>();
  for (const d of indexed) {
    for (const t of d.termFreqs.keys()) df.set(t, (df.get(t) ?? 0) + 1);
  }

  const N = indexed.length;
  const avgdl = N > 0 ? indexed.reduce((sum, d) => sum + d.length, 0) / N : 0;

  return { docs: indexed, df, avgdl, N };
}

function scoreDoc(
  doc: IndexedDoc,
  queryTokens: readonly string[],
  df: Map<string, number>,
  avgdl: number,
  N: number,
): { score: number; distinctiveMatches: number } {
  let score = 0;
  let distinctiveMatches = 0;

  for (const t of queryTokens) {
    const tf = doc.termFreqs.get(t);
    if (!tf) continue;
    const weight = idf(df.get(t) ?? N, N);
    const denom = tf + K1 * (1 - B + (B * doc.length) / (avgdl || 1));
    score += weight * ((tf * (K1 + 1)) / denom);
    if (weight >= DISTINCTIVE_IDF_MIN) distinctiveMatches += 1;
  }

  return { score, distinctiveMatches };
}

/**
 * Scores `question` against `corpus` and returns the top matches as
 * `ContextItem`s, honestly tagged. Returns an empty array when nothing clears
 * the relevance floor -- that is the expected, correct result for a question
 * with no real answer in the shipped exports, not a bug to work around.
 */
interface ScoredDoc {
  doc: IndexedDoc;
  score: number;
  distinctiveMatches: number;
  exact: boolean;
  /** Present (true) only for a doc added by `attachWhenKindPresent`, never found
   *  by lexical scoring at all. See that field's doc comment. */
  attached?: boolean;
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Whole-word match, not a bare substring. Player full names and multi-word
 * glossary terms were always long enough for plain `includes()` to be safe,
 * but the glossary alias map (added for the "CI" abbreviation, 2026-07-30)
 * introduced 2-4 letter identifiers -- "ci" is a substring of "decision",
 * "efficient", "specific" and dozens of other ordinary words, and a bare
 * substring match would have turned an unrelated question into a false
 * 'high'-confidence hit. `\b` word boundaries make an identifier match only
 * when it appears as its own word (or exact multi-word phrase), which is what
 * "exact match" is supposed to mean here.
 */
function isExactIdentifierMatch(question: string, identifier: string): boolean {
  if (identifier.length === 0) return false;
  return new RegExp(`\\b${escapeRegExp(identifier.toLowerCase())}\\b`, 'i').test(question);
}

export function retrieve(corpus: readonly RetrievalDoc[], question: string): ContextItem[] {
  const queryTokens = Array.from(new Set(tokenize(question)));
  if (queryTokens.length === 0 || corpus.length === 0) return [];

  const q = question.toLowerCase();
  const { docs, df, avgdl, N } = buildIndex(corpus);

  const scored: ScoredDoc[] = docs
    .map((doc) => {
      const { score, distinctiveMatches } = scoreDoc(doc, queryTokens, df, avgdl, N);
      const exact = doc.identifiers.some((id) => isExactIdentifierMatch(q, id));
      return { doc, score, distinctiveMatches, exact };
    })
    .filter((s) => s.exact || (s.distinctiveMatches >= MIN_DISTINCTIVE_MATCHES && s.score >= MIN_SCORE));

  scored.sort((a, b) => {
    if (a.exact !== b.exact) return a.exact ? -1 : 1;
    return b.score - a.score;
  });

  const kindCounts = new Map<string, number>();
  const diversified: typeof scored = [];
  for (const s of scored) {
    if (diversified.length >= TOP_K) break;
    const kind = kindOf(s.doc.id);
    const count = kindCounts.get(kind) ?? 0;
    if (!s.exact && count >= MAX_PER_KIND) continue;
    kindCounts.set(kind, count + 1);
    diversified.push(s);
  }

  // Attach any doc whose `attachWhenKindPresent` names a kind that's actually in
  // the result set -- conditioned on real lexical relevance already having found
  // something of that kind, never on the bare query. See the field's doc comment.
  const presentKinds = new Set(diversified.map((s) => kindOf(s.doc.id)));
  const attachedIds = new Set(diversified.map((s) => s.doc.id));
  for (const doc of docs) {
    if (!doc.attachWhenKindPresent || attachedIds.has(doc.id)) continue;
    if (!presentKinds.has(doc.attachWhenKindPresent)) continue;
    diversified.push({ doc, score: 0, distinctiveMatches: 0, exact: false, attached: true });
    attachedIds.add(doc.id);
  }

  return diversified.map((s): ContextItem => {
    // Every retrieved non-exact match already cleared MIN_DISTINCTIVE_MATCHES (2),
    // so 'low' is the floor, not a rare case: exactly two shared distinctive words
    // is real but thin evidence. A third independent word, or a high score
    // concentrated in fewer terms, is what earns 'medium'. An attached companion
    // (see attachWhenKindPresent) is 'high' on different grounds than an exact
    // match -- it wasn't found by a loose keyword accident, it's a deterministic,
    // always-applicable pairing to whatever kind of result triggered it.
    const confidence: ContextItem['confidence'] =
      s.exact || s.attached
        ? 'high'
        : s.distinctiveMatches >= 3 || s.score >= MEDIUM_SCORE
          ? 'medium'
          : 'low';
    return {
      id: s.doc.id,
      text: s.doc.text,
      confidence,
      source_path: s.doc.source_path,
    };
  });
}

// --- Corpus construction -----------------------------------------------------

function nameOf(row: BoardRow): string {
  return row.name.kind === 'present' ? row.name.value : '';
}

/**
 * `adp_selected_pct` is already a 0-100 percentage (16.0 means 16%), not the
 * 0-1 fraction `lib/format.ts#percent` expects (that one is correct for
 * `flex_split_assumption`, used below) -- a bare `percent()` call here would
 * render 16.0 as "1600%". Same local formatter and honest-zero /
 * genuinely-small distinction as `PlayerDetail.tsx`'s `adpPctText`, duplicated
 * rather than imported to keep this module's only dependency on `ui/data/` and
 * `ui/lib/`, not on a view component.
 */
function adpPctText(n: number): string {
  if (n > 0 && n < 1) return '<1%';
  return `${Math.round(n)}%`;
}

/** One document per board row, combining identity, ranking, projection and
 *  structural-attribution fields into a single retrievable text -- the same
 *  facts `templates.ts`'s `bestAvailable`/`comparePlayers` cite individually,
 *  read here as prose so a differently-phrased question can still find them. */
function boardDocs(rows: readonly BoardRow[]): RetrievalDoc[] {
  const docs: RetrievalDoc[] = [];

  for (const row of rows) {
    const name = nameOf(row);
    if (!name) continue;
    const i = row.raw.id - 1;
    const at = (field: string) => `board.json:players[${i}].${field}`;

    const label = row.positionalLabel.kind === 'present' ? row.positionalLabel.value : row.raw.position;
    const tier = row.tierLabel.kind === 'present' ? row.tierLabel.value : 'unknown tier';
    const rank = row.overallRank.kind === 'present' ? integer(row.overallRank.value) : 'unranked';
    const consensus = row.consensusRank.kind === 'present' ? integer(row.consensusRank.value) : 'unranked';
    const delta = row.deltaVsConsensus.kind === 'present' ? signed(row.deltaVsConsensus.value) : 'unknown';
    const vbd = row.vbd.kind === 'present' ? decimal(row.vbd.value) : 'unknown';

    const projectionText =
      row.projectedPoints.kind === 'present'
        ? `${name} projects ${decimal(row.projectedPoints.value)} points.`
        : `${name} has no displayable projection: ${row.projectedPoints.reason}`;

    // Founder, 2026-07-30, after the CI/VBD mislabelling was explained and
    // fixed on screen: "the chat bot should have been able to answer the
    // question like you did about CI." It couldn't, because this doc never
    // mentioned the interval or what it applies to -- the assistant saw the
    // same two numbers the founder did and had nothing to reconcile them
    // with. `ciTargetFor` reads `ci_applies_to` per row rather than assuming
    // "vbd"; this is the fact, not a hand-written answer -- the reasoning
    // lane still has to use it to actually answer the question.
    const ciTarget = ciTargetFor(row);
    const ciText =
      row.interval.kind === 'present'
        ? ciTarget.kind === 'known'
          ? ` ${name} also has an interval on file, ${decimal(row.interval.value.low)}-${decimal(row.interval.value.high)}, which applies to ${ciTarget.label} (${ciTarget.quantity === 'vbd' ? 'value over replacement' : 'the point projection'}), not to whichever other number is being discussed unless that number is ${ciTarget.label}.`
          : ` ${name} also has an interval on file, ${decimal(row.interval.value.low)}-${decimal(row.interval.value.high)}, which applies to "${ciTarget.kind === 'unrecognized' ? ciTarget.raw : ''}", a quantity this app does not otherwise display.`
        : '';

    const adpText =
      row.adp.kind === 'present'
        ? `MyFantasyLeague proxy ADP has ${name} at pick ${decimal(row.adp.value)}` +
          (row.adpMinPick.kind === 'present' && row.adpMaxPick.kind === 'present'
            ? `, drafted between picks ${integer(row.adpMinPick.value)} and ${integer(row.adpMaxPick.value)}`
            : '') +
          (row.adpSelectedPct.kind === 'present' ? `, selected in ${adpPctText(row.adpSelectedPct.value)} of drafts sampled` : '') +
          '.'
        : `No ADP figure for ${name}: ${row.adp.reason}`;

    const rosterStatusText =
      row.raw.roster_status === 'no_active_contract_on_file'
        ? ` ${name} has no active contract on file (this is a proxy signal, not a confirmed retirement or roster cut).`
        : '';

    const suspensionText = row.raw.suspension_flag
      ? ` ${name} carries a suspension: ${integer(row.raw.suspension_games ?? 0)} games. ${row.raw.suspension_adjustment_note ?? ''}`
      : '';

    docs.push({
      id: `board.${row.raw.id}.identity`,
      text:
        `${name} is a ${label}, tier ${tier}, on this board at overall rank ${rank}. Consensus has ` +
        `${name} at ${consensus}, a difference of ${delta}. VBD ${vbd}. ${projectionText} ${adpText}` +
        `${rosterStatusText}${suspensionText}${ciText}`,
      source_path: at('overall_rank'),
      identifiers: [name],
    });

    docs.push({
      id: `board.${row.raw.id}.attribution`,
      text: `${name}'s difference against consensus is entirely structural, reflecting this league's format, not an opinion about the player. ${row.evaluativeNote}`,
      source_path: at('evaluative_adjustment_note'),
      identifiers: [name],
    });
  }

  return docs;
}

/**
 * One document per glossary term, term + both definitions, so either the
 * short or long wording can be the thing that matches a differently-phrased
 * question.
 *
 * `identifiers` also carries every UI abbreviation that `GLOSSARY_ALIASES`
 * maps onto this term ("CI" -> "confidence interval", etc.) -- the founder
 * asked this exact question ("what is CI") and retrieval found nothing,
 * because the column header renders "CI" and the glossary key is the spelled-
 * out term; nothing connected them. This is the fix: an exact-identifier hit
 * on the abbreviation the user actually saw now resolves to the real term.
 */
function glossaryDocs(data: Dataset): RetrievalDoc[] {
  const aliasesByTerm = new Map<string, string[]>();
  for (const [abbr, term] of Object.entries(GLOSSARY_ALIASES)) {
    const list = aliasesByTerm.get(term) ?? [];
    list.push(abbr);
    aliasesByTerm.set(term, list);
  }
  return Object.entries(data.glossary.terms).map(([term, def]) => ({
    id: `glossary.${term}`,
    text: `${term}: ${def.short_definition} ${def.long_explanation}`,
    source_path: `glossary.json:terms.${term}.short_definition`,
    identifiers: [term, ...(aliasesByTerm.get(term) ?? [])],
  }));
}

/** Per-strategy summary at sigma 10 (the export's own "about one round of
 *  slippage" reading), plus the power-floor caveat and the not-compositional
 *  note -- unchanged in substance from the retiring narrow/fallback logic, just
 *  now scored like everything else instead of dumped unconditionally. */
function strategyDocs(data: Dataset): RetrievalDoc[] {
  const s = data.strategies;
  if (!s) return [];
  const docs: RetrievalDoc[] = [];

  for (const [i, strategy] of s.strategies.entries()) {
    const cell = strategy.by_sigma.find((c) => c.sigma === 10) ?? strategy.by_sigma[0];
    if (!cell) continue;
    const j = strategy.by_sigma.indexOf(cell);

    const margin =
      cell.margin_vs_baseline === null
        ? ''
        : ` Margin vs. the baseline: ${cell.margin_vs_baseline > 0 ? '+' : ''}${decimal(cell.margin_vs_baseline)} points.`;
    const seasons =
      cell.seasons_positive === null
        ? ''
        : ` Positive in ${integer(cell.seasons_positive)} of ${integer(s.power_floor.n_seasons)} simulated seasons.`;
    const signTest = cell.sign_test_p === null ? '' : ` Sign-test p = ${decimal(cell.sign_test_p)}.`;

    docs.push({
      id: `strategies.${i}.summary`,
      text:
        `Draft strategy "${strategy.name}"${strategy.is_baseline ? ' (the baseline every other strategy is measured against)' : ''}: ` +
        `${strategy.verdict} At sigma ${integer(cell.sigma)}, mean roster points ${decimal(cell.mean_roster_points)}.` +
        `${margin}${seasons}${signTest}`,
      source_path: `strategies.json:strategies[${i}].by_sigma[${j}]`,
      identifiers: [strategy.name, strategy.name.replace(/_/g, ' ')],
    });
  }

  // These two travel with any strategy result on relevance grounds alone too
  // rarely -- short, low-vocabulary-overlap caveats -- but are dishonest to
  // omit whenever a strategy comparison is actually being shown. Attached via
  // `attachWhenKindPresent` rather than always dumped: they still don't appear
  // for a question with no strategy content in it at all.
  docs.push({
    id: 'strategies.power_floor',
    text: s.power_floor.plain_english,
    source_path: 'strategies.json:power_floor.plain_english',
    identifiers: [],
    attachWhenKindPresent: 'strategies',
  });

  docs.push({
    id: 'strategies.not_compositional',
    text:
      'Each draft strategy above was simulated independently against the baseline, one at a time. There is no ' +
      'simulation of combining two strategies into a single draft plan, and these numbers cannot be added ' +
      'or averaged together to produce one -- that would need a new simulation run, not arithmetic on the ' +
      'existing results.',
    source_path: 'strategies.json:strategies',
    identifiers: [],
    attachWhenKindPresent: 'strategies',
  });

  return docs;
}

/** league.json, split into a handful of topic documents rather than one giant
 *  blob -- so a scoring question and a roster-shape question retrieve
 *  independently instead of always dragging the whole file in together. */
function leagueDocs(data: Dataset): RetrievalDoc[] {
  const L = data.league;
  const docs: RetrievalDoc[] = [];

  docs.push({
    id: 'league.identity',
    text:
      `This league is "${L.league_name ?? L.league_id ?? 'unnamed'}"` +
      `${L.platform ? ` on ${L.platform}` : ''}, ${L.teams}-team, ${L.rounds}-round` +
      `${L.draft_type ? `, ${L.draft_type} draft` : ''}. The user's draft slot is ${L.user_draft_slot}.`,
    source_path: 'league.json:teams',
    identifiers: L.league_name ? [L.league_name] : [],
  });

  const scoring = L.scoring as Record<string, unknown>;
  const offense = scoring.offense as Record<string, unknown> | undefined;
  if (offense) {
    docs.push({
      id: 'league.scoring.offense',
      text:
        `This league's offensive scoring: half-point-per-reception (0.5 per reception), ` +
        `passing touchdown ${offense.passing_td}, interception ${offense.interception}, ` +
        `rushing touchdown ${offense.rushing_td}, receiving touchdown ${offense.receiving_td}, ` +
        `fumble lost ${offense.fumbles_lost}, two-point conversion ${offense.two_point_conversion}. ` +
        `Passing, rushing and receiving yardage all carry stacking bonuses at yardage thresholds ` +
        `(a player crossing multiple thresholds in one game gets every applicable bonus, not just the highest).`,
      source_path: 'league.json:scoring.offense',
      identifiers: [],
    });
  }

  docs.push({
    id: 'league.roster',
    text:
      `Roster shape: starters ${Object.entries(L.roster.starters)
        .map(([pos, n]) => `${n} ${pos}`)
        .join(', ')}, flex-eligible positions ${L.roster.flex_eligible.join('/')}, ` +
      `${L.roster.bench} bench spots, ${L.roster.ir} IR spot${L.roster.ir === 1 ? '' : 's'}` +
      `${L.roster.kicker ? '' : ', no kicker'}.`,
    source_path: 'league.json:roster',
    identifiers: [],
  });

  docs.push({
    id: 'league.replacement_levels',
    text:
      `Replacement levels used for VBD in this league: ${Object.entries(L.replacement_levels)
        .map(([pos, n]) => `${pos} ${n}`)
        .join(', ')}. ${L.replacement_levels_note}` +
      (L.positions_without_replacement_levels?.length
        ? ` No replacement level is published for ${L.positions_without_replacement_levels.join(', ')}. ${L.positions_without_replacement_levels_note ?? ''}`
        : ''),
    source_path: 'league.json:replacement_levels',
    identifiers: [],
  });

  docs.push({
    id: 'league.flex_split',
    text: `Flex-slot split assumption: ${Object.entries(L.flex_split_assumption)
      .map(([pos, frac]) => `${pos} ${percent(frac)}`)
      .join(', ')}. ${L.flex_split_note}`,
    source_path: 'league.json:flex_split_assumption',
    identifiers: [],
  });

  docs.push({
    id: 'league.playoff',
    text:
      `Playoffs: top ${L.playoff.teams} teams, weeks ${L.playoff.weeks.join('-')}, ` +
      `${L.playoff.reseeding ? 'with' : 'no'} reseeding. Trade deadline ${L.trade_deadline}. FAAB budget ${L.faab_budget}.`,
    source_path: 'league.json:playoff',
    identifiers: [],
  });

  return docs;
}

/** One document per nulls.json finding, including `method`/`result` alongside
 *  the plain-language summary -- broadens the vocabulary a question can hit
 *  without changing which sentence gets cited (still the plain-language one). */
function nullsDocs(data: Dataset): RetrievalDoc[] {
  return data.nulls.findings.map((f, i) => ({
    id: `nulls.${f.id}`,
    text: `We tested this and found nothing conclusive. ${f.claim_tested} Method: ${f.method} Result: ${f.result} ${f.plain_language_summary}`,
    source_path: `nulls.json:findings[${i}].plain_language_summary`,
    identifiers: [],
  }));
}

/**
 * `player_descriptions.json` -- AI-generated, display-only archetype prose
 * (ADR-044). Primary league only; `data.playerDescriptions` is `null` (or, in
 * the standalone build, `undefined` -- that embed deliberately excludes this
 * artifact) for every other case, and this degrades to zero documents rather
 * than throwing.
 */
function playerDescriptionDocs(data: Dataset): RetrievalDoc[] {
  const pd = data.playerDescriptions;
  if (!pd) return [];
  return pd.players.map((p, i) => ({
    id: `player_descriptions.${p.player_id}`,
    text: `${p.player_name} (${p.position}): ${p.description}`,
    source_path: `player_descriptions.json:players[${i}].description`,
    identifiers: [p.player_name],
  }));
}

export function buildCorpus(data: Dataset, rows: readonly BoardRow[]): RetrievalDoc[] {
  return [
    ...boardDocs(rows),
    ...glossaryDocs(data),
    ...strategyDocs(data),
    ...leagueDocs(data),
    ...nullsDocs(data),
    ...playerDescriptionDocs(data),
  ];
}
