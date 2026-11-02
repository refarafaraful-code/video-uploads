const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await (await b.newContext({ locale: 'en-US' })).newPage();
  const json = [];
  p.on('response', async r => { if ((r.headers()['content-type'] || '').includes('json')) { try { json.push({ u: r.url(), d: await r.json() }); } catch (e) {} } });
  await p.goto(url, { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
  for (let i = 0; i < 4; i++) { await p.mouse.wheel(0, 2500); await p.waitForTimeout(1500); }
  const text = await p.evaluate(() => document.body.innerText);
  const links = await p.evaluate(() => [...document.querySelectorAll('a')].map(a => a.href).filter(h => /tiktok|instagram|youtube/.test(h)));
  fs.writeFileSync(out, JSON.stringify({ text, links, json }));
  console.log('text', text.length, 'links', links.length, 'json', json.length);
  await b.close();
})();
