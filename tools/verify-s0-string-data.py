"""Read-only saved reference verification; run in a fresh commandlet process."""
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir())/'Saved/S0StringTable';a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');t=u.load_asset('/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData');p=lambda o,k:o.get_editor_property(k)
rows={str(n) for n in u.DataTableFunctionLibrary.get_data_table_row_names(t)};n=0
for s in p(a,'steps'):
 if p(s,'type')!=u.DirectorNodeType.DIALOGUE:continue
 refs=[p(s,'dialogue_row')]
 for c in p(s,'choices'):
  refs.append(p(c,'text_row'))
  if str(p(c,'disabled_reason')):refs.append(p(c,'disabled_reason_row'))
 for ref in refs:assert p(ref,'data_table')==t and str(p(ref,'row_name')) in rows;n+=1
result=u.SceneDirectorLibrary.compile_director(a);assert result is not None
(R/'verified.json').write_text(json.dumps(dict(reloaded_references=n,table_rows=len(rows),compile=str(result)),ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_STRING_REFERENCES_VERIFIED '+str(n))
