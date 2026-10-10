"""Apply the 2026-10-08 S0 feedback to existing authored nodes only.
Run with the interactive editor closed. Backups are retained before any asset save.
"""
import unreal as u,json,shutil
from pathlib import Path
ROOT=Path(u.Paths.project_dir()).resolve();OUT=ROOT/'Saved/S0Opening'
BACKUP=OUT/'Backup/feedback-20261008';BACKUP.mkdir(parents=True,exist_ok=True)
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
ASSET='/Game/SceneDirector/School/DA_S0_Opening'
for rel in ['Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap','Content/SceneDirector/School/DA_S0_Opening.uasset']:
 p=ROOT/rel;b=BACKUP/p.name
 if not b.exists():shutil.copy2(p,b)
assert u.EditorLoadingAndSavingUtils.load_map(MAP)
a=u.load_asset(ASSET);steps=list(a.get_editor_property('steps'));N=u.DirectorNodeType

def setp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o

def pos(s):
 p=s.get_editor_property('destination').get_editor_property('value');return tuple(round(v,2) for v in (p.x,p.y,p.z))

def path(s,points,scale=1):
 pts=[setp(u.DirectorMotionPoint(),time=float(t),position=u.Vector(*p),rotation=u.Vector(0,0,yaw),scale=u.Vector(scale,scale,scale),interpolation=u.DirectorPathInterpolation.LINEAR) for t,p,yaw in points]
 setp(s,use_motion_path=True,motion_points=pts,duration=float(points[-1][0]),destination=setp(u.DirectorVectorInput(),value=u.Vector(*points[-1][1])))

def find(kind,old,new):
 rows=[s for s in steps if s.get_editor_property('type')==kind and pos(s) in [old,new]]
 assert len(rows)==1,(old,len(rows))
 return rows[0]
peeks=[s for s in steps if s.get_editor_property('type')==N.CAMERA_MOVE and pos(s) in [(3140,0,165),(3158,0,245)]]
assert len(peeks)==3
for s in peeks:path(s,[(0,(3192,0,165),180),(.7,(3190,0,245),180),(1.3,(3158,0,245),180)])
for s in steps:
 if s.get_editor_property('type')==N.GAME_ACTION:
  p=s.get_editor_property('action_parameters')
  if str(p.get_editor_property('identifier')) in ['PeekStart','PeekEnd']:
   setp(p,identifier='OpenEyes',value=.3);setp(s,action_parameters=p)
f1=find(N.CHARACTER_MOVE,(2700,350,67),(2650,0,67))
f2=find(N.CHARACTER_MOVE,(2100,650,67),(650,-50,67))
f3=find(N.CHARACTER_MOVE,(1900,790,7),(450,-50,67))
path(f1,[(0,(3010,0,67),-90),(.6,(3010,0,67),90),(1.5,(2650,0,67),90)],.7)
path(f2,[(0,(2650,0,67),90),(4.6,(850,0,67),90),(5.1,(650,-50,67),90)],.7)
# The current single-bone girl stops at the opening; this does not invent a crawl pose.
path(f3,[(0,(650,-50,67),90),(.6,(450,-50,67),90)],.7)
for s in steps:
 if s.get_editor_property('type')==N.CAMERA_MOVE and pos(s) in [(3030,0,170),(2860,0,35),(2860,0,45)]:
  r=s.get_editor_property('rotation');v=r.get_editor_property('value');v.z=180
  if pos(s)==(2860,0,45):v.y=0
  setp(r,value=v);setp(s,rotation=r)
a.set_editor_property('steps',steps)
result=u.SceneDirectorLibrary.compile_director(a);assert result is not None
stage=next(x for x in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(x,u.SchoolOpeningSceneActor))
stage.set_editor_property('region_title_class',None)
assert not stage.get_editor_property('region_title_class')
assert u.EditorAssetLibrary.save_loaded_asset(a,False)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(OUT/'feedback-20261008-result.json').write_text(json.dumps({'success':True,'compile':str(result),'physical_vent':[3158,0,245],'turn_degrees':180,'flee_end':[450,-50,67],'region_title':False,'peeks':len(peeks)},indent=2),encoding='utf8')
u.log('S0_FEEDBACK_APPLIED')
u.SystemLibrary.quit_editor()
