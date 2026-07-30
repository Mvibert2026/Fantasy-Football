import { chromium } from 'playwright';
const OUT = 'e2e/artifacts/design-2026-07-30';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const c = await b.newContext({ viewport: { width: 1600, height: 1000 } });
const p = await c.newPage();
const shot = async (name) => { await p.waitForTimeout(1200); await p.screenshot({ path: `${OUT}/${name}.png` }); console.log('shot', name); };
await p.goto('http://127.0.0.1:4321/', { waitUntil: 'networkidle', timeout: 60000 });
await p.waitForTimeout(3000);
await shot('01-prep-board');
for (const [label, name] of [['Draft', '02-draft-room'], ['Prep', '03-prep-back']]) {
  const t = p.getByRole('button', { name: label }).first();
  if (await t.count()) { await t.click().catch(() => {}); await shot(name); }
}
console.log('title:', await p.title());
await b.close();
