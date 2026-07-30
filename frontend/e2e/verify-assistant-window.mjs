/**
 * ASSISTANT-WINDOW.md item 4 visual verification (one-off, kept for provenance,
 * pattern from e2e/verify-069-073.mjs).
 *
 * Captures, against a RUNNING dev server (default http://localhost:5190):
 *   1. fr077-followup-assistant-empty.png -- freshly opened, nothing asked yet,
 *      the scope note ("Answers come only from the exports...") and the three
 *      suggestion chips both visible.
 *   2. fr077-followup-assistant-scroll-top.png / -scroll-bottom.png -- a long,
 *      multi-paragraph mocked answer (the reasoning lane's /__reasoning
 *      endpoint is intercepted so this needs no ANTHROPIC_API_KEY), the
 *      transcript scrolled to its top and then its bottom, header and input
 *      visibly pinned in both.
 *   3. fr077-followup-assistant-collapsed.png -- collapsed to the header pill.
 *   4. fr077-followup-assistant-sources-off.png / -sources-trace-on.png --
 *      the per-answer "N sources" disclosure opened, first with the trace
 *      switch off (a bare tag pill, no field path), then on via Alt+T (the
 *      pill expands to the raw context key -- "In trace mode that expands
 *      to the page.* keys" from ASSISTANT-WINDOW.md item 4).
 *
 * Usage: node e2e/verify-assistant-window.mjs [--url http://localhost:5190]
 */

import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const artifacts = join(root, 'e2e', 'artifacts');
mkdirSync(artifacts, { recursive: true });

const args = process.argv.slice(2);
const url = args.includes('--url') ? args[args.indexOf('--url') + 1] : 'http://localhost:5190';

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1440, height: 780 } });

const LONG_ANSWER = [
  'Bijan is 4% to still be there at 18 and Ja\'Marr Chase is 0%. That difference, not the point gap, is the reason for the order.',
  'The next tier down is thinner than the pick count suggests: five running backs are within a half point of vs-replacement, so if Bijan is gone the actual decision at 18 is closer to a coin flip than the ranked list alone shows.',
  'Your roster already has two starters at running back, so the marginal value of a third is lower than the raw vs-replacement number implies -- this is exactly the gap the vs your options column is meant to surface once it ships.',
  'Wide receiver depth behind the top tier is real this year: six players project within three points of each other, so passing at 18 on a name for a receiver later is a defensible plan if the board falls that way.',
  'None of this changes the recommendation at your current pick -- it only describes how the decision tree looks four picks from now, which is what you asked.',
  'If you want the same breakdown for a different position, ask and it will run the same way: retrieved from the board and the current draft state, never from outside knowledge.',
].join('\n\n');

await page.route('**/__reasoning', async (route) => {
  const body = JSON.parse(route.request().postData() ?? '{}');
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      status: 'ok',
      text: LONG_ANSWER,
      context_ids: (body.context ?? []).map((c) => c.id),
    }),
  });
});

await page.goto(url, { waitUntil: 'load' });
// A generous timeout: this sandbox's egress to fonts.googleapis.com is
// occasionally slow/reset, and the app's own board-data fetch queues behind
// it in some runs even though it is same-origin -- not a defect in the code
// under test, just this environment's network being flaky.
await page.waitForSelector('text=/generated 20/', { timeout: 60_000 });

// 1. Empty state: open the dock, nothing asked yet.
await page.getByText('Assistant', { exact: true }).click();
await page.waitForSelector('text=Nothing asked yet.');
await page.screenshot({ path: join(artifacts, 'fr077-followup-assistant-empty.png') });
console.log('captured: fr077-followup-assistant-empty.png');

// 2. Ask the mocked long-answer question, then screenshot the transcript at
//    both scroll extremes.
const input = page.getByPlaceholder('Ask about the board');
await input.fill('walk me through your thinking on my next pick');
await page.getByRole('button', { name: /ask/i }).click();
await page.waitForSelector('text=/Bijan is 4%/');

const answersEl = page.locator('.answers');
await answersEl.evaluate((el) => { el.scrollTop = 0; });
await page.screenshot({ path: join(artifacts, 'fr077-followup-assistant-scroll-top.png') });
console.log('captured: fr077-followup-assistant-scroll-top.png');

await answersEl.evaluate((el) => { el.scrollTop = el.scrollHeight; });
await page.screenshot({ path: join(artifacts, 'fr077-followup-assistant-scroll-bottom.png') });
console.log('captured: fr077-followup-assistant-scroll-bottom.png');

// Verify the header and input stayed put -- the pinned, non-scrolling parts.
const headerVisible = await page.getByText('Assistant', { exact: true }).isVisible();
const inputVisible = await page.getByPlaceholder('Ask a follow-up').isVisible();
if (!headerVisible || !inputVisible) {
  console.error('FAIL: header or input not visible after scrolling the transcript');
  process.exitCode = 1;
}

// 3. Collapse -- header pill only, conversation preserved underneath (not
//    visually provable from a screenshot alone; see the unit test for that).
await page.getByRole('button', { name: /collapse assistant/i }).click();
await page.waitForTimeout(150);
await page.screenshot({ path: join(artifacts, 'fr077-followup-assistant-collapsed.png') });
console.log('captured: fr077-followup-assistant-collapsed.png');

// 4. Reopen -- prove the conversation is still there, in the same screenshot
//    frame as the collapse, for a human reviewer to compare directly.
await page.getByText('Assistant', { exact: true }).click();
await page.waitForSelector('text=/Bijan is 4%/');
await page.screenshot({ path: join(artifacts, 'fr077-followup-assistant-reopened.png') });
console.log('captured: fr077-followup-assistant-reopened.png (conversation survived the collapse)');

// 5. The per-answer sources disclosure: closed by default, opened here, first
//    with the trace switch off (kind-only pills) then on (Alt+T -- the same
//    pills expand to the raw context key).
await page.getByRole('button', { name: /source/i }).first().click();
await page.screenshot({ path: join(artifacts, 'fr077-followup-assistant-sources-off.png') });
console.log('captured: fr077-followup-assistant-sources-off.png');

await page.keyboard.press('Alt+T');
await page.screenshot({ path: join(artifacts, 'fr077-followup-assistant-sources-trace-on.png') });
console.log('captured: fr077-followup-assistant-sources-trace-on.png');
await page.keyboard.press('Alt+T'); // leave trace mode off, matching this script's other captures

await browser.close();
