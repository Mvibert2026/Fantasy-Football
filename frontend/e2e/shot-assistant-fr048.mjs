import { chromium } from 'playwright';

const url = process.argv[2] ?? 'http://localhost:5199';
const outDir = process.argv[3] ?? 'e2e/artifacts';

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

page.on('console', (msg) => {
  if (msg.type() === 'error') console.log('CONSOLE ERROR:', msg.text());
});

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);

// The floating pill, bottom-right (last "Assistant" text match, not the sidebar link).
const pill = page.locator('text=Assistant').last();
await pill.click();
await page.waitForTimeout(400);
await page.screenshot({ path: `${outDir}/fr048-01-dock-open.png`, fullPage: false });

const input = page.locator('input[aria-label="Ask about the board"]');
await input.waitFor({ timeout: 10000 });

// A template question -- deterministic, no network, proves the dock still works
// end-to-end after the Dataset/types.ts/load.ts changes this session made.
await input.fill('what is VBD');
await input.press('Enter');
await page.waitForTimeout(600);
await page.screenshot({ path: `${outDir}/fr048-02-template-answer.png`, fullPage: false });

// A free-text question that only the reasoning lane (built on ./retrieval.ts this
// session) can route to. This container has no ANTHROPIC_API_KEY (documented gap,
// frontend-cloud-runbook.md), so the network call to /__reasoning fails and the UI
// should show the "offline" notice defined in reasoning.ts, not a crash -- proving
// the integration point (retrieveContext -> fetch -> graceful unavailable state)
// still wires up correctly even though the LLM call itself can't be exercised here.
await input.fill('when should I take a tight end');
await input.press('Enter');
await page.waitForTimeout(2000);
await page.screenshot({ path: `${outDir}/fr048-03-reasoning-lane-offline.png`, fullPage: false });

console.log('Screenshots written to', outDir);
await browser.close();
