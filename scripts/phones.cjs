const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({viewport:{width:1180,height:900,deviceScaleFactor:2}});
  await p.goto('file://'+process.cwd()+'/index.html');
  await p.waitForTimeout(900);
  const phones = p.locator('.phone');
  const n = await phones.count();
  // stitch: screenshot phones 1-4 and 5-8 by scrolling each into view
  for (const idx of [0,1,2,3,4,5,6,7]) {
    await phones.nth(idx).scrollIntoViewIfNeeded();
    await p.waitForTimeout(150);
    await phones.nth(idx).screenshot({path:`phone-${idx+1}.png`});
  }
  await b.close(); console.log('phones:'+n);
})();
