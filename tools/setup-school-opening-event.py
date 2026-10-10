"""Create S0 once. Existing authored assets are never silently regenerated.
Run in Unreal editor Python; backups and report are in Saved/S0Opening.
"""
import unreal as u
from pathlib import Path
import shutil,json
ROOT=Path(u.Paths.project_dir()).resolve();OUT=ROOT/'Saved/S0Opening';OUT.mkdir(exist_ok=True,parents=True)
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
ASSET='/Game/SceneDirector/School/DA_S0_Opening'
assert not u.EditorAssetLibrary.does_asset_exist(ASSET), 'S0 already exists; edit the graph or explicitly remove your generated draft before rebuilding.'
source=ROOT/'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
backup=OUT/'Backup/AbandonedSchool.before-S0.umap';backup.parent.mkdir(exist_ok=True,parents=True)
if not backup.exists():shutil.copy2(source,backup)
assert u.EditorLoadingAndSavingUtils.load_map(MAP)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
allactors=actors.get_all_level_actors();locker=next(a for a in allactors if a.get_actor_label()=='locker_player')
assert not any(a.get_actor_label()=='S0_OpeningStage' for a in allactors),'Partial S0 authoring detected'
def setp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
def xf(x,y,z,yaw=0,scale=1):return u.Transform(location=u.Vector(x,y,z),rotation=u.Rotator(yaw=yaw),scale=u.Vector(scale,scale,scale))
def mesh_actor(label,path,pos,rot=u.Rotator(),scale=u.Vector(1,1,1)):
 a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),rot);a.set_actor_label(label);a.set_folder_path('S0 Opening')
 c=a.static_mesh_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_static_mesh(u.load_asset(path));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_scale3d(scale);return a
body=locker.get_component_by_class(u.StaticMeshComponent);body.set_static_mesh(u.load_asset('/Game/Constellation/Environments/School/Props/SM_Locker/SM_Locker_Body'))
door=mesh_actor('S0_LockerDoor','/Game/Constellation/Environments/School/Props/SM_Locker/SM_Locker_Door',(3151.8,74.18,142),u.Rotator(yaw=90),u.Vector(1.08,.75,1.03))
girl=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(1800,450,67),u.Rotator(yaw=-90));girl.set_actor_label('S0_LittleGirl_Blocking');girl.set_folder_path('S0 Opening')
girl.skeletal_mesh_component.set_skeletal_mesh_asset(u.load_asset('/Game/Constellation/Characters/NPC/Little_Girl/SKM_Little_Girl'));girl.set_actor_scale3d(u.Vector(.7,.7,.7));girl.set_actor_enable_collision(False)
stage=actors.spawn_actor_from_class(u.SchoolOpeningSceneActor,u.Vector(1800,450,130));stage.set_actor_label('S0_OpeningStage');stage.set_folder_path('S0 Opening')
setp(stage,girl=girl,locker=door,door_component_name='StaticMeshComponent0',exit_transform=xf(2780,0,100,180),region_title_class=None)
# Component's actual name varies across engine versions; capture the spawned component.
stage.set_editor_property('door_component_name',door.static_mesh_component.get_name())
asset=u.AssetToolsHelpers.get_asset_tools().create_asset('DA_S0_Opening','/Game/SceneDirector/School',u.SceneDirectorAsset,u.SceneDirectorFactory())
assert asset
setp(asset,event_key='S0_Opening',actions=[setp(u.DirectorActionEntry(),key='S0',action_class=u.SchoolOpeningSceneAction)],objects=[setp(u.DirectorObjectEntry(),key='Girl',actor_class=u.SkeletalMeshActor)])
cam=setp(u.DirectorCameraEntry(),key='Eyes',transform=xf(3203,0,214.6,180),field_of_view=115.0);setp(asset,cameras=[cam])
N=u.DirectorNodeType;steps=[];labels={}
def node(kind,label='',**kw):
 s=u.SceneDirectorLibrary.make_director_step(kind);setp(s,duration=.1,**kw);setp(s,editor_position=u.Vector2D(len(steps)*260,0));steps.append(s);labels[str(s.get_editor_property('id'))]=label;return s
