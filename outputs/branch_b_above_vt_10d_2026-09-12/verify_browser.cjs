const {chromium} = require('/Users/dgrissen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const assert = require('node:assert/strict');
const path = __dirname;
(async()=>{
  const browser = await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--no-sandbox']});
  try {
    const page = await browser.newPage({viewport:{width:1700,height:1220},deviceScaleFactor:1});
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    const checks=[];
    const ready=()=>page.waitForFunction(()=>window.carouselReady);
    const options=()=>page.locator('#date-select option').evaluateAll(xs=>xs.map(x=>x.value));
    async function checkDates(expected, label){
      await ready();
      assert.deepEqual(await options(),Object.keys(expected),label);
      for(const [date,times] of Object.entries(expected)){
        await page.selectOption('#date-select',date); await ready();
        const snapshot=await page.evaluate(()=>{
          const chart=document.querySelector('#chart');
          return {candles:chart.data[0].x.length,title:chart.layout.title.text,
            times:chart.data.filter(t=>t.name.endsWith(' entry')).flatMap(t=>t.x).sort(),
            rows:document.querySelectorAll('#entry-table tr').length};
        });
        assert.equal(snapshot.candles,78);
        assert.ok(snapshot.title.includes(date));
        assert.deepEqual(snapshot.times,times);
        assert.equal(snapshot.rows,times.length);
        checks.push({filter:label,date,...snapshot});
      }
    }
    await page.goto(`file://${path}/branch_b_carousel.html`);
    await ready();
    assert.equal(await page.locator('#mode-select').inputValue(),'staircase');
    for(const [button,title] of [['info-thrust','Thrust —'],['info-staircase','Staircase —'],['info-mode','Staircase —']]){
      const before=await page.locator('#date-select').inputValue();
      await page.click(`#${button}`);
      assert.ok(await page.locator('#entry-info').isVisible());
      assert.ok((await page.locator('#info-title').textContent()).startsWith(title));
      assert.ok((await page.locator('#info-body').textContent()).includes('Shared trend requirements'));
      await page.keyboard.press('ArrowRight');
      assert.equal(await page.locator('#date-select').inputValue(),before,'Modal must not navigate charts');
      await page.keyboard.press('Escape');
      assert.ok(await page.locator('#entry-info').isHidden());
    }
    await page.click('#info-thrust');
    await page.screenshot({path:`${path}/entry_info_preview.png`});
    await page.click('#info-close');
    await checkDates({'2026-08-27':['12:40'],'2026-08-28':['10:45','10:55'],
      '2026-09-03':['11:05','11:15','13:40']},'combined');
    await page.screenshot({path:`${path}/integrated_preview.png`});
    await page.click('#next'); await ready();
    assert.equal(await page.locator('#date-select').inputValue(),'2026-08-27');
    await page.click('#prev'); await ready();
    assert.equal(await page.locator('#date-select').inputValue(),'2026-09-03');
    await page.selectOption('#mode-select','thrust'); await ready();
    assert.equal(await page.locator('#date-select').inputValue(),'2026-09-03','Keep matching date');
    await checkDates({'2026-08-28':['10:45'],'2026-09-03':['11:05','11:30']},'thrust-only');
    await page.screenshot({path:`${path}/thrust_preview.png`});
    await page.selectOption('#mode-select','staircase'); await ready();
    await page.uncheck('#show-staircase');
    await checkDates({'2026-08-28':['10:45'],'2026-09-03':['11:05']},'combined/thrust type');
    await page.check('#show-staircase'); await ready();
    await page.uncheck('#show-thrust');
    await checkDates({'2026-08-27':['12:40'],'2026-08-28':['10:55'],
      '2026-09-03':['11:15','13:40']},'combined/staircase type');
    await page.screenshot({path:`${path}/staircase_preview.png`});
    await page.check('#show-raw'); await ready();
    assert.equal(await page.locator('#date-select option').count(),3,'Diagnostic cannot add dates');
    await page.uncheck('#show-staircase'); await ready();
    assert.deepEqual(await options(),[]);
    assert.ok(await page.locator('#empty-state').isVisible());
    assert.ok(await page.locator('#chart-panel').isHidden());
    assert.ok(await page.locator('#entry-panel').isHidden());
    assert.ok(await page.locator('#prev').isDisabled());
    assert.ok(await page.locator('#next').isDisabled());
    assert.equal(await page.locator('#counter').textContent(),'0 / 0');
    await page.keyboard.press('ArrowRight'); await ready();
    await page.check('#show-staircase'); await ready();
    assert.equal(await page.locator('#date-select').inputValue(),'2026-08-27');
    await page.selectOption('#mode-select','thrust'); await ready();
    assert.equal(await page.locator('#date-select').inputValue(),'2026-08-28','Skip ineligible date on mode change');
    for(const [control,traceName] of [['show-ema','EMA20 · jaw'],['show-vt','Vol Trigger']]){
      await page.uncheck(`#${control}`); await ready();
      assert.ok(await page.evaluate(name=>!document.querySelector('#chart').data.some(t=>t.name===name),traceName));
      await page.check(`#${control}`); await ready();
    }
    await page.uncheck('#show-labels'); await ready();
    assert.ok(await page.evaluate(()=>document.querySelector('#chart').data.filter(t=>t.name.endsWith(' entry')).every(t=>t.mode==='markers')));
    await page.keyboard.press('ArrowRight'); await ready();
    assert.equal(await page.locator('#date-select').inputValue(),'2026-09-03');
    for(const mode of ['thrust','staircase']){
      await page.goto(`file://${path}/${mode}_carousel.html#2026-09-03`); await ready();
      assert.ok(page.url().includes('branch_b_carousel.html#mode='+mode));
      assert.equal(await page.locator('#mode-select').inputValue(),mode);
      assert.equal(await page.locator('#date-select').inputValue(),'2026-09-03');
    }
    assert.deepEqual(errors,[]);
    const result={errors,checks,entry_info:'passed',mode_and_type_filters:'passed',empty_state:'passed',navigation:'passed',legacy_redirects:'passed'};
    fs.writeFileSync(`${path}/browser_checks.json`,JSON.stringify(result,null,2));
    console.log(JSON.stringify({checkedFilteredCharts:checks.length,errors,filters:'passed',navigation:'passed',empty_state:'passed',redirects:'passed'}));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
