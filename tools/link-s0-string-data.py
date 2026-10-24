"""Link S0 to existing sequence string DataTable; preserve all existing row text and localization IDs."""
import unreal as u,json,shutil
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'Saved/S0StringTable';O.mkdir(exist_ok=True)
A='/Game/SceneDirector/School/DA_S0_Opening';D='/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData'
P=lambda x,k:x.get_editor_property(k)
def setp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
a=u.load_asset(A);table=u.load_asset(D);assert a and table
for rel in ['Content/SceneDirector/School/DA_S0_Opening.uasset','Content/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData.uasset']:
 p=R/rel;b=O/('before-link-'+p.name)
 if not b.exists():shutil.copy2(p,b)
rows=json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(table));original={x['Name']:dict(x) for x in rows};by=dict(original)
prefix='AbandonedSchool_S0_';legacy='AbandonedSchool_Sequence_Little_Girl_Classroom_Start_'
body_keys={'…':'ChoicePrompt','좁은 틈 너머로 칠판이 보입니다.':'InspectSlit','포스트잇, 스티커, 별자리 사진, 키링…':'InspectLocker','그다지 특별한 건 보이지 않습니다.':'NothingSpecial','사진에는 당신이 찍혀 있습니다.':'MemoryPhoto','옆에 서 있는 건…누구일까요?':'PhotoCompanion','잠시 기억을 되짚어보지만, 그녀에 대한 것은 전혀 떠오르지 않습니다.':'MissingMemory','처음 보는 소녀가 당신이 갇혀 있는 락커 앞으로 달려옵니다.':'GirlApproaches'}
legacy_keys={'동쪽 하늘에서도 서쪽 하늘에서도':2,'어?':4,'이게 뭐지?':5,'…..':6,'이, 이, 이…':7,'인간이다아!!':8}
steps=list(P(a,'steps'));manifest=[];song=0
speaker=u.load_asset('/Game/Constellation/Gameplay/Sequences/Data/DT_SpeakerData');speaker_names={str(n) for n in u.DataTableFunctionLibrary.get_data_table_row_names(speaker)} if speaker else set()
def link(obj,field,text,key):
 row=P(obj,field)
 if P(row,'data_table'):
  assert P(row,'data_table')==table and str(P(row,'row_name')) in by;key=str(P(row,'row_name'))
 else:
  if key not in by:
   assert key.startswith(prefix),('Expected existing legacy row',key)
   by[key]={'Name':key,'Description':text};rows.append(by[key])
  setp(obj,**{field:setp(u.DataTableRowHandle(),data_table=table,row_name=key)})
 manifest.append({'field':field,'key':key,'previous_direct_text':text})
for s in steps:
 if P(s,'type')!=u.DirectorNodeType.DIALOGUE:continue
 text=str(P(s,'dialogue_text'));ref=P(s,'dialogue_row')
 if P(ref,'data_table'):key=str(P(ref,'row_name'))
 elif text=='반짝반짝 작은 별 아름답게 비치네':song+=1;key=legacy+str(1 if song==1 else 3)
 elif text in legacy_keys:key=legacy+str(legacy_keys[text])
 else:assert text in body_keys,('Unmapped dialogue',text);key=prefix+body_keys[text]
 link(s,'dialogue_row',text,key)
 choices=list(P(s,'choices'))
 for c in choices:
  link(c,'text_row',str(P(c,'text')),prefix+'Choice_'+str(P(c,'key')))
  if str(P(c,'disabled_reason')):link(c,'disabled_reason_row',str(P(c,'disabled_reason')),prefix+'Choice_'+str(P(c,'key'))+'_Disabled')
 setp(s,choices=choices)
 # Reuse the existing speaker master, retaining narration with no visible name.
 if P(s,'speaker_source')==u.DirectorSpeakerSource.DIRECT:
  sk={'???':'Girl_Unknown','꼬마 소녀':'Girl'}.get(str(P(s,'speaker_name')))
  if sk and sk in speaker_names:setp(s,speaker_source=u.DirectorSpeakerSource.TABLE,speaker_row=setp(u.DataTableRowHandle(),data_table=speaker,row_name=sk))
assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows,ensure_ascii=False))
after={x['Name']:x for x in json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(table))}
assert all(after[k]==v for k,v in original.items()),'Existing table row or localization identity changed'
setp(a,steps=steps);result=u.SceneDirectorLibrary.compile_director(a);assert result is not None,str(result)
assert u.EditorAssetLibrary.save_loaded_asset(table,False);assert u.EditorAssetLibrary.save_loaded_asset(a,False)
report=dict(asset=A,table=D,existing_rows_preserved=len(original),total_rows=len(after),new_rows=[k for k in after if k not in original],references=manifest,compile=str(result))
(O/'linked.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
(O/'after-link-table.json').write_text(json.dumps(list(after.values()),ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_STRING_DATA_LINKED '+str(len(manifest)))
