import unreal as u,json
from pathlib import Path
p=lambda o,k:o.get_editor_property(k)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');r=[]
for s in p(a,'steps'):
 if p(s,'type')==u.DirectorNodeType.DIALOGUE:r.append(dict(text=str(p(s,'dialogue_text')),speaker=str(p(s,'speaker_source')),choices=[dict(key=str(p(c,'key')),text=str(p(c,'text')),reason=str(p(c,'disabled_reason'))) for c in p(s,'choices')]))
(Path(u.Paths.project_dir())/'Saved/S0StringTable/dialogues.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
