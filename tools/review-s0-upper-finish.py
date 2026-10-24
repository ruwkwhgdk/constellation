import unreal as u,time,json,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/UpperFinish_20261018';O.mkdir(parents=True,exist_ok=True)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
rows=[];lights=[]
for a in A.get_all_level_actors():
 p=a.get_actor_location()
 row=dict(name=a.get_name(),label=a.get_actor_label(),transform=str(a.get_actor_transform()),collision=a.get_actor_enable_collision(),meshes=[])
 for c in a.get_components_by_class(u.StaticMeshComponent):
  row['meshes'].append(dict(name=c.get_name(),mesh=c.static_mesh.get_path_name() if c.static_mesh else '',materials=[m.get_path_name() if m else '' for m in c.get_materials()]))
 rows.append(row)
 if -1500<p.x<4500 and -4000<p.y<4000:
  for c in a.get_components_by_class(u.LightComponent):
   vals={}
   for k in ['intensity','light_color','attenuation_radius','intensity_units','use_inverse_squared_falloff','cast_shadows','source_radius','inner_cone_angle','outer_cone_angle','mobility']:
    try:vals[k]=str(c.get_editor_property(k))
    except:pass
   lights.append(dict(label=a.get_actor_label(),pos=str(p),rotation=str(a.get_actor_rotation()),values=vals))
pc=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='S0_WetFloor_PlanarReflection').get_component_by_class(u.PlanarReflectionComponent)
(O/'reflection-settings.json').write_text(json.dumps({'screen_percentage':pc.get_editor_property('screen_percentage'),'flags':[{'name':f.show_flag_name,'enabled':f.enabled} for f in pc.get_editor_property('show_flag_settings')]},indent=2))
cmd=u.SystemLibrary.get_command_line();tag='baseline'
for t in ['art1','final']:
 if '-Polish'+t in cmd:tag=t
(O/(tag+'-actors.json')).write_text(json.dumps(rows,indent=2))
(O/(tag+'-lights.json')).write_text(json.dumps(lights,indent=2))
if tag=='final':
 material_report={}
 for name in ['M_S0_WoodCaveFloor_V3','M_S0_ShallowWater_V3','M_S0_ArtPlaster','M_S0_ArtRock','M_S0_CoolWindow','M_S0_WoodCaveFloor_V7','M_S0_ShallowWater_V7','M_S0_Plaster_V9','M_S0_Rock_V9']:
  mat=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/'+name)
  material_report[name]={'shading_model':str(mat.get_editor_property('shading_model')),'blend_mode':str(mat.get_editor_property('blend_mode')),'expression_count':u.MaterialEditingLibrary.get_num_material_expressions(mat),'water_outputs':sum(isinstance(n,u.MaterialExpressionSingleLayerWaterMaterialOutput) for n in u.MaterialEditingLibrary.get_material_expressions(mat))}
 (O/'final-materials.json').write_text(json.dumps(material_report,indent=2))
 local_report={}
 for a in A.get_all_level_actors():
  if a.get_actor_label() not in ['S0_WetFloor_ShallowWater','S0_WetFloor_PlanarReflection','S0_WetFloor_ReflectionVolume']:continue
  record={'bounds':str(a.get_actor_bounds(False)),'components':[]}
  for c in a.get_components_by_class(u.ActorComponent):
   values={}
   for k in ['collision_enabled','box_extent','unbound','priority','screen_percentage','normal_distortion_strength','prefilter_roughness']:
    try:values[k]=str(c.get_editor_property(k))
    except:pass
   if isinstance(c,u.PostProcessComponent):
    settings=c.get_editor_property('settings')
    for k in ['reflection_method','override_reflection_method','screen_space_reflection_quality','override_lumen_scene_detail','override_lumen_reflection_quality']:
     try:values[k]=str(settings.get_editor_property(k))
     except:pass
   if values:record['components'].append({'name':c.get_name(),'values':values})
  local_report[a.get_actor_label()]=record
 (O/'final-local-settings.json').write_text(json.dumps(local_report,indent=2))
cam=A.spawn_actor_from_class(u.CameraActor,u.Vector(3050,2550,1600),u.Rotator(pitch=-25,yaw=-130),transient=True)
cam.camera_component.set_field_of_view(83)
u.EditorLevelLibrary.pilot_level_actor(cam);u.EditorLevelLibrary.editor_set_game_view(True)
u.EditorPythonScripting.set_keep_python_script_alive(True)
S={'t':time.monotonic(),'i':0,'sent':False,'busy':False}
shots=[('concept',(2900,900,700),(-20,-138)),('floor',(2600,0,180),(-8,180)),('reverse',(3050,-2650,1650),(-25,130))]
if tag=='final':shots.append(('upper-route',(1400,-2300,900),(-10,180)))
def tick(dt):
 if S['busy']:return
 S['busy']=True
 try:
  if S['i']>=len(shots):
   if '-PolishHold' in cmd:
    command=O/'control.py'
    if command.exists():
     code=command.read_text(encoding='utf8');command.rename(O/('executed-'+str(time.time_ns())+'.py'));exec(code,globals())
    return
   u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
  name,p,r=shots[S['i']];path=O/(tag+'-'+name+'.png')
  if S['sent'] and path.exists() and path.stat().st_size>0 and path.stat().st_mtime_ns!=S.get('previous_mtime'):S.update(i=S['i']+1,sent=False,t=time.monotonic());return
  if time.monotonic()-S['t']>240:raise RuntimeError('Capture timeout')
  if not S['sent']:
   cam.set_actor_location(u.Vector(*p),False,True);cam.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1]),False)
   if time.monotonic()-S['t']>25:
    S['previous_mtime']=path.stat().st_mtime_ns if path.exists() else None
    S['sent']=True;u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=cam,delay=1)
 except Exception:
  (O/(tag+'-capture-error.txt')).write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 finally:S['busy']=False
handle=u.register_slate_post_tick_callback(tick)



