const fs=require('fs'),assert=require('assert'),{chromium}=require('C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const c=JSON.parse(fs.readFileSync('Saved/CombatAuthor/server.json','utf8'));const b=await chromium.launch({channel:'msedge',headless:true});const p=await b.newPage();
await p.goto(c.url);await p.locator('#versions').selectOption('CombatTool_Tuned_v1');await p.locator('#load').click();await p.locator('#message').filter({hasText:'불러왔습니다'}).waitFor();
let snap=await p.evaluate(async()=>await (await fetch('/api/state',{headers:{'X-Combat-Token':window.COMBAT_TOKEN}})).json());
if(!snap.versions.find(x=>x.id==='CombatTool_Tuned_v1').playable){
 await p.locator('#build').click();await p.locator('#message').filter({hasText:'작업 시작'}).waitFor();
 for(let i=0;i<240;i++){await new Promise(r=>setTimeout(r,1000));let j=await p.evaluate(async()=>await (await fetch('/api/state',{headers:{'X-Combat-Token':window.COMBAT_TOKEN}})).json());if(!j.job.running)break;}
}
let s=await p.evaluate(async()=>await (await fetch('/api/state',{headers:{'X-Combat-Token':window.COMBAT_TOKEN}})).json());assert(s.job.passed,JSON.stringify(s.job));assert(s.versions.find(x=>x.id==='CombatTool_Tuned_v1').playable);await b.close();console.log('PASS: authored tuning version built through UI',s.job.log);})().catch(e=>{console.error(e);process.exit(1)});
