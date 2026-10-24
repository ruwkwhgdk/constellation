import unreal as u,json
from pathlib import Path
P=lambda o,k:o.get_editor_property(k)
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'));gid=lambda g:tuple(P(g,k) for k in ('a','b','c','d'));ids={gid(P(s,'id')):i for i,s in enumerate(ss)}
out=[]
for i,s in enumerate(ss):
 out.append(dict(i=i,type=str(P(s,'type')),next=[ids[gid(g)] for g in P(s,'next_nodes')],duration=P(s,'duration'),wait=P(s,'wait_for_completion'),role=str(P(s,'role')),text=str(P(s,'dialogue_text')),row=str(P(P(s,'dialogue_row'),'row_name')),action=str(P(P(s,'action_parameters'),'identifier')),visible=P(s,'visible'),points=[dict(t=P(p,'time'),pos=str(P(p,'position')),rot=str(P(p,'rotation'))) for p in P(s,'motion_points')]))
o=Path(u.Paths.project_dir())/'Saved/S0GirlReview';o.mkdir(exist_ok=True);(o/'audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
