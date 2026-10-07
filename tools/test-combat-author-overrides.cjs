const fs=require('fs'),assert=require('assert'),{chromium}=require('C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const c=JSON.parse(fs.readFileSync('Saved/CombatAuthor/server.json','utf8'));const b=await chromium.launch({channel:'msedge',headless:true});const p=await b.newPage();
try{await p.goto(c.url);await p.locator('#versions').selectOption('CombatTool_v3');await p.locator('#clone').click();await p.getByRole('button',{name:'AI 파일 · JSON',exact:true}).click();
const area=p.getByLabel('전체 레시피 JSON');let d=JSON.parse(await area.inputValue());d.enemies=[{id:'Only',offset:[0,0,0],action_values:{Heavy:{damage:55}}}];await area.fill(JSON.stringify(d));await p.getByRole('button',{name:'JSON을 초안에 반영',exact:true}).click();await p.getByRole('button',{name:'적 배치 · 교전',exact:true}).click();
assert.equal(await p.getByLabel('피해량',{exact:true}).count(),1,'damage-only override must be visible');assert.equal(await p.getByLabel('피해량',{exact:true}).inputValue(),'55');
await p.getByRole('button',{name:'개별 설정 항목 확장',exact:true}).click();
await p.getByRole('button',{name:'AI 파일 · JSON',exact:true}).click();d=JSON.parse(await area.inputValue());assert.equal(d.enemies[0].action_values.Heavy.damage,55);
console.log('PASS: damage-only override visible and preserved when expanding settings');}finally{await b.close();}})().catch(e=>{console.error(e);process.exit(1)});
