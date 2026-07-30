/**
 * FR-076 (assistant page-context) + FR-077 (standing chat / answer area / 3
 * suggested questions) verification, screenshot-based per docs/operating-
 * model.md's evidence table ("UI screen or component: a screenshot a human
 * has looked at, never a passing test suite alone").
 *
 * This container has no ANTHROPIC_API_KEY (docs/frontend-cloud-runbook.md --
 * confirmed absent again this session), so the real /__reasoning proxy would
 * only ever return "no_key" here. Rather than screenshot that permanent,
 * uninformative state, this script intercepts the POST to /__reasoning at the
 * network layer and returns a scripted reply that ECHOES BACK whatever page-
 * context item ids the real client actually sent -- so the screenshot proves
 * the real request payload (built by ui/assistant/pageContext.ts from a real,
 * live DraftRoom render) reached the network layer with real page-state
 * content in it, and that a follow-up question carries real conversation
 * history. It does not, and cannot in this container, prove the hosted
 * Anthropic call itself succeeds -- that is unchanged from every other
 * capture in this repo (see the cloud runbook's own "Known gaps" item 4).
 *
 * Usage: node e2e/verify-fr076-fr077.mjs [--url http://localhost:5199]
 */

import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const url = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5199';

const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH || '/opt/pw-browsers';
const executablePath = join(browsersPath, 'chromium');

const browser = await chromium.launch({ executablePath });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

const reasoningRequests = [];

await page.route('**/__reasoning', async (route) => {
  const body = JSON.parse(route.request().postData() ?? '{}');
  reasoningRequests.push(body);
  const pageItems = (body.context ?? []).filter((c) => c.id.startsWith('page.'));
  const historyNote =
    (body.history ?? []).length > 0
      ? ` This is turn ${body.history.length + 1} of the conversation; the prior turn's question was "${body.history[body.history.length - 1].question}".`
      : ' This is the first turn of the conversation.';
  const text =
    pageItems.length > 0
      ? `Scripted test reply, grounded in ${pageItems.length} page-context item(s) actually received: ` +
        pageItems.map((i) => `[${i.id}] ${i.text}`).join(' ') +
        historyNote
      : `Scripted test reply: no page-context items were present in this request.${historyNote}`;
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ status: 'ok', text, context_ids: (body.context ?? []).map((c) => c.id) }),
  });
});

// Seed a draft: 2 filler picks so overall pick 3 (this league's real
// pick_sequence[0], user_draft_slot 3, teams 10) is on the clock for the
// user -- same seeding shape as frontend/ui/__tests__/draft-room-middle-pane-
// tabs.test.tsx's seedUpToUsersFirstPick, just written directly to
// localStorage before the app boots.
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.evaluate(() => {
  const now = new Date().toISOString();
  const state = {
    leagueId: 'primary',
    mockId: 'fr076-fr077-verify',
    picks: [1, 2].map((n) => ({
      overallPick: n,
      round: 1,
      teamSlot: n,
      playerId: null,
      playerName: `Filler ${n}`,
      timestamp: now,
      entryMode: 'typed',
    })),
    queue: [],
  };
  localStorage.setItem('prep.draft.primary', JSON.stringify(state));
});

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });

// Switch to Draft mode.
await page.getByRole('button', { name: 'Draft', exact: true }).click();
await page.waitForSelector('text=RECOMMENDED', { timeout: 15_000 }).catch(() => {});

// Open the assistant dock.
await page.getByText('Assistant', { exact: true }).click();
await page.waitForSelector('input[placeholder="Ask about the board"]', { timeout: 15_000 });

// Confirm at most 3 suggested-question buttons before asking anything.
const suggestedButtons = await page.locator('.templates button').count();
console.log(`suggested-question buttons shown: ${suggestedButtons}`);

await page.screenshot({ path: join(artifacts, 'fr077-dock-open-3-suggestions.png') });

// The founder's exact reported failing question.
const founderQuestion = 'what are my likely choices and trade offs at my next pick';
await page.fill('input[placeholder="Ask about the board"]', founderQuestion);
await page.getByRole('button', { name: /^Ask$/ }).click();
await page.waitForSelector('text=Scripted test reply', { timeout: 15_000 });

await page.screenshot({ path: join(artifacts, 'fr076-founder-question-answered.png'), fullPage: true });

// Follow-up, to prove the standing input survived and history is sent.
await page.fill('input[placeholder="Ask a follow-up"]', 'what about the alternative');
await page.getByRole('button', { name: /^Ask$/ }).click();
await page.waitForFunction(
  () => document.querySelectorAll('body').length > 0 && document.body.innerText.includes('turn 2 of the conversation'),
  { timeout: 15_000 },
);

await page.screenshot({ path: join(artifacts, 'fr077-followup-conversation.png'), fullPage: true });

console.log(`reasoning requests captured: ${reasoningRequests.length}`);
reasoningRequests.forEach((r, i) => {
  const pageIds = (r.context ?? []).filter((c) => c.id.startsWith('page.')).map((c) => c.id);
  console.log(`  request ${i + 1}: question=${JSON.stringify(r.question)} history_turns=${(r.history ?? []).length} page_context_ids=${JSON.stringify(pageIds)}`);
});
console.log(`console errors: ${consoleErrors.length}`);
for (const e of consoleErrors) console.log(`  console error: ${e}`);

await browser.close();
