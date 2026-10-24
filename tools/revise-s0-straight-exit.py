"""Align the authored aperture and overlap the existing fall with the girl's run."""
import unreal as u,json,shutil,hashlib
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0ExitRevision';P=lambda o,k:o.get_editor_property(k)
def setp(o,**values):
 for k,v in values.items():o.set_editor_property(k,v)
 return o
guid=lambda g:tuple(P(g,k) for k in ['a','b','c','d'])
files=[R/'Content/SceneDirector/School/DA_S0_Opening.uasset',R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap']
hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
for f in files:
 target=O/('before-'+f.name)
 if target.exists():assert target.read_bytes()==f.read_bytes(),'Already applied or changed; inspect before retrying'
 else:shutil.copy2(f,target)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');s=list(P(a,'steps'));N=u.DirectorNodeType
before=str(u.SceneDirectorLibrary.compile_director(a));assert '72.43' in before,before
assert P(s[67],'type')==N.CHARACTER_MOVE and P(P(s[69],'action_parameters'),'identifier')=='Fall'
assert guid(P(s[67],'next_nodes')[0])==guid(P(s[68],'id'))
assert guid(P(s[72],'next_nodes')[0])==guid(P(s[73],'id'))
for i in [73,74]:
 pts=list(P(s[i],'motion_points'))
 for pt in pts:
  pos=P(pt,'position');pos.y=0;setp(pt,position=pos)
 dest=P(s[i],'destination');pos=P(dest,'value');pos.y=0;setp(dest,value=pos)
 setp(s[i],motion_points=pts,destination=dest)
# Start long run before the existing camera/fall chain, then wait for both at the hub.
hub=setp(u.SceneDirectorLibrary.make_director_step(N.HUB),next_nodes=[P(s[74],'id')],editor_position=u.Vector2D(19000,300))
assert guid(P(hub,'id')) not in [guid(P(x,'id')) for x in s]
setp(s[67],next_nodes=[P(s[73],'id')]);setp(s[73],wait_for_completion=False,next_nodes=[P(s[68],'id')]);setp(s[72],next_nodes=[P(hub,'id')]);s.append(hub)
setp(a,steps=s);after=u.SceneDirectorLibrary.compile_director(a);assert after is not None
by={x.get_actor_label():x for x in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
for name,expected_y in [('classroom_start_floor_16',-100),('classroom_start_floor_17',2800),('classroom_start_floor_18',0)]:
 actor=by[name];pos=actor.get_actor_location();assert abs(pos.y-expected_y)<.1;pos.y+=50;actor.set_actor_location(pos,False,True)
left,le=by['classroom_start_floor_16'].get_actor_bounds(False);right,re=by['classroom_start_floor_17'].get_actor_bounds(False);top,te=by['classroom_start_floor_18'].get_actor_bounds(False)
assert abs(left.y+le.y+50)<.1 and abs(right.y-re.y-50)<.1 and abs(top.y)<.1
for f in files:assert hashlib.sha256(f.read_bytes()).hexdigest()==hashes[str(f)],'Concurrent edit: '+str(f)
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(O/'applied.json').write_text(json.dumps(dict(before=before,after=str(after),aperture_center_y=0,aperture_width=100,run_y=0,fall_overlaps_run=True),ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_STRAIGHT_EXIT_APPLIED '+str(after))
