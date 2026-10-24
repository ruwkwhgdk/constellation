"""Finalize approved S0 camera continuity and timed landing impact."""
import unreal as u,runpy,json,shutil,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0Feedback1016Final';O.mkdir(exist_ok=True)
P=lambda o,k:o.get_editor_property(k)
base=runpy.run_path(str(R/'tools/revise-s0-feedback1015.py'));sp=base['sp']
files=[R/'Content/SceneDirector/School/DA_S0_Opening.uasset',R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap']
hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
for f in files:
 b=O/('before-'+f.name)
 if not b.exists():shutil.copy2(f,b)
w=u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool');assert w
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening')
assert len(P(a,'steps'))==114,'Do not apply twice or overwrite concurrent graph edits'
base['revise'](a,camera_draft=True)
ss=list(P(a,'steps'));N=u.DirectorNodeType
def make(typ,**kw):
 n=sp(u.SceneDirectorLibrary.make_director_step(typ),**kw);ss.append(n);return n
def link(x,y):sp(x,next_nodes=[P(y,'id')])
# Keep the original fall duration without joining the girl's longer escape.
sp(ss[70],wait_for_completion=False)
wait=make(N.WAIT,duration=1.5)
impact=make(N.GAME_ACTION,action_key=P(ss[69],'action_key'),action_parameters=sp(u.DirectorActionParameters(),identifier='FallImpact'))
shake=make(N.CAMERA_SHAKE,shake=sp(u.DirectorShakeSettings(),duration=.45,translation_range=1.2,rotation_range=.8,frequency=14.,blend_in=.02,blend_out=.35),wait_for_completion=False)
hub=make(N.WAIT,duration=P(ss[70],'duration')-1.5)
link(ss[70],wait);link(wait,impact);link(impact,shake);link(shake,hub);link(hub,ss[71])
sp(a,steps=ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result
stage=next(x for x in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(x,u.SchoolOpeningSceneActor))
sp(stage,use_first_person_head_mask=True)
for f in files:assert hashlib.sha256(f.read_bytes()).hexdigest()==hashes[str(f)],'Concurrent change: '+str(f)
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(O/'saved.json').write_text(json.dumps(dict(compile=result,steps=len(ss),head_mask=True,impact_delay=1.5),ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_FINAL_SAVED '+result)
u.SystemLibrary.quit_editor()
