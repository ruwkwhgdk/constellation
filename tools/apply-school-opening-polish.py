"""S0 14.5s wake, six atlas-backed paper props, furniture-clear approach path."""
import unreal as u,json,shutil,time,math
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();out=R/'Saved/WakeVision/Polish-20261011';out.mkdir(parents=True,exist_ok=True)
for rel in ['Content/SceneDirector/School/DA_S0_Opening.uasset','Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap']:
 p=R/rel;b=out/p.name
 if not b.exists():shutil.copy2(p,b)
P=lambda o,k:o.get_editor_property(k)
def setp(o,**kw):
 for k,v in kw.items():o.set_editor_property(k,v)
 return o
A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
aa=A.get_all_level_actors();by={x.get_actor_label():x for x in aa}
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');steps=list(P(a,'steps'));N=u.DirectorNodeType
key=lambda g:tuple(P(g,k) for k in ('a','b','c','d'))
def nxt(s):return next(x for x in steps if key(P(x,'id'))==key(P(s,'next_nodes')[0]))
eye=next(x for x in steps if P(x,'type')==N.EYELIDS)
setp(eye,eye_start_hold=1.,eye_final_seconds=.5,eye_final_hold=2.,vision_curve=u.DirectorVisionCurve.SMOOTH)
blinks=list(P(eye,'blinks'));assert len(blinks)==2
for b,amount,hold in zip(blinks,[.25,.55],[.5,1.5]):setp(b,open_amount=amount,open_seconds=2.,open_hold=1.,close_seconds=1.5,closed_hold=hold)
setp(eye,blinks=blinks)
vis=nxt(eye)
for duration,blur0,blur1,haze0,haze1 in [(5.5,.85,.85,.22,.22),(.5,.85,.25,.22,.06),(4.5,.25,.25,.06,.06),(1.5,.25,0,.06,0),(2.5,0,0,0,0)]:
 assert P(vis,'type')==N.VISION;setp(vis,duration=duration,blur_from=blur0,blur_to=blur1,haze_from=haze0,haze_to=haze1);vis=nxt(vis)
assert P(vis,'type')==N.HUB
# Start outside the desk rows; approach across their near edge, then turn toward the locker.
start=(2320,1100,67);path1=[(0,start,180),(2.5,(2320,500,67),180)]
path2=[(0,(2320,500,67),180),(.2,(2350,500,67),-90),(1.1,(2580,500,67),-90),(1.3,(2615,455,67),-161.2),(3.3,(2770,0,67),-161.2),(3.5,(2790,0,67),-90),(4.3,(3010,0,67),-90)]
girl=by['S0_LittleGirl_Blocking'];girl.set_actor_location(u.Vector(*start),False,True);girl.set_actor_rotation(u.Rotator(yaw=180),False)
for s in steps:
 if P(s,'type')==N.BIND_NPC and str(P(s,'role'))=='Girl':setp(s,transform=girl.get_actor_transform())
moves=[s for s in steps if P(s,'type')==N.CHARACTER_MOVE]
assert len(moves)>=2
for s,path in zip(moves[:2],[path1,path2]):
 pts=[]
 for t,p,yaw in path:pts.append(setp(u.DirectorMotionPoint(),time=t,position=u.Vector(*p),rotation=u.Vector(0,0,yaw),scale=u.Vector(.7,.7,.7),interpolation=u.DirectorPathInterpolation.LINEAR))
 d=P(s,'destination');setp(d,value=u.Vector(*path[-1][1]));setp(s,use_motion_path=True,motion_points=pts,duration=path[-1][0],destination=d)
# Conservative horizontal bounding circles include hands and garment; check every 2 cm of travel.
furniture=[]
for actor in aa:
 if any(c.static_mesh and any(k in c.static_mesh.get_path_name().lower() for k in ('desk','chair','table')) for c in actor.get_components_by_class(u.StaticMeshComponent)):
  o,e=actor.get_actor_bounds(False)
  if o.z-e.z<140 and o.z+e.z>0:furniture.append((actor.get_actor_label(),o,e))
minimum=1e9;nearest=''
for path in [path1,path2]:
 for (_,p,_),(_,q,_) in zip(path,path[1:]):
  n=max(2,int(math.dist(p,q)/2))
  for i in range(n+1):
   x=p[0]+(q[0]-p[0])*i/n;y=p[1]+(q[1]-p[1])*i/n
   for label,o,e in furniture:
    distance=math.hypot(max(abs(x-o.x)-e.x,0),max(abs(y-o.y)-e.y,0))
    if distance<minimum:minimum=distance;nearest=label
