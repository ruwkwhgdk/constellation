import unreal as u,json,re
from pathlib import Path
t=u.load_asset('/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData')
rows=json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(t));original={r['Name']:dict(r) for r in rows};key='AbandonedSchool_S0_ChoicePrompt'
row=next(r for r in rows if r['Name']==key)
assert '눈을 뜨자, 낯선 풍경이 보입니다.' in row['Description']
row['Description']=row['Description'].replace('눈을 뜨자, 낯선 풍경이 보입니다.','…')
assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(t,json.dumps(rows,ensure_ascii=False))
after={r['Name']:r for r in json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(t))}
assert all(after[k]==v for k,v in original.items() if k!=key)
assert u.EditorAssetLibrary.save_loaded_asset(t,False)
out=Path(u.Paths.project_dir())/'Saved/S0NotionDialogue/applied.json';report=json.loads(out.read_text(encoding='utf8'));report['changed_rows']['ChoicePrompt']='…';out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_CHOICE_PROMPT_SEPARATED')
