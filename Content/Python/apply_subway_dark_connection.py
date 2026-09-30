"""Targeted streaming tunnel patch. No PIE; preserve unrelated actors and back up maps."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,time,datetime,shutil,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'ArtSource/SubwayEntrance/Connection/v002';D='/Game/Constellation/Environments/SubwayEntrance'
E=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();M=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
EXT='/Game/Constellation/Worlds/StartIsland/Maps/L_StartIsland';INT='/Game/Constellation/Worlds/Stairwell/Maps/L_Stairwell_PlayScale2'
Env=u.load_class(None,'/Script/Constellation.SubwayTunnelEnvironment');assert Env
backup=R/'Saved/SubwayEntranceRecovery'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_dark');backup.mkdir(parents=True,exist_ok=True)
for package in [EXT,INT]:
 f=R/'Content'/(package.removeprefix('/Game/')+'.umap');shutil.copy2(f,backup/f.name)
report={'backup':str(backup),'play_tested':False,'maps':[]}
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
path=D+'/Materials/M_SE_TunnelDark';mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset('M_SE_TunnelDark',D+'/Materials',u.Material,u.MaterialFactoryNew())
M.delete_all_material_expressions(mat);n=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector);n.constant=u.LinearColor(.008,.011,.012,1);M.connect_material_property(n,'',u.MaterialProperty.MP_BASE_COLOR)
for prop,val in [(u.MaterialProperty.MP_ROUGHNESS,.97),(u.MaterialProperty.MP_SPECULAR,0)]:
 n=M.create_material_expression(mat,u.MaterialExpressionConstant);n.r=val;M.connect_material_property(n,'',prop)
M.recompile_material(mat);E.save_loaded_asset(mat)
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
p=opts.static_mesh_import_data;p.combine_meshes=True;p.auto_generate_collision=False;p.one_convex_hull_per_ucx=True;p.convert_scene_unit=True;p.transform_vertex_to_absolute=False;p.generate_lightmap_u_vs=True
manifest=load_current_json((O/'manifest.json').read_text());meshes={};checks=[]
for row in manifest['assets']:
 t=u.AssetImportTask();t.filename=str(O/'FBX'/(row['name']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.replace_existing=True;t.save=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t]);assert t.imported_object_paths
 mesh=E.load_asset(t.imported_object_paths[0]);meshes[row['name']]=mesh
 if row['name']!='SM_SE_IslandDarkTunnel':
  for i,slot in enumerate(mesh.get_editor_property('static_materials')):
   mp=D+'/Materials/M_SE_'+str(slot.material_slot_name);mm=E.load_asset(mp);assert mm,mp;mesh.set_material(i,mm)
 if row['hulls']==0:mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
 b=mesh.get_bounding_box();v=b.max-b.min;dims=[v.x,v.y,v.z];assert all(abs(x-y)<.3 for x,y in zip(dims,row['dimensions_cm'])),(row,dims)
 g=mesh.get_editor_property('body_setup').get_editor_property('agg_geom');hulls=sum(len(g.get_editor_property(p)) for p in ['convex_elems','box_elems','sphere_elems','sphyl_elems']);assert hulls==row['hulls'],(row,hulls)
 E.save_loaded_asset(mesh);checks.append(dict(name=row['name'],dimensions=dims,hulls=hulls))
report['imports']=checks

def actors():return {a.get_actor_label():a for a in A.get_all_level_actors()}
def snap():
 out={}
 for a in A.get_all_level_actors():
  p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
  out[a.get_actor_label()]=([p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z],a.static_mesh_component.static_mesh.get_path_name() if isinstance(a,u.StaticMeshActor) and a.static_mesh_component.static_mesh else '')
 return out
def spawn(cls,label,pos,rot=0):
 existing=actors().get(label)
 if existing:
  expected=cls.static_class() if isinstance(cls,type) else cls
  assert existing.get_class()==expected,(label,'unexpected existing class')
  return existing
 a=A.spawn_actor_from_class(cls,u.Vector(*pos),u.Rotator(pitch=0,yaw=rot,roll=0));a.set_actor_label(label);a.set_folder_path('SubwayEntrance/DarkConnection');return a
def meshactor(label,mesh,pos):
 a=spawn(u.StaticMeshActor,label,pos);a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_collision_profile_name('BlockAll');return a
def environment(label,pos,extent):
 a=spawn(Env,label,pos);a.get_editor_property('bounds').set_box_extent(u.Vector(*extent),False);return a
def travel(a,pos,yaw,arrival,arrivalyaw,maxfoot):
 a.set_actor_location_and_rotation(u.Vector(*pos),u.Rotator(pitch=0,yaw=yaw,roll=0),False,True)
 a.set_editor_property('arrival_transform',u.Transform(location=u.Vector(*arrival),rotation=u.Rotator(pitch=0,yaw=arrivalyaw,roll=0),scale=u.Vector(1,1,1)))
 a.set_editor_property('maximum_foot_height',maxfoot);a.set_editor_property('preload_distance',4000)
 a.get_editor_property('zone').set_box_extent(u.Vector(140,185,280),False)
 b=a.get_editor_property('safety_barrier');b.set_box_extent(u.Vector(12,210,160),False);b.set_relative_location(u.Vector(80,0,140),False,True)
 # Editor traces validate static floor without the runtime holding barrier.
 b.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
def globals_tag(d,names):
 for name in names:
  a=d[name];tags=list(a.tags)
  if 'SE_GlobalEnvironment' not in [str(t) for t in tags]:tags.append('SE_GlobalEnvironment')
  a.tags=tags

def patch(which):
 assert L.load_level(which);d=actors()
 if 'SE_DarkTunnel' in d:
  expected='SM_SE_ExteriorDarkTunnel' if which==EXT else 'SM_SE_InteriorDarkTunnel'
  assert d['SE_DarkTunnel'].static_mesh_component.static_mesh==meshes[expected],'Conflicting tunnel revision'
 old=snap()
 if which==EXT:
  d['SE_E09'].static_mesh_component.set_static_mesh(meshes['SM_SE_E09_DarkEntry']);d['sky_island'].static_mesh_component.set_static_mesh(meshes['SM_SE_IslandDarkTunnel'])
  meshactor('SE_DarkTunnel',meshes['SM_SE_ExteriorDarkTunnel'],(3900,-19500,10000))
  travel(d['SE_TravelToInterior'],(4700,-20500,9640),0,(-1500,-800,360),90,9670)
  environment('SE_DarkExposure',(4540,-20500,9780),(510,210,145))
  globals_tag(d,['SunSky','PostProcessVolume'])
  changed={'SE_E09','sky_island','SE_TravelToInterior'}
  samples=[(3900,-19770,9760),(3900,-20065,9700),(3900,-20500,9640),(4700,-20500,9640),(4200,-19520,10000),(3900,-18800,10000),(4700,-20500,10000)]
 else:
  meshactor('SE_DarkTunnel',meshes['SM_SE_InteriorDarkTunnel'],(0,0,0))
  travel(d['SE_TravelToExterior'],(-1500,-800,360),-90,(4700,-20500,9640),180,390)
  environment('SE_DarkExposure',(-1500,-710,500),(210,520,145))
  globals_tag(d,['SWScene_Exposure'])
  changed={'SE_TravelToExterior'};samples=[(-720,0,360),(-950,0,360),(-1500,0,360),(-1500,-400,360),(-1500,-800,360)]
 new=snap()
 for name,v in old.items():
  if name not in changed:assert new[name]==v,('Unrelated actor changed',name)
 return which,samples,len(old)-len(changed)

state=patch(EXT);started=time.time();phase=0;busy=False
u.EditorPythonScripting.set_keep_python_script_alive(True)
def tick(dt):
 global started,state,phase,busy
 if busy or time.time()-started<10:return
 busy=True
 try:
  which,samples,count=state;w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();traces=[]
  for x,y,z in samples:
   h=u.SystemLibrary.line_trace_single(w,u.Vector(x,y,z+60),u.Vector(x,y,z-120),u.TraceTypeQuery.ECC_VISIBILITY,False,[],u.DrawDebugTrace.NONE,True)
   got=h.to_tuple()[4].z if h else None;assert got is not None and abs(got-z)<4,(which,x,y,z,got)
   traces.append(dict(x=x,y=y,expected=z,actual=got))
  assert u.EditorLoadingAndSavingUtils.save_map(w,which);report['maps'].append(dict(map=which,unrelated_actors_preserved=count,traces=traces))
  if phase==0:
   phase=1;state=patch(INT);started=time.time();busy=False;return
  (O/'applied.json').write_text(json.dumps(report,indent=2));u.log('SUBWAY_DARK_CONNECTION_APPLIED');u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
 except Exception:
  u.log_error(traceback.format_exc());(O/'apply_failure.txt').write_text(traceback.format_exc());u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