assert minimum>65,('Approach intersects furniture safety radius',minimum,nearest)
D='/Game/SceneDirector/School/S0/Decor';source=R/'ArtSource/SchoolOpening/Decor'
def imp(name,mesh=False):
 task=setp(u.AssetImportTask(),filename=str(source/name),destination_path=D,automated=True,save=True,replace_existing=True)
 if mesh:
  opts=setp(u.FbxImportUI(),import_mesh=True,import_as_skeletal=False,import_materials=False,import_textures=False,mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH)
  setp(opts.static_mesh_import_data,combine_meshes=True,auto_generate_collision=False);setp(task,options=opts,factory=u.FbxFactory())
 AT.import_asset_tasks([task]);assert task.imported_object_paths;return E.load_asset(task.imported_object_paths[0])
atlas=imp('T_LockerScrapbookAtlas.png');setp(atlas,never_stream=True);E.save_loaded_asset(atlas,False)
textures={n:imp(n+'.png') for n in ['T_PaperRoughness','T_PaperMetallic']}
for tex in textures.values():setp(tex,srgb=False,compression_settings=u.TextureCompressionSettings.TC_MASKS);E.save_loaded_asset(tex,False)
mi=E.load_asset(D+'/MI_ScrapbookPaper') if E.does_asset_exist(D+'/MI_ScrapbookPaper') else AT.create_asset('MI_ScrapbookPaper',D,u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew())
M.set_material_instance_parent(mi,u.load_asset('/Game/Constellation/MaterialLibrary/Materials/M_Base_PBR'))
for param,tex in [('BaseColor',atlas),('Roughness',textures['T_PaperRoughness']),('Metalic',textures['T_PaperMetallic']),('Normal',u.load_asset('/Engine/EngineMaterials/DefaultNormal'))]:M.set_material_instance_texture_parameter_value(mi,param,tex)
setp(mi,base_property_overrides=setp(u.MaterialInstanceBasePropertyOverrides(),override_two_sided=True,two_sided=True))
M.update_material_instance(mi);E.save_loaded_asset(mi,False)
layout=[('MoonPhoto',24,236,.13,-6),('SaturnPhoto',-4,238,.14,7),('NebulaPhoto',-30,201,.13,-8),('MoonSticker',51,247,.075,12),('StarSticker',24,201,.075,-10),('PlanetSticker',-22,253,.08,8)]
for name,y,z,size,tilt in layout:
 mesh=imp('SM_S0_'+name+'.fbx',True);mesh.set_material(0,mi);E.save_loaded_asset(mesh,False)
 label='S0_Decor_'+name;actor=by.get(label) or A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(3154.3,y,z),u.Rotator(pitch=tilt,yaw=-90,roll=90))
 actor.set_actor_label(label);actor.set_folder_path('S0 Opening/Props');actor.static_mesh_component.set_mobility(u.ComponentMobility.MOVABLE);actor.static_mesh_component.set_static_mesh(mesh)
 actor.set_actor_location(u.Vector(3154.3,y,z),False,True);actor.set_actor_rotation(u.Rotator(pitch=tilt,yaw=-90,roll=90),False);actor.set_actor_scale3d(u.Vector(size,size,1));actor.set_actor_enable_collision(False)
 actor.attach_to_actor(by['S0_LockerDoor'],'',u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,u.AttachmentRule.KEEP_WORLD,False)
setp(a,steps=steps);result=u.SceneDirectorLibrary.compile_director(a);assert result is not None,str(result);assert E.save_loaded_asset(a,False)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(out/'applied.json').write_text(json.dumps(dict(wake_seconds=14.5,props=6,approach_minimum_aabb_distance=minimum,nearest_furniture=nearest,character_clearance_radius=65,paths=[path1,path2],compile=str(result)),ensure_ascii=False,indent=2),encoding='utf8');u.log('S0_POLISH_APPLIED '+str(result))
u.EditorPythonScripting.set_keep_python_script_alive(True);start_time=time.monotonic()
def finish(dt):
 if time.monotonic()-start_time>4:u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(finish)
