import { chromium } from 'playwright';
const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p = await b.newPage({viewport:{width:1180,height:1400,deviceScaleFactor:2}});
await p.goto('file://'+process.cwd()+'/index.html');
await p.waitForTimeout(800);
// front full studio
await p.locator('.studio').screenshot({path:'shot-front.png'});
// switch to back
await p.locator('.viewtabs button[data-view="back"]').click();
await p.waitForTimeout(300);
await p.locator('.studio').screenshot({path:'shot-back.png'});
// select a muscle to test detail
await p.locator('.viewtabs button[data-view="front"]').click();
await p.waitForTimeout(200);
await p.locator('.stage.front .m--int[data-key="pecho"]').click();
await p.waitForTimeout(200);
await p.locator('.studio').screenshot({path:'shot-sel.png'});
await b.close();
console.log('ok');
