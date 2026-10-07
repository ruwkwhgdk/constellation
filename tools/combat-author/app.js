const $=s=>document.querySelector(s), copy=o=>JSON.parse(JSON.stringify(o));
let doc=null,baseline=null,section="overview",history=[],future=[],schema={},state={};
const labels={enabled:"이펙트 표시",mode:"효과 방식",kind:"갤러리 효과 종류",system:"Niagara 자산",scale:"효과 크기 배율",duration:"최대 유지 시간 (초)",battle_key:"장면 이벤트 전투 키",notify_scene:"전투 종료를 장면 이벤트에 전달",id:"이름 / ID",source:"복제할 원본 액션",montage:"애니메이션 몽타주",next_action:"다음 콤보",damage:"피해량",stamina_cost:"SP 비용",cooldown:"쿨다운 (초)",play_rate:"애니메이션 배속",reach:"전방 판정 거리 (cm)",radius:"판정 반경 (cm)",ultimate_cost:"궁극기 게이지 비용",ultimate_gain:"적중 시 게이지 획득",dash_distance:"돌진 거리 (cm)",dash_duration:"돌진 시간 (초)",radial_hit:"주변 구형 범위 판정",allow_dodge_cancel:"공격 중 회피 전환",input_window_start:"선입력 시작 (몽타주 초)",input_window_end:"선입력 종료 (몽타주 초)",dodge_cancel_start:"회피 전환 시작 (몽타주 초)",dodge_cancel_end:"회피 전환 종료 (몽타주 초)",max_health:"최대 HP",max_stamina:"최대 SP",stamina_recovery_per_second:"SP 초당 회복량",stamina_recovery_delay:"SP 회복 대기 (초)",hit_reaction_duration:"피격 경직 (초)",dodge_duration:"회피 시간 (초)",dodge_distance:"회피 거리 (cm)",dodge_stamina_cost:"회피 SP 비용",dodge_invulnerable_start:"무적 시작 (초)",dodge_invulnerable_end:"무적 종료 (초)",detect_radius:"적 감지 거리",lose_radius:"추적 중단 거리",leash_radius:"활동 반경",attack_distance:"공격 접근 거리",move_speed:"이동 속도",think_interval:"AI 판단 간격",lost_sight_time:"시야 상실 유예",home_tolerance:"복귀 완료 거리",retry_delay:"이동 재시도 대기",retry_cooldown:"재교전 대기",stuck_timeout:"이동 막힘 판정 시간",max_move_failures:"이동 실패 허용 횟수",restore_on_return:"복귀 시 자원 회복",min_distance:"최소 거리",max_distance:"최대 거리",max_angle:"최대 각도",require_sight:"시야 필요",weight:"선택 가중치",max_consecutive:"연속 제한 (0=무제한)",action:"사용 액션",basic:"좌클릭 기본 공격",skill:"Q 스킬",ultimate:"E 궁극기",start:"타격 시작 (몽타주 초)",end:"타격 종료 (몽타주 초)",max_attackers:"동시 공격 가능한 적 수",mesh:"몬스터 메시"};
const sections=[["overview","전체 구성","새 버전 이름을 정한 뒤 항목별로 수정하고 아래 순서로 검증·제작하세요."],["player","플레이어 · 슬롯","기본 콤보와 Q/E 액션을 연결합니다."],["playerActions","플레이어 액션","애니메이션을 재사용하여 새 전투 액션을 만듭니다."],["monster","몬스터 · 능력치","슬라임 기본 능력치와 공격 액션입니다."],["patterns","AI 공격 패턴","거리·각도·가중치 조건으로 액션을 선택합니다."],["encounter","추적 · 복귀","감지, 이동, 추적 포기와 재교전 설정입니다."],["placements","적 배치 · 교전","템플릿 적 위치 기준 cm 단위 상대 위치입니다."],["vfx","공격 · 피격 이펙트","공격은 타격 구간에서, 피격은 실제 피해가 확정됐을 때 표시합니다."],["changes","변경 내역","열었던 버전과 현재 초안의 차이입니다."],["json","AI 파일 · JSON","AI가 만든 전체 레시피를 붙여 넣거나 파일로 불러옵니다."]];
async function api(path,body){let r=await fetch(path,{method:body===undefined?"GET":"POST",headers:{"X-Combat-Token":window.COMBAT_TOKEN,"Content-Type":"application/json"},body:body===undefined?undefined:JSON.stringify(body)});let d=await r.json();if(!r.ok)throw Error(d.error||r.status);return d;}
function navigateError(text){
 const key=text.split(":")[0];
 section=key.startsWith("player.actions")?"playerActions":key.startsWith("player")?"player":key.startsWith("actions")?"monster":key.startsWith("patterns")?"patterns":key.startsWith("encounter")?"encounter":key.startsWith("enemies")?"placements":"overview";
 $("#search").value="";render();
 const field=key.split(".").pop();const label=[...$("#content").querySelectorAll("label")].find(n=>n.querySelector("small")?.textContent===field);
 if(label){label.scrollIntoView({block:"center"});label.querySelector("input,select")?.focus();}
}
function message(s,error=false){$("#message").style.display="block";$("#message").className=error?"error":"";$("#message").textContent=s;if(error)$("#message").append(button("해당 항목으로 이동",()=>navigateError(s)));}
function attempt(fn){return async()=>{try{await fn();}catch(e){message(e.message,true);}};}
function change(fn){history.push(copy(doc));if(history.length>100)history.shift();future=[];fn();render();}
function edit(fn){history.push(copy(doc));if(history.length>100)history.shift();future=[];fn();$("#undo").disabled=false;$("#redo").disabled=true;}
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function button(text,fn){const b=el("button",text);b.onclick=attempt(fn);return b;}
function card(title,parent=$("#content")){const c=el("section",undefined,"card");if(title)c.append(el("h3",title));parent.append(c);return c;}
function fields(obj,parent,opts={}){const grid=el("div",undefined,"fields");parent.append(grid);Object.entries(obj).forEach(([key,value])=>{if(value!==null&&typeof value==="object")return;if(opts.skip?.includes(key))return;const lab=el("label",labels[key]||key,"field");let input;if(opts.options?.[key]){input=el("select");for(const item of opts.options[key]){const o=el("option",item||"미지정");o.value=item;input.append(o);}input.value=value??"";}else{input=el("input");input.type=typeof value==="boolean"?"checkbox":typeof value==="number"?"number":"text";if(input.type==="checkbox")input.checked=value;else input.value=value??"";if(input.type==="number")input.step="any";}input.setAttribute("aria-label",labels[key]||key);if(key==="system")input.setAttribute("list","niagaraAssets");if(key==="source" || key==="montage")input.setAttribute("list",key==="source"?"actionAssets":"montageAssets");input.onchange=()=>edit(()=>{obj[key]=input.type==="checkbox"?input.checked:typeof value==="number"?Number(input.value):(key==="battle_key"?input.value:input.value||null);opts.onEdit?.(key,obj[key]);});lab.append(input,el("small",key));grid.append(lab);});}
function numericEditor(obj,allowed,parent){fields(obj,parent);const available=Object.keys(allowed).filter(k=>!(k in obj));if(!available.length)return;const row=el("div",undefined,"addline"),select=el("select");available.forEach(k=>{const o=el("option",labels[k]||k);o.value=k;select.append(o);});row.append(select,button("설정 추가",()=>change(()=>obj[select.value]=typeof allowed[select.value]==="boolean"?false:Array.isArray(allowed[select.value])?allowed[select.value][0]:allowed[select.value])));parent.append(row);}
function upgrade(){if(doc.schema_version===1)doc.schema_version=2;doc.monster_stats??={};doc.enemies??=[{id:"Enemy1",offset:[0,0,0]}];doc.max_attackers??=1;}
function expandOverrides(a){
 a.stats={...copy(doc.monster_stats),...a.stats};a.encounter_values={...copy(doc.encounter),...a.encounter_values};
 a.action_values=Object.fromEntries(doc.actions.map(x=>[x.id,{...copy(x.values),...a.action_values?.[x.id]}]));
 a.pattern_values=Object.fromEntries(doc.patterns.map(x=>[x.id,{...Object.fromEntries(Object.entries(x).filter(([k])=>k!=="id"&&k!=="action")),...a.pattern_values?.[x.id]}]));
}
function actions(rows,parent){rows.forEach((a,i)=>{const c=card(a.id,parent);fields(a,c,{options:{next_action:["",...rows.map(x=>x.id)]}});if(!("next_action"in a))c.append(button("콤보 연결 추가",()=>change(()=>a.next_action=null)));if(!("montage"in a))c.append(button("몽타주 직접 지정",()=>change(()=>a.montage="")));numericEditor(a.values,{...schema.actions,...Object.fromEntries(schema.booleans.map(k=>[k,false]))},c);if(a.hit_windows){a.hit_windows.forEach((w,j)=>{const sub=card("타격 구간 "+(j+1),c);fields(w,sub);sub.append(button("구간 삭제",()=>change(()=>{a.hit_windows.splice(j,1);if(!a.hit_windows.length)delete a.hit_windows;})));});}const row=el("div",undefined,"addline");row.append(button("타격 구간 추가",()=>change(()=>{a.hit_windows??=[];a.hit_windows.push({id:"Hit"+(a.hit_windows.length+1),start:.2,end:.4});})),button("이 액션 복제",()=>change(()=>{let n=copy(a);n.id=a.id+"_Copy";rows.push(n);})),button("액션 삭제",()=>change(()=>rows.splice(i,1))));c.append(row);});parent.append(button("새 액션 추가",()=>change(()=>rows.push({id:"NewAction",source:rows[0]?.source||"/Game/Constellation/Review/CombatCore/DA_PlayerSlash",values:{}}))));}
function differences(a,b,path="",out=[]){if(JSON.stringify(a)===JSON.stringify(b))return out;if(a&&b&&typeof a==="object"&&typeof b==="object"){for(const k of new Set([...Object.keys(a),...Object.keys(b)]))differences(a[k],b[k],path?path+"."+k:k,out);}else out.push([path,JSON.stringify(a)??"없음",JSON.stringify(b)??"없음"]);return out;}
function effectEditor(owner,key,title,inherited){
 const c=card(title),v=owner[key];
 if(!v){c.append(el("p",inherited?"몬스터 공통 이펙트를 사용합니다.":"갤러리 기본 효과를 사용합니다. 검 궤적, 슬라임 공격과 대상별 피격 효과가 자동 연결됩니다.","note"),button("이 대상의 이펙트 설정",()=>change(()=>owner[key]=copy(inherited||{enabled:true,attack:schema.vfxCue,hit:schema.vfxCue}))));return;}
 fields({enabled:v.enabled??inherited?.enabled??true},c,{onEdit:(k,x)=>v[k]=x});for(const slot of ["attack","hit"]){
  const sub=card(slot==="attack"?"공격 시":"피격 시",c);
  if(!v[slot]){sub.append(button("효과 설정 추가",()=>change(()=>v[slot]=copy({...schema.vfxCue,...inherited?.[slot]}))));continue;}
  const cue={...copy(schema.vfxCue),...copy(inherited?.[slot]||{}),...copy(v[slot])};fields(cue,sub,{onEdit:(k,x)=>v[slot][k]=x,options:{mode:["Default","Disabled","Builtin","Niagara"],kind:schema.vfxKinds}});
  if(!cue.color)sub.append(button("색상 지정",()=>change(()=>cue.color=[1,1,1,1])));
  else{const row=el("div",undefined,"fields");["R","G","B","A"].forEach((k,i)=>{let l=el("label","색 "+k),n=el("input");n.type="number";n.step="0.05";n.value=cue.color[i];n.setAttribute("aria-label",title+" "+slot+" "+k);n.onchange=()=>edit(()=>{cue.color[i]=Number(n.value);v[slot].color=copy(cue.color);});l.append(n);row.append(l);});sub.append(row);}
 }
 c.append(el("p","Default: 기존 효과 · Disabled: 끄기 · Builtin: 갤러리 종류 · Niagara: 지정 자산. 색·크기는 Builtin/Niagara에 적용됩니다. Niagara는 User.Color / User.Scale 파라미터를 사용할 수 있습니다.","note"),button("상속 / 기본 효과로 복원",()=>change(()=>delete owner[key])));
}
function render(){
 $("#content").replaceChildren();$("#nav").replaceChildren();sections.forEach(([id,title])=>{const b=button(title,()=>{section=id;$("#search").value="";render();});b.className=id===section?"active":"";$("#nav").append(b);});const info=sections.find(s=>s[0]===section);$("#title").textContent=info[1];$("#subtitle").textContent=info[2];$("#undo").disabled=!history.length;$("#redo").disabled=!future.length;
 if(!doc){card("왼쪽에서 전투 버전을 선택하세요.");return;}$("#versionName").value=doc.id;
 if(section==="overview"){let c=card("현재 구성");c.append(el("p","몬스터 액션 "+doc.actions.length+"개 · 패턴 "+doc.patterns.length+"개 · 플레이어 액션 "+(doc.player?.actions.length||0)+"개 · 적 "+(doc.enemies?.length||1)+"마리"));c.append(el("p","권장: CombatTool 버전을 복제하면 기본 콤보·돌진 스킬·범위 궁극기를 바로 조정할 수 있습니다.","hint"));fields(doc,c,{skip:["schema_version","id"]});}
 if(section==="player"){if(!doc.player){card("플레이어 구성이 있는 CombatTool 샘플을 복제하세요.");}else{fields(doc.player.slots,card("슬롯 연결"),{options:Object.fromEntries(["basic","skill","ultimate"].map(k=>[k,["",...doc.player.actions.map(a=>a.id)]]))});numericEditor(doc.player.stats,schema.stats,card("능력치 · 회피"));fields(doc.player,card("이동"),{skip:[]});}}
 if(section==="playerActions"){if(doc.player)actions(doc.player.actions,$("#content"));else card("플레이어 구성이 있는 샘플을 복제하세요.");}
 if(section==="monster"){if(doc.schema_version===1)$("#content").append(button("능력치 편집을 위해 v2로 전환",()=>change(upgrade)));else numericEditor(doc.monster_stats,schema.stats,card("몬스터 능력치"));actions(doc.actions,$("#content"));}
 if(section==="patterns"){doc.patterns.forEach((p,i)=>{let c=card(p.id);fields(p,c,{options:{action:doc.actions.map(a=>a.id)}});c.append(button("패턴 삭제",()=>change(()=>doc.patterns.splice(i,1))));});$("#content").append(button("패턴 추가",()=>change(()=>doc.patterns.push({id:"Pattern"+(doc.patterns.length+1),action:doc.actions[0]?.id,...schema.patterns}))));}
 if(section==="encounter")fields(doc.encounter,card("몬스터 AI"));
 if(section==="placements"){if(doc.schema_version===1)$("#content").append(button("배치 편집을 위해 v2로 전환",()=>change(upgrade)));else{fields(doc,card("교전"),{skip:["id","schema_version","mesh"]});doc.enemies.forEach((a,i)=>{let c=card(a.id);fields(a,c);const g=el("div",undefined,"fields");["X","Y","Z"].forEach((k,j)=>{let l=el("label",k+" (cm)"),n=el("input");n.type="number";n.value=a.offset[j];n.onchange=()=>edit(()=>a.offset[j]=Number(n.value));l.append(n);g.append(l);});c.append(g,button("적 삭제",()=>change(()=>doc.enemies.splice(i,1))));
 if(["stats","action_values","pattern_values","encounter_values"].some(k=>k in a)){if(a.stats)numericEditor(a.stats,schema.stats,card("이 적의 능력치",c));for(const [name,values] of Object.entries(a.action_values||{}))numericEditor(values,{...schema.actions,...Object.fromEntries(schema.booleans.map(k=>[k,false]))},card("이 적의 공격 · "+name,c));
 if(a.encounter_values)fields(a.encounter_values,card("이 적의 추적 · 복귀",c));
 for(const [name,values] of Object.entries(a.pattern_values||{}))fields(values,card("이 적의 패턴 · "+name,c));
 c.append(button("공통 설정으로 되돌리기",()=>change(()=>{delete a.stats;delete a.action_values;delete a.pattern_values;delete a.encounter_values;})));
 }c.append(button("개별 설정 항목 확장",()=>change(()=>expandOverrides(a))));});$("#content").append(button("적 추가",()=>change(()=>doc.enemies.push({id:"Enemy"+(doc.enemies.length+1),offset:[0,doc.enemies.length*180,0]}))));}}
 if(section==="vfx"){if(doc.schema_version===1)$("#content").append(button("이펙트 편집을 위해 v2로 전환",()=>change(upgrade)));else{if(doc.player)effectEditor(doc.player,"vfx","플레이어");effectEditor(doc,"monster_vfx","몬스터 공통");doc.enemies.forEach(a=>effectEditor(a,"vfx","몬스터 · "+a.id,doc.monster_vfx||{enabled:true,attack:schema.vfxCue,hit:schema.vfxCue}));}}
 if(section==="changes"){const rows=differences(baseline,doc);const c=card("변경 "+rows.length+"건"),t=el("table");let tr=el("tr");["항목","이전","초안"].forEach(x=>tr.append(el("th",x)));t.append(tr);rows.forEach(r=>{let tr=el("tr");r.forEach(v=>tr.append(el("td",v)));t.append(tr);});c.append(t);}
 if(section==="json"){
 const bridge=card("플레이 조정값 → 새 버전");
 bridge.append(el("p","F1 → AI 전달 파일로 내보낸 값을 불러옵니다. 제작 원본이 일치하는 보고서만 허용됩니다.","note"));
 const reports=el("select");reports.setAttribute("aria-label","플레이 조정 보고서");(state.reports||[]).forEach(name=>{const o=el("option",name);o.value=name;reports.append(o);});
 bridge.append(reports,button("플레이 조정값 불러오기",async()=>{
  if(!baseline)throw Error("먼저 제작된 원본 버전을 여세요.");
  const r=await api("/api/import-report",{base_id:baseline.id,new_id:doc.id===baseline.id?doc.id+"_Tuned":doc.id,report:reports.value});
  change(()=>doc=r.draft);message("조정값 "+r.changes.length+"건을 새 초안에 반영했습니다. 변경 내역 확인 후 저장하세요.");
 }));
 const c=card("전체 레시피");const area=el("textarea");area.value=JSON.stringify(doc,null,2);area.setAttribute("aria-label","전체 레시피 JSON");c.append(area,button("JSON을 초안에 반영",async()=>{let d=JSON.parse(area.value);const checked=await api("/api/validate",d);change(()=>doc=checked.draft);}));let file=el("input");file.type="file";file.accept=".json";file.onchange=attempt(async()=>{let d=JSON.parse(await file.files[0].text());const checked=await api("/api/validate",d);change(()=>doc=checked.draft);});c.append(file);}
 filter();
}
function filter(){const q=$("#search").value.toLowerCase();$("#content").querySelectorAll(":scope > .card").forEach(c=>{
 const visibleText=[...c.querySelectorAll("h3,label")].map(n=>[...n.childNodes].filter(x=>x.nodeType===3).map(x=>x.textContent).join(" ")).join(" ").toLowerCase();
 c.hidden=!!q&&!visibleText.includes(q)&&![...c.querySelectorAll("input")].some(n=>n.value.toLowerCase().includes(q));
});}
async function refresh(){state=await api("/api/state");const chosen=$("#versions").value;$("#versions").replaceChildren();state.versions.forEach(v=>{let o=el("option",v.id+(v.playable?" · 플레이 가능":" · JSON"));o.value=v.file;$("#versions").append(o);});if([...$("#versions").options].some(o=>o.value===chosen))$("#versions").value=chosen;const j=state.job;$("#status").textContent=j.running?j.id+" · "+j.mode+" 진행 중":j.message?j.id+" · "+j.message:"준비";["preview","build","play"].forEach(k=>$("#"+k).disabled=!!j.running);}
$("#load").onclick=attempt(async()=>{doc=await api("/api/recipe?id="+encodeURIComponent($("#versions").value));baseline=copy(doc);history=[];future=[];render();message("불러왔습니다. 수정본은 새 이름으로 저장하세요.");});
$("#clone").onclick=attempt(async()=>{doc=await api("/api/recipe?id="+encodeURIComponent($("#versions").value));baseline=copy(doc);doc.id=doc.id+"_Next";upgrade();history=[];future=[];render();message("새 버전 초안입니다. 이름을 정하고 필요한 항목을 수정하세요.");});
$("#versionName").onchange=()=>{if(doc)edit(()=>doc.id=$("#versionName").value);};
$("#undo").onclick=()=>{if(history.length){future.push(copy(doc));doc=history.pop();render();}};
$("#redo").onclick=()=>{if(future.length){history.push(copy(doc));doc=future.pop();render();}};
$("#search").oninput=filter;
$("#validate").onclick=attempt(async()=>{let r=await api("/api/validate",doc);message([r.message,...r.warnings].join("\n"));});
$("#save").onclick=attempt(async()=>{let r=await api("/api/save",doc);doc=await api("/api/recipe?id="+encodeURIComponent(doc.id));baseline=copy(doc);render();message(r.message);await refresh();});
for(const [buttonId,mode] of [["preview","preview"],["build","build"],["play","play"]])$("#"+buttonId).onclick=attempt(async()=>{if(!doc)throw Error("먼저 버전을 여세요.");const saved=await api("/api/recipe?id="+encodeURIComponent(doc.id));if(JSON.stringify(saved)!==JSON.stringify(doc))throw Error("저장되지 않은 변경이 있습니다. 새 버전 이름으로 저장하세요.");let r=await api("/api/job",{mode,id:doc.id});message(r.message);await refresh();});
$("#logs").onclick=attempt(async()=>{$("#logText").textContent=(await api("/api/log")).text;$("#logDialog").showModal();});
(async()=>{try{schema=await api("/api/schema");const catalog=await api("/api/catalog");
 for(const [id,items] of [["actionAssets",catalog.actions],["montageAssets",catalog.montages],["niagaraAssets",catalog.niagara||[]]]){const list=el("datalist");list.id=id;items.forEach(v=>{const o=el("option");o.value=v;list.append(o);});document.body.append(list);}
 await refresh();render();setInterval(()=>refresh().catch(e=>message(e.message,true)),4000);}catch(e){message(e.message,true);}})();

$("#exportDiagnostic").onclick=attempt(async()=>{
 const diagnostic={kind:"ConstellationCombatReproduction",version:1,draft:doc,baseline,changes:doc?differences(baseline,doc):[],job:state.job,log:(await api("/api/log")).text};
 const url=URL.createObjectURL(new Blob([JSON.stringify(diagnostic,null,2)],{type:"application/json"}));
 const a=el("a");a.href=url;a.download=(doc?.id||"Combat")+"-diagnostic.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
