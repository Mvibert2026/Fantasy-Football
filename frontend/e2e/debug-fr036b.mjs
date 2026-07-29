import { chromium } from 'playwright';
const EXEC = '/opt/pw-browsers/chromium';
const browser = await chromium.launch({ executablePath: EXEC });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5199', { waitUntil: 'load', timeout: 15000 });
await page.waitForTimeout(1000);

async function dumpOptions(label) {
  const opts = await page.evaluate(() => {
    const sel = document.querySelector('select[aria-label="Select league"]');
    return Array.from(sel.options).map((o) => ({ value: o.value, text: o.textContent }));
  });
  console.log(label, JSON.stringify(opts.filter((o) => o.value === 'default' || o.value === 'ethans_expert_league')));
}

await dumpOptions('initial:');

const select = page.locator('select[aria-label="Select league"]');
await select.selectOption('ethans_expert_league');
await page.waitForTimeout(2000);
await dumpOptions('after selecting ethans_expert_league:');

await select.selectOption('default');
await page.waitForTimeout(2000);
await dumpOptions('after selecting back to default:');

await select.selectOption('ethans_expert_league');
await page.waitForTimeout(2000);
await dumpOptions('after selecting ethans_expert_league again:');

await browser.close();
