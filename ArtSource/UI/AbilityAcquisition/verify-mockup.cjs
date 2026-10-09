const { chromium } = require('C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const path = require('path');
const fs = require('fs');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const url='file:///'+path.resolve(__dirname,'mockup.html').replaceAll('\\','/');
 for(const [name,query] of [['01-emblem','?capture&scene=intro'],['02-jump','?capture&ability=0'],['03-combat','?capture&ability=1'],['04-transform','?capture&ability=2'],['mural-alpha','?capture'],['mural-gamma','?capture&ability=2']]){
  await page.goto(url+query);await page.waitForFunction(()=>mural.complete&&mural.naturalWidth>0);await page.waitForTimeout(150);await page.locator('canvas').screenshot({path:path.join(__dirname,name+'.png')});
 }
 await page.goto(url);
 for(const st of ['d']){await page.locator('#style').selectOption(st);if(await page.evaluate(()=>style)!==st)throw Error('Style selector failed');}
 const drawn=await page.evaluate(()=>{const drawn=[];const original=ctx.fillText.bind(ctx);ctx.fillText=(s,...args)=>{drawn.push(s);original(s,...args)};reveal(7,0);ctx.fillText=original;return drawn});
 if(!drawn.includes('α CrB')||drawn.some(t=>t.includes('/ 07')||t.includes('북 쪽')))throw Error('Title cleanup failed');
 await page.locator('#sound').uncheck();await page.locator('#play').click();
 await page.keyboard.press('Space');await page.waitForTimeout(300);
 if(await page.evaluate(()=>mode)!=='play')throw Error('Early input dismissed animation');
 await page.waitForTimeout(6500);
 if(!(await page.locator('#status').textContent()).includes('아무 키'))throw Error('Await input prompt missing');
 await page.keyboard.press('Enter');await page.waitForTimeout(300);
 if(await page.evaluate(()=>mode)!=='exit')throw Error('Exit fade missing');
 await page.waitForTimeout(500);
 if(await page.evaluate(()=>mode)!=='returned')throw Error('Return missing');
 await page.locator('#ability').selectOption('2');
 if(await page.evaluate(()=>selected)!==2)throw Error('Selection failed');
 const mapping=await page.evaluate(()=>({slots:data.slots.length,lines:data.connection.length-1,titles:data.abilities.map(a=>a.title),mode}));
 if(mapping.slots!==7||mapping.lines!==6)throw Error('Topology invalid');
 await page.setViewportSize({width:390,height:844});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Narrow width overflow');
 await page.screenshot({path:path.join(__dirname,'review-mobile.png')});
 if(errors.length)throw Error(errors.join('\n'));
 const report={verifiedAt:new Date().toISOString(),checks:['6 full-HD scenes rendered','mural background loaded and style selected','CrB title and removed subtitle/counter verified','early input ignored','prompt appears after animation','exit fades then returns','ability selection works','7 slots and 6 links','390px no horizontal overflow','no browser JS errors'],mapping};
 fs.writeFileSync(path.join(__dirname,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
