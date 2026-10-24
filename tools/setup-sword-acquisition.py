"""Install the approved functional sword event; animation cues remain pending."""
import unreal as u,json,shutil,traceback,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/SwordAcquisition/IntegrationInstall';O.mkdir(parents=True,exist_ok=True)
backup_root=O/('Backup-'+time.strftime('%Y%m%d-%H%M%S'))
MAP='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool';PATH='/Game/SceneDirector/School/DA_SwordAcquisition'
def prop(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
def backup(p,ext='.uasset'):
 src=R/'Content'/(p.removeprefix('/Game/')+ext)
 if src.exists():
  dst=backup_root/(p.removeprefix('/Game/')+ext);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
def pose(loc,target):
 v=u.Vector(*loc);return u.Transform(location=v,rotation=u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)))
try:
 backup(MAP,'.umap');world=u.EditorLoadingAndSavingUtils.load_map(MAP);assert world
 A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=list(A.get_all_level_actors())
 sword=next(a for a in actors if a.get_name()=='BP_Sword_Stuck_At_Ground_C_1')
 stage=next((a for a in actors if isinstance(a,u.SwordAcquisitionStage)),None)
 if not stage:stage=A.spawn_actor_from_class(u.SwordAcquisitionStage,sword.get_actor_location())
 stage.set_actor_label('SwordAcquisition_Stage');stage.set_folder_path('Sword Acquisition')
 icon=u.load_asset('/Game/Constellation/UI/ItemAcquisition/T_RustySword');assert icon,'Rendered sword icon missing'
 definition_path='/Game/Constellation/UI/ItemAcquisition/DA_RustySword';backup(definition_path);definition=u.load_asset(definition_path)
 if not definition:
  factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',u.ItemAcquisitionDefinition);definition=u.AssetToolsHelpers.get_asset_tools().create_asset('DA_RustySword','/Game/Constellation/UI/ItemAcquisition',u.ItemAcquisitionDefinition,factory)
 prop(definition,presentation=prop(u.ItemAcquisitionPresentation(),item_id='RustySword',sprite=icon,name='녹슨 검',description='오랫동안 바닥에 꽂혀 있던 녹슨 검.',quantity=1))
 assert u.EditorAssetLibrary.save_loaded_asset(definition,False)
 prop(stage,sword=sword,heroine_transform=u.Transform(location=u.Vector(-10810,0,890.2),rotation=u.Rotator(yaw=180)),item_definition=definition)
 bp_path='/Game/Constellation/Gameplay/Interaction/Actors/BP_Sword_Pickup';backup(bp_path);bp=u.load_asset(bp_path)
 # Existing helper routes Interact generically and preserves the legacy fallback for unbound instances.
 route=u.AbilityAcquisitionEditorLibrary.install_jump_interaction_route(bp)
 (O/'route-api.txt').write_text(str(u.AbilityAcquisitionEditorLibrary.install_jump_interaction_route.__doc__)+'\nResult type='+str(type(route))+' value='+repr(route)+'\nFailure value='+repr(u.AbilityAcquisitionEditorLibrary.install_jump_interaction_route(None)),encoding='utf8')
 assert route is not None and route is not False,repr(route)
 assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
 assert u.AbilityAcquisitionEditorLibrary.ensure_scene_interaction_component(sword)
 removed=[]
 for c in sword.get_components_by_class(u.StaticMeshComponent):
  if c.static_mesh and 'Star_Object' in c.static_mesh.get_path_name():
   removed.append(c.get_name());c.set_static_mesh(None);c.set_visibility(False,True);c.set_hidden_in_game(True,True)
 backup(PATH);graph=u.load_asset(PATH)
 if not graph:graph=u.AssetToolsHelpers.get_asset_tools().create_asset('DA_SwordAcquisition','/Game/SceneDirector/School',u.SceneDirectorAsset,u.SceneDirectorFactory())
 prop(graph,event_key='SwordAcquisition',actions=[prop(u.DirectorActionEntry(),key='Sword',action_class=u.SwordAcquisitionAction)],objects=[prop(u.DirectorObjectEntry(),key='SwordStage',actor_class=u.SwordAcquisitionStage)],dialogue_character_interval=.04)
 foot=802.2
 views={'A':pose((-10490,-350,foot+220),(-10865,0,foot+85)),'B':pose((-11160,-310,foot+170),(-10865,0,foot+85)),'C':pose((-11170,-360,foot+160),(-10845,0,foot+150))}
 prop(graph,cameras=[prop(u.DirectorCameraEntry(),key=k,transform=v,field_of_view=48.) for k,v in views.items()])
 N=u.DirectorNodeType;steps=[]
 def node(kind,**kw):
  s=u.SceneDirectorLibrary.make_director_step(kind);prop(s,duration=.1,editor_position=u.Vector2D((len(steps)%8)*260,(len(steps)//8)*260));prop(s,**kw);steps.append(s);return s
 def cue(name):return node(N.GAME_ACTION,action_key='Sword',action_parameters=prop(u.DirectorActionParameters(),identifier=name))
 def wait(t):return node(N.WAIT,duration=float(t))
 def shot(k,t):return node(N.CAMERA_SWITCH,camera_key=k,duration=float(t),blend_seconds=.6,wait_for_completion=False)
 node(N.START);node(N.INPUT_LOCK,lock_input=True);node(N.HUD_HIDDEN,hide_hud=True);cue('Begin')
 shot('A',3);wait(3);shot('B',6);cue('Grip');wait(3)
 q=node(N.QTE,qte=prop(u.DirectorQTESettings(),type=u.DirectorQTEType.DIRECTION_DRAG,timed=False,drag_direction=u.Vector2D(0,-1),drag_distance=160.,screen_position=u.Vector2D(.78,.72),scene_policy=u.DirectorQTEScenePolicy.HOLD))
 after=cue('Pull');wait(3);shot('C',12);cue('RaiseHold');wait(3);cue('ItemUI');wait(.1);cue('Lower');wait(2)
 node(N.DIALOGUE,dialogue_text='녹슨 검을 얻었습니다.',dialogue_advance=u.DirectorDialogueAdvance.CLICK,duration=3.)
 node(N.CLOSE_DIALOGUE);cue('Commit');node(N.CAMERA_RETURN,duration=1.);node(N.END)
 for a,b in zip(steps,steps[1:]):a.set_editor_property('next_nodes',[b.id])
 q.set_editor_property('next_nodes',[]);q.set_editor_property('choice_targets',{u.Name('Success'):after.id,u.Name('Failure'):after.id})
 prop(graph,steps=steps);compiled=u.SceneDirectorLibrary.compile_director(graph);assert not graph.get_editor_property('needs_compile'),str(compiled)
 assert u.EditorAssetLibrary.save_loaded_asset(graph,False)
 binding=next((a for a in actors if isinstance(a,u.SceneEventBinding) and a.get_editor_property('source')==sword and a.get_editor_property('trigger')==u.SceneEventTrigger.INTERACTION),None)
 if not binding:binding=A.spawn_actor_from_class(u.SceneEventBinding,sword.get_actor_location())
 binding.set_actor_label('SwordAcquisition_Interaction');binding.set_folder_path('Sword Acquisition')
 prop(binding,source=sword,director=graph,trigger=u.SceneEventTrigger.INTERACTION,repeat=u.SceneEventRepeat.ONCE_PER_VISIT,origin=u.SceneEventOrigin.AUTHORED,objects={'SwordStage':stage})
 assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
 (O/'result.json').write_text(json.dumps({'graph':PATH,'removed_star_mesh_components':removed,'backup':str(backup_root),'animation':'pending','compiled':str(compiled)},ensure_ascii=False,indent=2),encoding='utf8')
except:(O/'error.txt').write_text(traceback.format_exc(),encoding='utf8');u.log_error(traceback.format_exc())
finally:
 if '-SwordReview' in u.SystemLibrary.get_command_line():exec((R/'tools/review-sword-integration.py').read_text(encoding='utf8'),{'__name__':'__main__'})
 else:u.SystemLibrary.quit_editor()
