const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({viewport:{width:1180,height:1400,deviceScaleFactor:2}});
  await p.goto('file://'+process.cwd()+'/index.html');
  await p.waitForTimeout(900);
  await p.locator('.studio').screenshot({path:'shot-front.png'});
  await p.locator('.viewtabs button[data-view="back"]').click();
  await p.waitForTimeout(350);
  await p.locator('.studio').screenshot({path:'shot-back.png'});
  await p.locator('.viewtabs button[data-view="front"]').click();
  await p.waitForTimeout(250);
  await p.locator('.stage.front .m--int[data-key="pecho"]').click();
  await p.waitForTimeout(250);
  await p.locator('.studio').screenshot({path:'shot-sel.png'});
  await p.screenshot({path:'shot-page.png', fullPage:false});
  await b.close();
  console.log('ok');
})();
