import { applyFilters, NO_FILTERS, type BoardRow } from '../data/board';
import { isStartable, type LeagueConfig } from '../data/league';
import type { Dataset } from '../data/load';
import { runIdOf } from '../data/load';
import { decimal, integer, interval, signed } from '../lib/format';
import { modelClaim, type Claim } from './claim';

/**
 * The deterministic lane. Every answer here is arithmetic over the exports -- same
 * question, same board, same answer, every time.
 *
 * Templates only. A question that matches no template is reported as unmatched rather
 * than guessed at, because the alternative is an assistant that sounds equally
 * confident whether or not it has grounds.
 */

export interface TemplateContext {
  data: Dataset;
  rows: BoardRow[];
  league: LeagueConfig;
}

export interface Template {
  id: string;
  /** Shown in the UI so the user can see what the assistant can actually answer. */
  example: string;
  description: string;
  match: (q: string) => RegExpMatchArray | null;
  run: (m: RegExpMatchArray, ctx: TemplateContext) => Claim[];
}

function boardPath(row: BoardRow, field: string): string {
  return `board.json:players[${row.raw.id - 1}].${field}`;
}

function nameOf(row: BoardRow): string {
  return row.name.kind === 'present' ? row.name.value : 'unknown player';
}

function findPlayer(rows: BoardRow[], query: string): BoardRow | undefined {
  const needle = query.trim().toLowerCase();
  if (!needle) return undefined;
  const exact = rows.find((r) => nameOf(r).toLowerCase() === needle);
  if (exact) return exact;
  return rows.find((r) => nameOf(r).toLowerCase().includes(needle));
}

/**
 * How a row's projection is described. For the 233 sparse players the contract forbids
 * showing the point projection, so the claim says that instead of showing a number --
 * the assistant is held to the same rule as the table.
 */
function projectionClaim(row: BoardRow): Claim {
  if (row.projectedPoints.kind === 'absent') {
    return modelClaim(
      `${nameOf(row)} has no displayable projection: ${row.projectedPoints.reason}`,
      boardPath(row, 'projection_note'),
      row.projectedPoints.runId,
      'low',
    );
  }
  const value = decimal(row.projectedPoints.value);
  const intervalText =
    row.interval.kind === 'present'
      ? ` Its interval is ${interval(row.interval.value.low, row.interval.value.high)}, which applies to ${row.interval.value.appliesTo}, not to the projection.`
      : '';
  return modelClaim(
    `${nameOf(row)} projects ${value} points.${intervalText}`,
    boardPath(row, 'projected_points'),
    row.projectedPoints.runId,
    'low',
  );
}

/** The structural attribution, as one honest claim. There is no evaluative component to split out. */
function attributionClaims(row: BoardRow): Claim[] {
  const runId = row.structuralAdjustment.runId;
  const claims: Claim[] = [];

  if (row.structuralAdjustment.kind === 'present' && row.deltaVsConsensus.kind === 'present') {
    claims.push(
      modelClaim(
        `${nameOf(row)} sits ${signed(row.deltaVsConsensus.value)} against consensus, and all of that movement is structural: it comes from this league's format, not from any opinion about the player.`,
        boardPath(row, 'structural_adjustment'),
        runId,
        'medium',
      ),
    );
  }
  if (
    row.replacementLevelsComponent.kind === 'present' &&
    row.scoringAndVbdComponent.kind === 'present'
  ) {
    claims.push(
      modelClaim(
        `Of that, ${signed(row.replacementLevelsComponent.value)} is this league's replacement levels and ${signed(row.scoringAndVbdComponent.value)} is our scoring rules and VBD method.`,
        boardPath(row, 'structural_breakdown.replacement_levels'),
        runId,
        'medium',
      ),
    );
  }
  claims.push(
    modelClaim(row.evaluativeNote, boardPath(row, 'evaluative_adjustment_note'), runId, 'high'),
  );
  return claims;
}

