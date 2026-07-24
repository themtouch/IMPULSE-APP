const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({viewport:{width:1180,height:900,deviceScaleFactor:2}});
  await p.goto('file://'+process.cwd()+'/index.html');
  await p.waitForTimeout(900);
  // select muscle in the studio stage specifically (not the phone clone)
  await p.locator('.studio .stage.front .m--int[data-key="pecho"]').click();
  await p.waitForTimeout(250);
  await p.locator('.studio').screenshot({path:'shot-sel.png'});
  // phones 01-04
  const rail = p.locator('#rail');
  const box = await rail.boundingBox();
  await p.screenshot({path:'shot-rail1.png', clip:{x:0,y:box.y-10,width:1180,height:560}});
  // scroll rail right to see phones 05-08
  await rail.evaluate(el=>el.scrollLeft = el.scrollWidth);
  await p.waitForTimeout(400);
  await p.screenshot({path:'shot-rail2.png', clip:{x:0,y:box.y-10,width:1180,height:560}});
  await b.close(); console.log('ok');
})();
