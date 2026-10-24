import unreal as u,time,json,traceback,math
from pathlib import Path
P=Path(__file__).resolve().parent;OUT=P/'Preview';OUT.mkdir(exist_ok=True)
B='/Game/Constellation/Characters/Enemies/Slime_Liquid'
OLD='/Game/Constellation/Characters/Enemies/Slime_Normal/Animation'
level=u.get_editor_subsystem(u.LevelEditorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Review/Slime/L_Slime_Liquid')
state={'start':time.monotonic(),'phase':'boot','samples':[],'clips':[],'captures':[],'next_capture':0,'clip_index':0}
clips=[('Idle',B+'/AS_Slime_Liquid_Idle',8.05)]+[(n,OLD+'/AS_Slime_'+n,None) for n in ['Move','Attack','Damaged','Dead','Jump']]
def finish(ok,error=''):
 state['success']=ok;state['error']=error
 (P/'playback-report.json').write_text(json.dumps({k:v for k,v in state.items() if k not in ['comp','camera','world','capture','target']},indent=2))
 u.unregister_slate_post_tick_callback(handle);level.editor_request_end_play()
def begin_clip():
 name,path,duration=clips[state['clip_index']];anim=u.load_asset(path);assert anim
 state['comp'].play_animation(anim,name=='Idle')
 state['clip_start']=u.GameplayStatics.get_time_seconds(state['world']);state['clip_name']=name
 state['clip_duration']=duration or anim.get_play_length()+.1
 state['clip_capture']=False;state['last_sample']=0
 state['clips'].append({'name':name,'asset':path,'duration':anim.get_play_length(),'skeleton_matches':anim.get_editor_property('skeleton')==state['comp'].get_editor_property('skeletal_mesh_asset').get_editor_property('skeleton')})
 assert state['clips'][-1]['skeleton_matches']
def tick(dt):
 try:
  if time.monotonic()-state['start']>150:raise RuntimeError('Playback timeout')
  w=editor.get_game_world()
  if not w:return
  if state['phase']=='boot':
   found=[a for a in u.GameplayStatics.get_all_actors_of_class(w,u.SkeletalMeshActor) if a.get_actor_label()=='Liquid Slime']
   if not found:return
   state['world']=w;state['comp']=found[0].skeletal_mesh_component
   assert state['comp'].get_editor_property('skeletal_mesh_asset').get_path_name().startswith(B+'/SKM_Slime_Liquid.')
   state['camera']=next(a for a in u.GameplayStatics.get_all_actors_of_class(w,u.CameraActor) if a.get_actor_label()=='Slime Review Camera')
   state['capture']=next(a for a in u.GameplayStatics.get_all_actors_of_class(w,u.SceneCapture2D) if a.get_actor_label()=='Slime Review Capture').capture_component2d
   state['target']=u.RenderingLibrary.create_render_target2d(w,800,720,u.TextureRenderTargetFormat.RTF_RGBA8)
   state['capture'].texture_target=state['target']
   state['capture'].capture_scene()
   pc=u.GameplayStatics.get_player_controller(w,0);pc.set_view_target_with_blend(state['camera'],0)
   pawn=u.GameplayStatics.get_player_pawn(w,0)
   if pawn:pawn.set_actor_hidden_in_game(True);pawn.set_actor_enable_collision(False)
   state['phase']='playing';begin_clip();return
  elapsed=u.GameplayStatics.get_time_seconds(w)-state['clip_start'];c=state['comp']
  if elapsed-state['last_sample']>.04:
   state['last_sample']=elapsed
   poses={n:c.get_socket_location(n) for n in ['Root','Center','Top','drop','crest_tip','puddle_00']}
   assert all(math.isfinite(v) for p in poses.values() for v in [p.x,p.y,p.z])
   assert (poses['Top']-poses['Root']).length()<400
   state['samples'].append({'clip':state['clip_name'],'time':elapsed,'animation_position':c.get_position(),'positions':{n:[p.x,p.y,p.z] for n,p in poses.items()}})
  capture=False
  if state['clip_name']=='Idle' and elapsed>=state['next_capture'] and state['next_capture']<4.1:
   state['next_capture']+=.4;capture=True
  elif state['clip_name']!='Idle' and not state['clip_capture'] and elapsed>=state['clip_duration']*.5:
   state['clip_capture']=True;capture=True
  if capture:
   filename=f"play-{state['clip_name']}-{len(state['captures']):02d}.png"
   state['capture'].capture_scene()
   u.RenderingLibrary.export_render_target(w,state['target'],str(OUT),filename)
   state['captures'].append(filename)
  if elapsed>state['clip_duration']:
   state['clip_index']+=1
   if state['clip_index']>=len(clips):
    idle=[s for s in state['samples'] if s['clip']=='Idle']
    assert len(idle)>30,'Idle did not tick'
    assert max(s['positions']['drop'][2] for s in idle)-min(s['positions']['drop'][2] for s in idle)>90
    finish(True)
   else:begin_clip()
 except Exception:finish(False,traceback.format_exc())
handle=u.register_slate_post_tick_callback(tick)
level.editor_request_begin_play()