const bestAvailable: Template = {
  id: 'best_available_at_pick',
  example: 'best available at pick 23',
  description: 'Highest-ranked players left at a given overall pick.',
  match: (q) => q.match(/best\s+available\s*(?:at)?\s*(?:pick)?\s*#?\s*(\d+)/i),
  run: (m, ctx) => {
    const pick = Number(m[1]);
    const runId = runIdOf(ctx.data.manifest, 'board');
    const claims: Claim[] = [];

    // Availability modelling is out of scope, so this does not estimate who will
    // actually be gone. It states its assumption and then does arithmetic.
    claims.push(
      modelClaim(
        `Assuming the ${integer(pick - 1)} picks before yours take the top ${integer(pick - 1)} players on this board, these are the best remaining. This is a stated assumption, not a forecast — no availability model is used.`,
        'board.json:players',
        runId,
        'medium',
      ),
    );

    const remaining = ctx.rows
      .filter((r) => r.overallRank.kind === 'present' && r.overallRank.value >= pick)
      .slice(0, 5);

    if (remaining.length === 0) {
      claims.push(
        modelClaim(
          `No player on the board has an overall rank at or beyond pick ${integer(pick)}. The board runs to ${integer(ctx.rows.length)} players.`,
          'board.json:players',
          runId,
          'high',
        ),
      );
      return claims;
    }

    for (const row of remaining) {
      const startable = isStartable(ctx.league, row.raw.position, row.positionalRank);
      const startableText =
        startable === undefined
          ? ''
          : startable
            ? ' — a startable-tier player in this league'
            : ' — below this league’s startable threshold for the position';
      claims.push(
        modelClaim(
          `${integer(row.overallRank.kind === 'present' ? row.overallRank.value : 0)}. ${nameOf(row)} (${row.positionalLabel.kind === 'present' ? row.positionalLabel.value : ''}, ${row.tierLabel.kind === 'present' ? row.tierLabel.value : ''})${startableText}.`,
          boardPath(row, 'overall_rank'),
          runId,
          'medium',
        ),
      );
    }
    return claims;
  },
};

const comparePlayers: Template = {
  id: 'compare_two_players',
  example: 'compare Bijan Robinson and Deebo Samuel',
  description: 'Side-by-side of two players on every field the board carries.',
  match: (q) => q.match(/compare\s+(.+?)\s+(?:and|vs\.?|versus|with)\s+(.+?)\s*\??$/i),
  run: (m, ctx) => {
    const a = findPlayer(ctx.rows, m[1] ?? '');
    const b = findPlayer(ctx.rows, m[2] ?? '');
    const runId = runIdOf(ctx.data.manifest, 'board');

    const missing: Claim[] = [];
    if (!a) {
      missing.push(
        modelClaim(
          `No player matching "${(m[1] ?? '').trim()}" is on this board.`,
          'board.json:players',
          runId,
          'high',
        ),
      );
    }
    if (!b) {
      missing.push(
        modelClaim(
          `No player matching "${(m[2] ?? '').trim()}" is on this board.`,
          'board.json:players',
          runId,
          'high',
        ),
      );
    }
    if (!a || !b) return missing;

    const claims: Claim[] = [];
    for (const row of [a, b]) {
      claims.push(
        modelClaim(
          `${nameOf(row)} — ${row.positionalLabel.kind === 'present' ? row.positionalLabel.value : ''}, board rank ${integer(row.overallRank.kind === 'present' ? row.overallRank.value : 0)}, consensus ${integer(row.consensusRank.kind === 'present' ? row.consensusRank.value : 0)}, VBD ${decimal(row.vbd.kind === 'present' ? row.vbd.value : 0)}.`,
          boardPath(row, 'overall_rank'),
          runId,
          'medium',
        ),
      );
      claims.push(projectionClaim(row));
      claims.push(...attributionClaims(row));
    }
    return claims;
  },
};

const filterBoard: Template = {
  id: 'filter_board',
  example: 'show WR in tier T2 with delta above 10',
  description: 'Filter the board by position, tier, and delta against consensus.',
  match: (q) =>
    q.match(
      /(?:show|list|which|who)\b(?=.*\b(?:qb|rb|wr|te|tier|delta|sparse)\b)(.*)$/i,
    ),
  run: (m, ctx) => {
    const text = (m[1] ?? '').toLowerCase();
    const runId = runIdOf(ctx.data.manifest, 'board');

    const positions = (['QB', 'RB', 'WR', 'TE'] as const).filter((p) =>
      new RegExp(`\\b${p}s?\\b`, 'i').test(text),
    );
    const tierMatches = [...text.matchAll(/\bt(\d\+?)\b/gi)].map((x) => `T${x[1]}`);
    const above = text.match(/(?:above|over|greater than|>)\s*(-?\d+)/);
    const below = text.match(/(?:below|under|less than|<)\s*(-?\d+)/);

    const filters = {
      ...NO_FILTERS,
      positions: [...positions],
      tiers: tierMatches,
      minDelta: above ? Number(above[1]) : null,
      maxDelta: below ? Number(below[1]) : null,
      sparseOnly: /\bsparse\b/i.test(text),
    };

    const hits = applyFilters(ctx.rows, filters);
    const parts: string[] = [];
    if (positions.length) parts.push(`position ${positions.join(', ')}`);
    if (tierMatches.length) parts.push(`tier ${tierMatches.join(', ')}`);
    if (filters.minDelta !== null) parts.push(`delta above ${integer(filters.minDelta)}`);
    if (filters.maxDelta !== null) parts.push(`delta below ${integer(filters.maxDelta)}`);
    if (filters.sparseOnly) parts.push('projection suppressed');

    const claims: Claim[] = [
      modelClaim(
        `${integer(hits.length)} of ${integer(ctx.rows.length)} players match ${parts.join('; ') || 'no filter'}.`,
        'board.json:players',
        runId,
        'high',
      ),
    ];

    for (const row of hits.slice(0, 10)) {
      claims.push(
        modelClaim(
          `${integer(row.overallRank.kind === 'present' ? row.overallRank.value : 0)}. ${nameOf(row)} (${row.positionalLabel.kind === 'present' ? row.positionalLabel.value : ''}, ${row.tierLabel.kind === 'present' ? row.tierLabel.value : ''}, ${signed(row.deltaVsConsensus.kind === 'present' ? row.deltaVsConsensus.value : 0)} vs consensus)`,
          boardPath(row, 'delta_vs_consensus'),
          runId,
          'medium',
        ),
      );
    }
    if (hits.length > 10) {
      claims.push(
        modelClaim(
          `${integer(hits.length - 10)} more match; the Board view shows the full list under the same filters.`,
          'board.json:players',
          runId,
          'high',
        ),
      );
    }
    return claims;
  },
};

const defineTerm: Template = {
  id: 'define_term',
  example: 'what is VBD',
  description: 'Definitions, straight from the glossary export.',
  match: (q) => q.match(/^(?:what(?:'s| is| are| does)|define)\s+(?:an?\s+|the\s+)?(.+?)(?:\s+mean)?\s*\??$/i),
  run: (m, ctx) => {
    const needle = (m[1] ?? '').trim().toLowerCase();
    const runId = runIdOf(ctx.data.manifest, 'glossary');
    const entry = Object.entries(ctx.data.glossary.terms).find(
      ([term]) => term.toLowerCase() === needle || term.toLowerCase().includes(needle),
    );
    if (!entry) {
      return [
        modelClaim(
          `"${(m[1] ?? '').trim()}" is not in the glossary. It covers: ${Object.keys(ctx.data.glossary.terms).join(', ')}.`,
          'glossary.json:terms',
          runId,
          'high',
        ),
      ];
    }
    const [term, def] = entry;
    return [
      modelClaim(`${term}: ${def.short_definition}`, `glossary.json:terms.${term}.short_definition`, runId, 'high'),
      modelClaim(def.long_explanation, `glossary.json:terms.${term}.long_explanation`, runId, 'high'),
    ];
  },
};

const thresholds: Template = {
  id: 'startable_thresholds',
  example: 'what are the startable thresholds',
  description: 'Startable thresholds per position, read from league config.',
  match: (q) => q.match(/\b(?:startable|replacement level|threshold)s?\b/i),
  run: (_m, ctx) => {
    const claims: Claim[] = [];
    for (const t of ctx.league.thresholds) {
      if (t.level.kind === 'present') {
        claims.push(
          modelClaim(
            `${t.position}: startable through ${t.position}${integer(t.level.value)}.`,
            t.level.path,
            t.level.runId,
            'high',
          ),
        );
      } else {
        claims.push(modelClaim(`${t.position}: ${t.level.reason}`, t.level.path, t.level.runId, 'high'));
      }
    }
    if (ctx.league.thresholdDrift) {
      claims.push(
        modelClaim(ctx.league.thresholdDrift, 'league.json:contract_version', runIdOf(ctx.data.manifest, 'league'), 'high'),
      );
    }
    return claims;
  },
};

const registeredNulls: Template = {
  id: 'registered_nulls',
  example: 'what have we tested and found nothing',
  description: 'Hypotheses that were tested and did not hold up.',
  match: (q) => q.match(/\b(?:null|nulls|failed|didn'?t work|no evidence|tested)\b/i),
  run: (_m, ctx) => {
    const runId = runIdOf(ctx.data.manifest, 'nulls');
    return ctx.data.nulls.findings.map((f, i) =>
      modelClaim(
        `${f.id} — ${f.claim_tested}: ${f.plain_language_summary}`,
        `nulls.json:findings[${i}].plain_language_summary`,
        runId,
        'high',
      ),
    );
  },
};

/** Order matters: the first template that matches wins. Specific patterns come first. */
export const TEMPLATES: readonly Template[] = [
  bestAvailable,
  comparePlayers,
  thresholds,
  registeredNulls,
  filterBoard,
  defineTerm,
];

export function matchTemplate(question: string): { template: Template; m: RegExpMatchArray } | null {
  for (const template of TEMPLATES) {
    const m = template.match(question);
    if (m) return { template, m };
  }
  return null;
}

