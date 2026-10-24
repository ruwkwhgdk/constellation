"""Install approved jump storyboard. Scoped assets only; backup shared packages before edits."""
import unreal as u,json,shutil,traceback,math
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();O=R/'Saved/JumpAcquisition';O.mkdir(parents=True,exist_ok=True)
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool';PATH='/Game/SceneDirector/School/DA_JumpAcquisition'
def setp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
def backup(p,ext='.uasset'):
 src=R/'Content'/(p.removeprefix('/Game/')+ext);dst=O/'Backup'/(p.removeprefix('/Game/')+ext)
 if src.exists() and not dst.exists():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def camera_pose(p,target):
 v=u.Vector(*p);r=u.MathLibrary.find_look_at_rotation(v,u.Vector(*target));return u.Transform(location=v,rotation=r,scale=u.Vector(1,1,1))
try:
 backup(MAP,'.umap');world=u.EditorLoadingAndSavingUtils.load_map(MAP);assert world
 sub=u.get_editor_subsystem(u.EditorActorSubsystem);actors=list(sub.get_all_level_actors());star=next(a for a in actors if a.get_actor_label()=='star_object_jump')
 assert u.AbilityAcquisitionEditorLibrary.ensure_scene_interaction_component(star)
 stage=next((a for a in actors if isinstance(a,u.JumpAcquisitionStage)),None)
 if not stage:stage=sub.spawn_actor_from_class(u.JumpAcquisitionStage,star.get_actor_location())
 stage.set_actor_label('JumpAcquisition_Stage');stage.set_folder_path('Jump Acquisition')
 origin=star.get_actor_location();player=origin+u.Vector(-95,0,88)
 setp(stage,star=star,heroine_transform=u.Transform(location=player,rotation=u.Rotator(),scale=u.Vector(1,1,1)))
 folder='/Game/Constellation/VFX/JumpAcquisition';u.EditorAssetLibrary.make_directory(folder)
 mat=u.load_asset(folder+'/M_StarAbsorption')
 if not mat:
  mat=u.AssetToolsHelpers.get_asset_tools().create_asset('M_StarAbsorption',folder,u.Material,u.MaterialFactoryNew())
  mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
  color=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-200,0);color.set_editor_property('constant',u.LinearColor(5,2.8,.65,1))
  u.MaterialEditingLibrary.connect_material_property(color,'',u.MaterialProperty.MP_EMISSIVE_COLOR);u.MaterialEditingLibrary.recompile_material(mat)
  assert u.EditorAssetLibrary.save_loaded_asset(mat,False)
 mat.set_editor_property('used_with_instanced_static_meshes',True)
 u.MaterialEditingLibrary.recompile_material(mat);assert u.EditorAssetLibrary.save_loaded_asset(mat,False)
 setp(stage,particle_material=mat)
 bp_path='/Game/Constellation/Gameplay/Interaction/Actors/BP_Star_Object';backup(bp_path);bp=u.load_asset(bp_path)
 assert u.AbilityAcquisitionEditorLibrary.install_jump_interaction_route(bp) is not None
 assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
 a=u.load_asset(PATH)
 if not a:a=u.AssetToolsHelpers.get_asset_tools().create_asset('DA_JumpAcquisition','/Game/SceneDirector/School',u.SceneDirectorAsset,u.SceneDirectorFactory())
 else:backup(PATH)
 setp(a,event_key='JumpAcquisition',actions=[setp(u.DirectorActionEntry(),key='Jump',action_class=u.JumpAcquisitionAction)],objects=[setp(u.DirectorObjectEntry(),key='JumpStage',actor_class=u.JumpAcquisitionStage)],dialogue_character_interval=.06)
 # Coordinates relative to the existing room star. The actor faces +X; camera stays on its left (-Y).
 def worldp(p):return (origin.x+p[0],origin.y+p[1],origin.z+p[2])
 views={'A':camera_pose(worldp((200,-295,230)),worldp((-35,0,140))),
        'Inspect':camera_pose(worldp((165,-265,215)),worldp((-40,0,140))),
        'Hand':camera_pose(worldp((-60,-160,170)),worldp((-55,0,145))),
        'Face':camera_pose(worldp((-65,-140,183)),worldp((-90,0,150))),
        'Absorb':camera_pose(worldp((70,-260,205)),worldp((-60,0,135)))}
 setp(a,cameras=[setp(u.DirectorCameraEntry(),key='JumpCamera',transform=views['A'],field_of_view=48.)])
 N=u.DirectorNodeType;steps=[];labels={}
 def node(kind,label='',**kw):
  s=u.SceneDirectorLibrary.make_director_step(kind);setp(s,duration=.1,editor_position=u.Vector2D((len(steps)%9)*270,(len(steps)//9)*280));setp(s,**kw);steps.append(s);labels[str(s.id)]=label;return s
 def cue(name,t=0):return node(N.GAME_ACTION,name,action_key='Jump',action_parameters=setp(u.DirectorActionParameters(),identifier=name,value=float(t)))
 def wait(t):return node(N.WAIT,duration=float(t))
 def cam(name,t):
  x=views[name];rot=x.rotation.rotator()
  return node(N.CAMERA_MOVE,name,camera_key='JumpCamera',activate_camera=False,duration=float(t),destination=setp(u.DirectorVectorInput(),value=x.translation),rotation=setp(u.DirectorVectorInput(),value=u.Vector(rot.roll,rot.pitch,rot.yaw)))
 node(N.START);node(N.INPUT_LOCK,lock_input=True);node(N.HUD_HIDDEN,hide_hud=True);cue('Begin')
 # One continuous camera lease spans all pauses and the blocking UI/dialogue.
 shot=node(N.CAMERA_SWITCH,camera_key='JumpCamera',duration=.7,blend_seconds=.7,wait_for_completion=False);wait(2)
 cue('Inspect',2);cam('Inspect',2)
 cue('Reach',2.5);wait(2.5)
 cue('Contact',1);cam('Hand',.25);wait(.75)
 cue('Surprise',1.2);cam('Face',.35);wait(.85)
 cue('Absorb',2);cam('Absorb',2)
 cue('White',.6);wait(.6);cue('AbilityUI');wait(.1)
 cue('Chest',2);cam('A',.8);wait(1.2)
 cue('Palm',1.8);wait(1.8);cue('Release',1.2);wait(1.2)
 tablepath='/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData';backup(tablepath);table=u.load_asset(tablepath)
 rows=json.loads(u.DataTableFunctionLibrary.export_data_table_to_json_string(table));key='AbandonedSchool_JumpAcquisition_Obtained'
 text='알 수 없는 힘을 받은 당신은 점프 능력을 획득하였습니다.'
 if not any(r['Name']==key for r in rows):rows.append({'Name':key,'Description':text});assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table,json.dumps(rows,ensure_ascii=False));assert u.EditorAssetLibrary.save_loaded_asset(table,False)
 node(N.DIALOGUE,'Jump acquired narration',dialogue_row=setp(u.DataTableRowHandle(),data_table=table,row_name=key),dialogue_advance=u.DirectorDialogueAdvance.CLICK,duration=.6)
 node(N.CLOSE_DIALOGUE);node(N.CAMERA_RETURN,duration=1.0);cue('Commit');node(N.END)
 for s,n in zip(steps,steps[1:]):setp(s,next_nodes=[n.id])
 setp(a,steps=steps);result=u.SceneDirectorLibrary.compile_director(a);assert '생성 완료' in str(result),str(result)
 # This graph is sequential except for the continuous shot. Match 30fps quantization.
 timed={N.WAIT,N.CAMERA_MOVE,N.DIALOGUE}
 frames=sum(max(1,math.floor(s.get_editor_property('duration')*30+.50001)) for s in steps if s.get_editor_property('type') in timed)
 setp(shot,duration=frames/30.);setp(a,steps=steps)
 result=u.SceneDirectorLibrary.compile_director(a);assert '생성 완료' in str(result),str(result)
 assert u.EditorAssetLibrary.save_loaded_asset(a,False)
 b=next((x for x in actors if isinstance(x,u.SceneEventBinding) and x.get_editor_property('source')==star),None)
 if not b:b=sub.spawn_actor_from_class(u.SceneEventBinding,origin)
 b.set_actor_label('JumpAcquisition_Interaction');b.set_folder_path('Jump Acquisition')
 setp(b,source=star,director=a,trigger=u.SceneEventTrigger.INTERACTION,repeat=u.SceneEventRepeat.ONCE_PER_VISIT,origin=u.SceneEventOrigin.AUTHORED,objects={'JumpStage':stage})
 assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
 (O/'installed.json').write_text(json.dumps({'asset':PATH,'stage':stage.get_path_name(),'binding':b.get_path_name(),'star':star.get_path_name(),'steps':len(steps),'compile':str(result),'labels':labels},ensure_ascii=False,indent=2),encoding='utf8')
 (O/'install-error.txt').unlink(missing_ok=True)
 u.log('JUMP_INSTALLED')
except:(O/'install-error.txt').write_text(traceback.format_exc(),encoding='utf8');u.log_error(traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
