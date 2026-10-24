"""Patch only jump timing and montage references; preserve approved camera transforms."""
import unreal as u,json,math
from pathlib import Path

def integrate_jump_animations():
 def prop(o,**kw):
  for k,v in kw.items():o.set_editor_property(k,v)
  return o
 stage=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if isinstance(a,u.JumpAcquisitionStage))
 # User-approved contact alignment: preserve the authored character pose/cameras.
 # Shift the four surrounding skeletons horizontally with the star; keep floor Z.
 star=stage.get_editor_property('star');star.set_actor_location(u.Vector(-13713.18454,-2444.458988,-800),False,True)
 mesh=star.get_component_by_class(u.StaticMeshComponent);mesh.set_world_location(u.Vector(-13713.18454,-2444.458988,-670.310328),False,True)
 skeletons={'skeleton_13':(-13963.18454,-2424.458988,-792),'skeleton_12':(-13713.18454,-2144.458988,-792),'skeleton_14':(-13463.18454,-2424.458988,-792),'skeleton_1':(-13713.18454,-2744.458988,-792)}
 matched=set()
 for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  label=actor.get_actor_label()
  if label in skeletons:actor.set_actor_location(u.Vector(*skeletons[label]),False,True);matched.add(label)
 assert matched==set(skeletons),'Expected four surrounding skeletons'
 base='/Game/Constellation/Characters/Heroine/GamePilot/Interaction/'
 names={'Inspect':'Star_Inspect','Reach':'ReachTouch_Right','Surprise':'Star_Surprise','Absorb':'Star_Absorb','Chest':'Star_RecoverChest','Palm':'Star_PalmConfused'}
 montages={key:u.load_asset(base+'AM_'+name) for key,name in names.items()}
 assert all(montages.values())
 lengths={key:float(u.load_asset(base+'AS_'+name).get_editor_property('sequence_length')) for key,name in names.items()}
 prop(stage,animation_montages=montages)
 graph=u.load_asset('/Game/SceneDirector/School/DA_JumpAcquisition');steps=list(graph.get_editor_property('steps'));N=u.DirectorNodeType
 def cue(s):return str(s.get_editor_property('action_parameters').get_editor_property('identifier')) if s.get_editor_property('type')==N.GAME_ACTION else ''
 for name,length in lengths.items():
  idx=next(i for i,s in enumerate(steps) if cue(s)==name);node=steps[idx]
  prop(node,action_parameters=prop(u.DirectorActionParameters(),identifier=name,value=length))
  end=next((i for i in range(idx+1,len(steps)) if cue(steps[i])),len(steps))
  block=steps[idx+1:end];timed=[s for s in block if s.get_editor_property('type') in {N.CAMERA_MOVE,N.WAIT}]
  if not timed:
   wait=u.SceneDirectorLibrary.make_director_step(N.WAIT);prop(wait,duration=length);steps.insert(idx+1,wait)
  elif name=='Absorb':
   assert len(timed)==1;prop(timed[0],duration=length)
  else:
   fixed=sum(s.get_editor_property('duration') for s in timed[:-1]);prop(timed[-1],duration=length-fixed)
 for i,(s,n) in enumerate(zip(steps,steps[1:])):prop(s,next_nodes=[n.id],editor_position=u.Vector2D((i%9)*270,(i//9)*280))
 shot=next(s for s in steps if s.get_editor_property('type')==N.CAMERA_SWITCH)
 frames=sum(max(1,math.floor(s.get_editor_property('duration')*30+.50001)) for s in steps if s.get_editor_property('type') in {N.WAIT,N.CAMERA_MOVE,N.DIALOGUE})
 prop(shot,duration=frames/30);prop(graph,steps=steps)
 result=u.SceneDirectorLibrary.compile_director(graph);assert '생성 완료' in str(result),str(result)
 return graph,stage,lengths
