"""Apply only the dialogue delta from #S0 fetched 2026-10-15 (KST)."""
import unreal as u,json,re,shutil,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'Saved/S0NotionDialogue';O.mkdir(exist_ok=True)
P=lambda x,k:x.get_editor_property(k)
def setp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
gid=lambda g:tuple(P(g,k) for k in ['a','b','c','d'])
prefix='AbandonedSchool_S0_';D='/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData';A='/Game/SceneDirector/School/DA_S0_Opening'
table=u.load_asset(D);asset=u.load_asset(A);assert table and asset
rows=json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(table));original={r['Name']:dict(r) for r in rows};by={r['Name']:r for r in rows}
new={'WakeScenery':'눈을 뜨자, 낯선 풍경이 보입니다.','WakeConfined':'아마도…당신은 굉장히 좁은 곳 안에 갇혀 있는 것 같습니다.','InspectClassroomFurniture':'칠판과 책상, 그리고 의자들이 보입니다.','InspectAbandonedClassroom':'버려진 지 오랜 시간이 지난 교실인 것 같습니다.','DiscoverMemoryPhoto':'우측 벽 한 쪽에 사진이 하나 걸려 있는 것을 발견합니다.'}
changed={'InspectSlit':'고개를 들어서 좁은 틈 너머로 바깥을 살펴봅니다.','GirlApproaches':'처음 보는 소녀가 당신이 갇혀 있는 곳 앞으로 달려옵니다.'}
assert not any(prefix+k in by for k in new),'Already applied or conflicting keys'
files=[R/'Content/SceneDirector/School/DA_S0_Opening.uasset',R/'Content/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData.uasset'];hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
for f in files:
 b=O/('before-'+f.name)
 if b.exists():assert b.read_bytes()==f.read_bytes()
 else:shutil.copy2(f,b)
for key,text in new.items():rows.append({'Name':prefix+key,'Description':text})
for key,text in changed.items():
 row=by[prefix+key];match=re.fullmatch(r'NSLOCTEXT\(("(?:[^"\\]|\\.)*"),\s*("(?:[^"\\]|\\.)*"),\s*("(?:[^"\\]|\\.)*")\)',row['Description']);assert match,key
 row['Description']='NSLOCTEXT('+match[1]+', '+match[2]+', '+json.dumps(text,ensure_ascii=False)+')'
assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows,ensure_ascii=False))
after={r['Name']:r for r in json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(table))}
assert all(after[k]==v for k,v in original.items() if k not in [prefix+x for x in changed])
steps=list(P(asset,'steps'));N=u.DirectorNodeType;before=str(u.SceneDirectorLibrary.compile_director(asset));added=[]
def key(s):return str(P(P(s,'dialogue_row'),'row_name'))
def make(k,anchor,offset):
 pos=P(anchor,'editor_position');s=u.SceneDirectorLibrary.make_director_step(N.DIALOGUE)
 setp(s,dialogue_text=new[k],dialogue_row=setp(u.DataTableRowHandle(),data_table=table,row_name=prefix+k),dialogue_advance=u.DirectorDialogueAdvance.CLICK,duration=.6,wait_for_completion=True,speaker_name='',editor_position=u.Vector2D(pos.x+offset*210,pos.y+180))
 steps.append(s);added.append(prefix+k);return s
def before_node(anchor,keys):
 parents=[s for s in steps if any(gid(g)==gid(P(anchor,'id')) for g in P(s,'next_nodes'))];assert len(parents)==1
 chain=[make(k,anchor,i) for i,k in enumerate(keys)]
 setp(parents[0],next_nodes=[P(chain[0],'id') if gid(g)==gid(P(anchor,'id')) else g for g in P(parents[0],'next_nodes')])
 for i,s in enumerate(chain):setp(s,next_nodes=[P(chain[i+1] if i+1<len(chain) else anchor,'id')])
def after_node(anchor,keys):
 old=list(P(anchor,'next_nodes'));assert len(old)==1;chain=[make(k,anchor,i) for i,k in enumerate(keys)];setp(anchor,next_nodes=[P(chain[0],'id')])
 for i,s in enumerate(chain):setp(s,next_nodes=[P(chain[i+1],'id')] if i+1<len(chain) else old)
first=[s for s in steps if P(s,'type')==N.DIALOGUE and len(P(s,'choices'))==3];assert len(first)==1
before_node(first[0],['WakeScenery','WakeConfined'])
slits=[s for s in steps if key(s)==prefix+'InspectSlit'];photos=[s for s in steps if key(s)==prefix+'MemoryPhoto'];assert len(slits)==2 and len(photos)==2
for s in slits:after_node(s,['InspectClassroomFurniture','InspectAbandonedClassroom'])
for s in photos:before_node(s,['DiscoverMemoryPhoto'])
for s in steps:
 if key(s) in [prefix+k for k in changed]:setp(s,dialogue_text=changed[key(s)[len(prefix):]])
setp(asset,steps=steps);result=u.SceneDirectorLibrary.compile_director(asset);assert result is not None
for f in files:assert hashlib.sha256(f.read_bytes()).hexdigest()==hashes[str(f)],'Concurrent edit'
assert u.EditorAssetLibrary.save_loaded_asset(table,False);assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
(O/'applied.json').write_text(json.dumps(dict(source='https://app.notion.com/p/3a85ddbe5e3780b0b3e3d6d9ce00786e',new_rows=new,changed_rows=changed,new_nodes=len(added),before=before,after=str(result),total_rows=len(after)),ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_NOTION_DIALOGUE_APPLIED '+str(result))
