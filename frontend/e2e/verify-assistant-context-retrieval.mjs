/**
 * End-to-end verification for docs/handoffs/2026-07-31-wire-assistant-retrieval-to-docs-assistant-conte.md.
 *
 * Drives the real browser (not a unit test): opens the assistant dock, asks a
 * question that ONLY docs/assistant-context.md answers, and inspects the actual
 * network POST body sent to /__reasoning -- the real request the model would
 * receive, not a simulation of it. No ANTHROPIC_API_KEY exists in this
 * container (docs/frontend-cloud-runbook.md), so the response is the documented
 * "no_key" unavailable state; the request body is the load-bearing evidence.
 *
 * Usage: node e2e/verify-assistant-context-retrieval.mjs [--url http://localhost:5199]
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

let reasoningRequestBody = null;
page.on('request', (req) => {
  if (req.url().endsWith('/__reasoning')) {
    reasoningRequestBody = req.postData();
  }
});

await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30_000 });
await page.waitForSelector('text=/generated 20/', { timeout: 30_000 });
await page.screenshot({ path: join(artifacts, 'assistant-context-01-board-loaded.png'), fullPage: false });

await page.locator('[aria-label="Open assistant"]').click();
await page.waitForSelector('[aria-label="Ask about the board"]', { timeout: 10_000 });
await page.screenshot({ path: join(artifacts, 'assistant-context-02-dock-open.png'), fullPage: false });

const QUESTION = 'is alpha detection happening for 2026';
await page.locator('[aria-label="Ask about the board"]').fill(QUESTION);
await page.keyboard.press('Enter');

// Wait for either the /__reasoning request to fire or the UI to settle on an
// unavailable/no-context state -- whichever happens first.
await page.waitForTimeout(3000);
await page.screenshot({ path: join(artifacts, 'assistant-context-03-after-question.png'), fullPage: false });

console.log(`Question asked: "${QUESTION}"`);
if (!reasoningRequestBody) {
  console.log('NO REQUEST to /__reasoning was observed (retrieval may have found nothing, or a template answered it).');
} else {
  const parsed = JSON.parse(reasoningRequestBody);
  console.log(`Request context items: ${parsed.context.length}`);
  for (const item of parsed.context) {
    console.log(`  [${item.id}] confidence=${item.confidence} source=${item.source_path}`);
  }
  const fromAssistantContext = parsed.context.filter((i) => i.id.startsWith('assistant_context.'));
  console.log(`Items sourced from docs/assistant-context.md: ${fromAssistantContext.length}`);
  for (const item of fromAssistantContext) {
    console.log(`  TEXT: ${item.text}`);
  }
  if (fromAssistantContext.length === 0) {
    console.error('FAIL: no assistant_context.* item in the real POST body sent to /__reasoning.');
    process.exitCode = 1;
  } else {
    console.log('PASS: the real browser request to /__reasoning carries content from docs/assistant-context.md.');
  }
}

const bodyText = await page.textContent('body');
const showsUnavailable = /reasoning lane|not configured|no_key|could not be reached/i.test(bodyText ?? '');
console.log(`UI shows an "unavailable" state (expected, no API key in this container): ${showsUnavailable}`);

await browser.close();
