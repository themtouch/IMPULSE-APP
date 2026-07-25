const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport:{width:440,height:900}, deviceScaleFactor:2 });
  const page = await ctx.newPage();
  const errors=[];
  page.on('console', m=>{ if(m.type()==='error') errors.push('CONSOLE: '+m.text()); });
  page.on('pageerror', e=>errors.push('PAGEERROR: '+e.message));
  const url='file://'+path.join(__dirname,'app.html');
  await page.goto(url);
  const D=path.join(__dirname);

  // ---- onboarding ----
  await page.click('#onb [data-step="0"] [data-next]');        // start
  await page.fill('#in-name','Enzo');
  await page.click('#onb [data-step="1"] [data-next]');        // name
  await page.fill('#in-age','27');
  await page.click('#onb [data-step="2"] [data-next]');        // about
  await page.click('#in-exp button[data-v="1-3"]');
  await page.click('#onb [data-step="3"] [data-next]');        // exp
  await page.click('#in-goal button[data-v="Hipertrofia"]');
  await page.click('#onb [data-done]');                        // done -> fisico
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(D,'t-fisico.png') });

  // count painted muscles
  const painted = await page.$$eval('.stage.front .m--int', els=>els.filter(e=>e.style.background&&e.style.background!=='').length);
  console.log('painted front muscles:', painted);

  // ---- inicio ----
  await page.click('.nav button[data-go="inicio"]');
  await page.waitForTimeout(200);
  await page.screenshot({ path: path.join(D,'t-inicio.png') });
  const hello = await page.textContent('#hello');
  console.log('hello:', hello);

  // ---- start session from recommended ----
  await page.click('#start-next');
  await page.waitForTimeout(300);
  // fill sets for each exercise (heavy volume to trigger rank-up)
  const inputs = await page.$$('#sess-body .setrow input');
  console.log('set inputs found:', inputs.length);
  // add several heavy sets to first exercise to force rank up
  for(let k=0;k<6;k++){ await page.click('#sess-body .card:first-child .addset'); }
  const first = await page.$$('#sess-body .card:first-child .setrow input');
  for(let i=0;i<first.length;i+=2){ await first[i].fill('120'); await first[i+1].fill('12'); }
  await page.screenshot({ path: path.join(D,'t-session.png') });
  await page.click('#sess-finish');
  await page.waitForTimeout(500);
  const cel = await page.isVisible('#celebrate.on');
  console.log('celebration shown:', cel);
  await page.screenshot({ path: path.join(D,'t-celebrate.png') });
  if(cel) await page.click('#cel-claim');
  await page.waitForTimeout(300);

  // ---- verify session persisted ----
  const data = await page.evaluate(()=>JSON.parse(localStorage.getItem('impulse.v1')));
  console.log('sessions saved:', data.sessions.length, '| exercises in s1:', data.sessions[0].exercises.length);

  // ---- biblioteca search ----
  await page.click('.nav button[data-go="biblioteca"]');
  await page.fill('#search','curl');
  await page.waitForTimeout(200);
  const libRows = await page.$$eval('#lib .row', r=>r.length);
  console.log('biblioteca "curl" results:', libRows);
  await page.screenshot({ path: path.join(D,'t-biblioteca.png') });

  // ---- perfil + paywall ----
  await page.click('.nav button[data-go="perfil"]');
  await page.waitForTimeout(150);
  await page.screenshot({ path: path.join(D,'t-perfil.png') });
  await page.click('#open-paywall');
  await page.waitForTimeout(200);
  await page.screenshot({ path: path.join(D,'t-paywall.png') });

  console.log('ERRORS:', errors.length? errors.join('\n'):'none');
  await browser.close();
})();
