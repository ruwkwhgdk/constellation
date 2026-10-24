import unreal as u,json
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0Feedback1015';O.mkdir(exist_ok=True)
P=lambda o,k:o.get_editor_property(k)
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
(O/'level.txt').write_text(u.ResourceRecoveryLibrary.export_level_blueprint_graphs(w),encoding='utf8')
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');ss=list(P(a,'steps'));gid=lambda g:tuple(P(g,k) for k in ('a','b','c','d'));ids={gid(P(s,'id')):i for i,s in enumerate(ss)}
(O/'steps.json').write_text(json.dumps([dict(i=i,next=[ids[gid(g)] for g in P(s,'next_nodes')],data=s.export_text()) for i,s in enumerate(ss)],ensure_ascii=False,indent=2),encoding='utf8')
for path in ['/Game/Constellation/Gameplay/Sequences/BP_SequenceManager','/Game/Constellation/Characters/Heroine/Blueprints/BP_PlayerController','/Game/Constellation/Core/BP_GameMode']:
 b=u.load_asset(path)
 if b:(O/(path.split('/')[-1]+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(b),encoding='utf8')
u.log('S0_FEEDBACK_AUDIT_DONE')