def link(a,b):setp(a,next_nodes=[b.get_editor_property('id')])
def chain(seq):
 for a,b in zip(seq,seq[1:]):link(a,b)
 return seq
# Actions are instantaneous; graph Wait nodes own all scene duration.
def cue(name,seconds=0):return node(N.GAME_ACTION,name,action_key='S0',action_parameters=setp(u.DirectorActionParameters(),identifier=name,value=float(seconds)))
def wait(t):s=node(N.WAIT);setp(s,duration=float(t));return s
def camera(pos=(3203,0,214.6),yaw=180,pitch=0,roll=0,t=1):
 s=node(N.CAMERA_MOVE,camera_key='Eyes',destination=setp(u.DirectorVectorInput(),value=u.Vector(*pos)),rotation=setp(u.DirectorVectorInput(),value=u.Vector(roll,pitch,yaw)));setp(s,duration=float(t));return s
def say(text,speaker='',t=.6,click=True):
 s=node(N.DIALOGUE,text,dialogue_text=text,speaker_name=speaker,dialogue_advance=u.DirectorDialogueAdvance.CLICK if click else u.DirectorDialogueAdvance.TIMED);setp(s,duration=float(t));return s
def choice(keys):
 s=say('…');options=[]
 for key in keys+['Force']:
  options.append(setp(u.DirectorChoice(),key=key,text={'Slit':'틈으로 밖을 살펴본다.','Inside':'락커 안을 둘러본다.','Force':'문을 연다. (필요 스탯 : 힘 1)'}[key],enabled=key!='Force',disabled_reason='힘이 부족합니다.' if key=='Force' else ''))
 setp(s,choices=options);return s
def motion(s,points,scale=1):
 pts=[setp(u.DirectorMotionPoint(),time=float(t),position=u.Vector(*p),rotation=u.Vector(0,0,yaw),scale=u.Vector(scale,scale,scale),interpolation=u.DirectorPathInterpolation.LINEAR) for t,p,yaw in points]
 setp(s,use_motion_path=True,motion_points=pts,duration=float(points[-1][0]));return s

def vent():return motion(camera((3165,0,214.6),t=1.3),[(0,(3203,0,214.6),180),(.7,(3180,0,214.6),180),(1.3,(3165,0,214.6),180)])

def peek():return chain([node(N.CLOSE_DIALOGUE),cue('OpenEyes',.3),vent(),say('좁은 틈 너머로 칠판이 보입니다.'),node(N.CLOSE_DIALOGUE),cue('OpenEyes',.3),camera(t=.8)])
def inside():return chain([node(N.CLOSE_DIALOGUE),camera(yaw=162,pitch=12,t=.9),say('포스트잇, 스티커, 별자리 사진, 키링…'),say('그다지 특별한 건 보이지 않습니다.'),camera((3181,-18,220),yaw=228,pitch=12,t=.7),say('사진에는 당신이 찍혀 있습니다.'),say('옆에 서 있는 건…누구일까요?'),say('잠시 기억을 되짚어보지만, 그녀에 대한 것은 전혀 떠오르지 않습니다.'),node(N.CLOSE_DIALOGUE),camera(t=.8)])
def move(pos,t):
 s=node(N.CHARACTER_MOVE,role='Girl',destination=setp(u.DirectorVectorInput(),value=u.Vector(pos[0],pos[1],pos[2]+67)),move_timing=u.DirectorMoveTiming.DURATION,play_move_animation=False);setp(s,duration=float(t));return s
