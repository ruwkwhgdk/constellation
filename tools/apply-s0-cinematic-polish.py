"""Apply authored S0 feedback without recreating the graph or source animation."""
import unreal as u,json,shutil,hashlib,re,math
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0CinematicPolish';P=lambda o,k:o.get_editor_property(k)
def sp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
files=[R/'Content/SceneDirector/School/DA_S0_Opening.uasset',R/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap',R/'Content/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData.uasset']
hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
for f in files:
 b=O/('before-'+f.name)
 if b.exists():assert b.read_bytes()==f.read_bytes(),'Source changed since backup: inspect before re-running'
 else:shutil.copy2(f,b)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
by={x.get_actor_label():x for x in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};stage=by['S0_OpeningStage'];g=by['S0_LittleGirl_Blocking']
comps=[c for c in g.get_components_by_class(u.SkeletalMeshComponent) if c.get_skeletal_mesh_asset()]
rig=[dict(mesh=c.get_skeletal_mesh_asset().get_path_name(),bones=[str(c.get_bone_name(i)) for i in range(c.get_num_bones())],relative_rotation=str(c.get_relative_transform().rotation.rotator())) for c in comps]
(O/'girl-rig.json').write_text(json.dumps(rig,ensure_ascii=False,indent=2),encoding='utf8')
sounds={}
for name in ['S_UI_DialogueTick','S_Locker_MetalOpen','S_Girl_RunApproach']:
 existing=u.load_asset('/Game/SceneDirector/School/S0/Audio/'+name)
 if existing:sounds[name]=existing;continue
 task=sp(u.AssetImportTask(),filename=str(R/'ArtSource/SchoolOpening/Audio'/(name+'.wav')),destination_path='/Game/SceneDirector/School/S0/Audio',destination_name=name,automated=True,save=True,replace_existing=False)
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);assert task.imported_object_paths;sounds[name]=u.load_asset(task.imported_object_paths[0])
sp(stage,door_sound=sounds['S_Locker_MetalOpen'],girl_run_sound=sounds['S_Girl_RunApproach'])
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');sp(a,dialogue_character_interval=.1,dialogue_tick_sound=sounds['S_UI_DialogueTick']);ss=list(P(a,'steps'));N=u.DirectorNodeType
def link(x,y):sp(x,next_nodes=[P(y,'id')])
def make(typ,**kw):
 n=sp(u.SceneDirectorLibrary.make_director_step(typ),**kw);ss.append(n);return n
def shake(duration,trans,rot):
 return make(N.CAMERA_SHAKE,shake=sp(u.DirectorShakeSettings(),duration=duration,translation_range=trans,rotation_range=rot,frequency=10.,blend_in=.06,blend_out=.25),wait_for_completion=False)
eye_shake=shake(.55,.7,.4)
parents=[s for s in ss if any(u.GuidLibrary.equal_equal_guid_guid(x,P(ss[92],'id')) for x in P(s,'next_nodes'))];assert len(parents)==1
link(parents[0],eye_shake);link(eye_shake,ss[92])
# Open-door camera movement at 70% of its prior speed.
sp(ss[61],duration=P(ss[61],'duration')/.7)
# Hold the same framing for the stammer; zoom only when the scream begins.
link(ss[62],ss[64]);link(ss[64],ss[63]);d=P(ss[63],'destination');sp(d,value=u.Vector(3100,0,148));r=P(ss[63],'rotation');sp(r,value=u.Vector(0,-19,180));sp(ss[63],destination=d,rotation=r,duration=.35,wait_for_completion=False)
scream_shake=shake(1.15,2.8,2.4);link(ss[63],scream_shake);link(scream_shake,ss[65])
# Run SFX and approaching narration begin together, not after arrival.
run=make(N.GAME_ACTION,action_key='S0',action_parameters=sp(u.DirectorActionParameters(),identifier='PlayGirlRun'),editor_position=u.Vector2D(14000,700))
# Preserve existing action class/key serialization rather than guessing authoring key names.
sp(run,action_key=P(ss[59],'action_key'))
link(ss[53],run);link(run,ss[54]);sp(ss[54],wait_for_completion=False)
join=make(N.HUB,next_nodes=P(ss[55],'next_nodes'));link(ss[55],join)
# Give the first-person image time to show the falling body/arms before moving down.
pts=list(P(ss[70],'motion_points'))
for p in pts:
 if P(p,'time')>0:sp(p,time=P(p,'time')+1/3)
hold=sp(u.DirectorMotionPoint(),time=1/3,position=P(pts[0],'position'),rotation=P(pts[0],'rotation'),scale=u.Vector(1,1,1),interpolation=u.DirectorPathInterpolation.LINEAR)
pts.insert(1,hold);sp(ss[70],motion_points=pts,duration=2+1/3)
sp(ss[71],duration=1.)
old=ss[72];high=sp(u.SceneDirectorLibrary.make_director_step(N.CAMERA_MOVE),camera_key=P(ss[70],'camera_key'),duration=3.5,wait_for_completion=True,next_nodes=P(old,'next_nodes'),editor_position=P(old,'editor_position'))
sp(high,destination=sp(u.DirectorVectorInput(),value=u.Vector(3140,-150,280)),rotation=sp(u.DirectorVectorInput(),value=u.Vector(0,-38,139)))
link(ss[71],high);ss[72]=high
sp(ss[79],duration=3.5)
assert not any(P(s,'type')==N.FADE for s in ss),'Unexpected existing fade: review before saving'
sp(a,steps=ss);result=str(u.SceneDirectorLibrary.compile_director(a));assert '생성 완료' in result,result
table=u.load_asset('/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData');rows=json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(table));row=next(x for x in rows if x['Name']=='AbandonedSchool_S0_ChoicePrompt')
oldtext=row['Description'];m=re.fullmatch(r'NSLOCTEXT\(("(?:[^"\\]|\\.)*"),\s*("(?:[^"\\]|\\.)*"),\s*("(?:[^"\\]|\\.)*")\)',oldtext);assert m
row['Description']='NSLOCTEXT('+m[1]+', '+m[2]+', '+json.dumps('무엇을 할까요?',ensure_ascii=False)+')';assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows,ensure_ascii=False))
for f in files:assert hashlib.sha256(f.read_bytes()).hexdigest()==hashes[str(f)],'Concurrent asset change '+str(f)
assert u.EditorAssetLibrary.save_loaded_asset(table,False);assert u.EditorAssetLibrary.save_loaded_asset(a,False);assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(O/'applied.json').write_text(json.dumps(dict(compile=result,rig=rig,character_interval=.1,door_camera_speed=.7,ground_hold=1.,zoomout=3.5,gameplay_blend=3.5),ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_CINEMATIC_POLISH_APPLIED '+result)
