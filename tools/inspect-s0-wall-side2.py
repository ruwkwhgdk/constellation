import unreal as u,json,math,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/WallSideProbe2_20261023';O.mkdir(parents=True,exist_ok=True)
try:
 assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
 # Trace visible bright side surfaces at three pixels of the known oblique camera.
 import math
 forward=u.Vector(math.cos(math.radians(10))*math.cos(math.radians(65)),math.cos(math.radians(10))*math.sin(math.radians(65)),math.sin(math.radians(10)))
 right=u.Vector(-math.sin(math.radians(65)),math.cos(math.radians(65)),0)
 up=u.Vector(-math.sin(math.radians(10))*math.cos(math.radians(65)),-math.sin(math.radians(10))*math.sin(math.radians(65)),math.cos(math.radians(10)))
 probe=[]
 for px,py in [(x,y) for x,y in [(1065,330),(1070,380),(1070,445),(1080,505),(1020,350),(1120,350),(1090,400)]]:
  direction=forward+right*((px/800-1)*math.tan(math.radians(41.5)))+up*((1-py/450)*math.tan(math.radians(41.5))*900/1600)
  result=u.SystemLibrary.line_trace_single(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),u.Vector(600,400,300),u.Vector(600,400,300)+direction*6000,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],u.DrawDebugTrace.NONE,True)
  hit={}
  for key in ['blocking_hit','distance','location','impact_point','impact_normal','component','face_index','element_index']:
   try:hit[key]=str(result.get_editor_property(key))
   except Exception as err:hit[key]=str(err)
  probe.append({'pixel':[px,py],'hit':hit})
 (O/'probes.json').write_text(json.dumps(probe,indent=2))

except Exception:
 (O/'error.txt').write_text(traceback.format_exc())
u.SystemLibrary.quit_editor()