intro=chain([node(N.START),node(N.INPUT_LOCK,lock_input=True),node(N.HUD_HIDDEN,hide_hud=True),node(N.PLAYER_HIDDEN,hide_player=True),node(N.BIND_NPC,role='Girl',actor_source=u.DirectorActorSource.OBJECT,object_key='Girl',actor_class=u.SkeletalMeshActor,transform=girl.get_actor_transform()),node(N.VISIBILITY,role='Girl',visible=True),cue('Begin'),camera(t=.1),wait(.5),cue('OpenEyes',2.4),wait(2.5),camera(yaw=190,t=.6),camera(yaw=170,t=.8),camera(t=.6),choice(['Slit','Inside'])])
a=peek();b=inside();after_a=choice(['Inside']);after_b=choice(['Slit']);ab=inside();ba=peek()
setp(intro[-1],choice_targets={'Slit':a[0].get_editor_property('id'),'Inside':b[0].get_editor_property('id')});link(a[-1],after_a);link(b[-1],after_b)
setp(after_a,choice_targets={'Inside':ab[0].get_editor_property('id')});setp(after_b,choice_targets={'Slit':ba[0].get_editor_property('id')})
final=chain([node(N.CLOSE_DIALOGUE),cue('PlayGirlSong'),wait(1),cue('OpenEyes',.3),vent(),say('반짝반짝 작은 별 아름답게 비치네', '???',3.5,False),move((2450,180,0),2.5),say('동쪽 하늘에서도 서쪽 하늘에서도','???',3.5,False),say('반짝반짝 작은 별 아름답게 비치네','???',3.5,False),cue('StopGirlSong'),say('어?','???',.8,False),node(N.CLOSE_DIALOGUE),cue('OpenEyes',.3),camera(t=.6),move((3010,0,0),1.5),say('처음 보는 소녀가 당신이 갇혀 있는 락커 앞으로 달려옵니다.'),say('이게 뭐지?','???'),node(N.CLOSE_DIALOGUE),wait(1),cue('OpenDoor',1.3),wait(1.5),camera(pitch=-27,t=.5),say('…..','꼬마 소녀',1.3,False),camera((3140,0,150),pitch=-8,t=.5),say('이, 이, 이…','꼬마 소녀',1.5,False),say('인간이다아!!','꼬마 소녀',1.3,False),node(N.CLOSE_DIALOGUE),motion(move((2650,0,0),1.5),[(0,(3010,0,67),-90),(.6,(3010,0,67),90),(1.5,(2650,0,67),90)],.7),camera((3030,0,170),yaw=180,pitch=-10,t=.6),cue('Fall'),camera((2860,0,35),yaw=180,pitch=-45,roll=24,t=.5),wait(.5),camera((2860,0,45),yaw=180,pitch=0,roll=8,t=1),motion(move((650,-50,0),5.1),[(0,(2650,0,67),90),(4.6,(850,0,67),90),(5.1,(650,-50,67),90)],.7),motion(move((450,-50,0),.6),[(0,(650,-50,67),90),(.6,(450,-50,67),90)],.7),node(N.VISIBILITY,role='Girl',visible=False),wait(.6),cue('PrepareHandoff'),node(N.CLOSE_DIALOGUE),node(N.GAMEPLAY_RETURN),node(N.END)])
setp(final[-2],duration=2.0);link(ab[-1],final[0]);link(ba[-1],final[0])
# Lay out readable rows by story sections, rather than a single giant horizontal chain.
for row,seq in enumerate([intro,a,[after_a],ab,b,[after_b],ba,final]):
 for col,s in enumerate(seq):setp(s,editor_position=u.Vector2D(col*265,row*280))
setp(asset,steps=steps)
result=u.SceneDirectorLibrary.compile_director(asset);assert result is not None,str(result)
assert u.EditorAssetLibrary.save_loaded_asset(asset,False)
binding=actors.spawn_actor_from_class(u.SceneEventBinding,u.Vector(3100,0,0));binding.set_actor_label('S0_LevelStart');binding.set_folder_path('S0 Opening')
setp(binding,director=asset,trigger=u.SceneEventTrigger.LEVEL_READY,repeat=u.SceneEventRepeat.ONCE_PER_VISIT,start_order=-100,objects={'Girl':girl})
assert u.SceneDirectorLibrary.configure_school_tutorial_focus(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),True)>=0
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(OUT/'authoring-report.json').write_text(json.dumps({'asset':ASSET,'steps':len(steps),'compile':str(result),'door_component':door.static_mesh_component.get_name(),'labels':labels},ensure_ascii=False,indent=2),encoding='utf8')
u.log('S0_AUTHORING_SUCCESS '+str(len(steps)))
u.SystemLibrary.quit_editor()
