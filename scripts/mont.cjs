const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch();
 const p=await b.newPage({viewport:{width:1180,height:560,deviceScaleFactor:2}});
 const imgs=[1,2,3,4].map(i=>`<img src="phone-${i}.png" style="height:500px">`).join('');
 await p.setContent(`<body style="margin:0;background:#000;display:flex;gap:14px;padding:14px;align-items:center">${imgs}</body>`);
 await p.waitForTimeout(300);await p.screenshot({path:'row1.png'});
 const imgs2=[5,6,7,8].map(i=>`<img src="phone-${i}.png" style="height:500px">`).join('');
 await p.setContent(`<body style="margin:0;background:#000;display:flex;gap:14px;padding:14px;align-items:center">${imgs2}</body>`);
 await p.waitForTimeout(300);await p.screenshot({path:'row2.png'});
 await b.close();console.log('rows ok');
})();
