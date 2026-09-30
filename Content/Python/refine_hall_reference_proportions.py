"""v024: reference elevation proportions, side cross-members and directed light."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v024';OUT.mkdir(parents=True,exist_ok=True);D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
if not (OUT/'baseline.json').exists():
    rows={}
    for n,a in actors.items():
        p=a.get_actor_location();s=a.get_actor_scale3d();r=a.get_actor_rotation();rows[n]=dict(position=[p.x,p.y,p.z],scale=[s.x,s.y,s.z],rotation=[r.pitch,r.yaw,r.roll])
        if isinstance(a,u.StaticMeshActor):rows[n].update(mesh=a.static_mesh_component.static_mesh.get_path_name() if a.static_mesh_component.static_mesh else None,materials=[a.static_mesh_component.get_material(i).get_path_name() if a.static_mesh_component.get_material(i) else None for i in range(a.static_mesh_component.get_num_materials())])
    (OUT/'baseline.json').write_text(json.dumps(rows,indent=2))
base=load_current_json((OUT/'baseline.json').read_text());changed=[]
for n,a in actors.items():
    if n.startswith('OH_ReferenceProportion_'):A.destroy_actor(a)
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
def transform(n,pos=None,scale=None,rotation=None):
    a=actors[n];a.modify()
    if pos:a.set_actor_location(u.Vector(*pos),False,False)
    if scale:a.set_actor_scale3d(u.Vector(*scale))
    if rotation:a.set_actor_rotation(u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]),False)
    if n not in changed:changed.append(n)
    return a
# Four slots retained, but the first is a narrow partially occluded bay; other three are broad.
boundaries=[610,477,158,-151,-498];windows=[]
for i,ids in enumerate([('0301','0302','0303'),('0305','0306','0307'),('0309','0310','0311'),('0313','0314','0315')]):
    left,right=boundaries[i:i+2];center=(left+right)/2;clear=left-right-26.2
    for j,suffix in enumerate(ids):
        n=('OH_FULL_07_' if j==2 else 'OH_FULL_06_')+suffix;a=actors[n];mesh=a.static_mesh_component.static_mesh;box=mesh.get_bounding_box();size=box.max-box.min;s=base[n]['scale'].copy();s[0]=clear/size.x;p=base[n]['position'].copy();p[0]=center
        if j==0:p[2]=315;s[2]=360/size.z
        if j==1:p[2]=825;s[2]=145/size.z
        transform(n,p,s);windows.append(dict(label=n,center_x=center,width_cm=clear,base_z=p[2]))
for i,x in enumerate(boundaries):
    for j in range(3):
        n='OH_FULL_02_%04d'%(239+i*3+j);p=base[n]['position'].copy();p[0]=x;transform(n,p)
# Thicker solid band between lower windows and the upper arcade, same upper edge.
for k in range(235,239):
    n='OH_FULL_09_%04d'%k;mesh=actors[n].static_mesh_component.static_mesh;box=mesh.get_bounding_box();s=base[n]['scale'].copy();s[2]=150/(box.max.z-box.min.z);p=base[n]['position'].copy();p[2]=675;transform(n,p,s)
n='OH_FULL_05_0277';p=base[n]['position'].copy();p[0]=555;s=base[n]['scale'].copy();s[0]*=65/145;transform(n,p,s)
# Mid-height cross-members visible in the reference; reuse existing Tripo broken beams.
members=[]
for n,side,y,z,pitch in [('OH_FULL_11_0285',1,1000,420,-12),('OH_FULL_11_0286',1,1400,400,-7),('OH_FULL_11_0296',-1,1000,435,15),('OH_FULL_11_0297',-1,1400,415,10)]:
    a=actors[n];s=base[n]['scale'].copy();s[0]*=2.35;center=u.Vector(side*635,y,z);transform(n,[center.x,center.y,center.z],s,[pitch,-90,0]);actual,_=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+center-actual,False,False);members.append(n)
mesh=E.load_asset(D+'/FoliageRuntime/SM_OH_PaintedCrown_Runtime');mat=E.load_asset(D+'/AtmosphereFinish/M_OH_LeafColorMass');box=mesh.get_bounding_box();size=box.max-box.min;added=[]
for i,n in enumerate(members):
    center,extent=actors[n].get_actor_bounds(False);target=center+u.Vector(0,25,extent.z*.6);a=A.spawn_actor_from_class(u.StaticMeshActor,target,u.Rotator());a.set_actor_label('OH_ReferenceProportion_BeamLeaves_%02d'%i);c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,mat);a.set_actor_scale3d(u.Vector(65/size.x,(210 if i%2==0 else 155)/size.y,80/size.z));actual,_=a.get_actor_bounds(False);a.set_actor_location(a.get_actor_location()+target-actual,False,False);c.set_collision_profile_name('NoCollision');c.set_cast_shadow(False);added.append(a.get_actor_label())
# The reference has a substantial upper side wall, not sky above every broken arch.
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0');infill=[]
for row in load_current_json((OUT/'upper_wall_assets.json').read_text()):
    opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
    t=u.AssetImportTask();t.filename=str(OUT/(row['mesh']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);m=E.load_asset(t.imported_object_paths[0]);m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);assert E.save_loaded_asset(m,only_if_is_dirty=False);infill.append(m)
for side in [-1,1]:
    for i,y in enumerate([400,800,1200,1600]):
        a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(side*652,y,450),u.Rotator(pitch=0,yaw=-90,roll=0));a.set_actor_label('OH_ReferenceProportion_UpperWall_%s_%d'%(side,i));c=a.static_mesh_component;c.set_static_mesh(infill[(i+(side>0))%2]);a.set_actor_scale3d(u.Vector(1,1,690/440));c.set_material(0,E.load_asset(D+'/AtmosphereFinish/M_OH_SlateArch'));c.set_collision_profile_name('BlockAll');added.append(a.get_actor_label())
light=actors['OH_Finish_FocalSun'];light.modify();p=u.Vector(-440,1850,1000);light.set_actor_location(p,False,False);light.set_actor_rotation(u.MathLibrary.find_look_at_rotation(p,u.Vector(0,1050,0)),False);changed.append('OH_Finish_FocalSun');c=light.get_component_by_class(u.SpotLightComponent)
for k,v in [('intensity',2800000),('inner_cone_angle',7),('outer_cone_angle',10.5),('volumetric_scattering_intensity',5)]:c.set_editor_property(k,v)
fog=actors['OH_ReferenceFog'];fog.modify();fog.get_component_by_class(u.ExponentialHeightFogComponent).set_editor_property('fog_density',.018)
assert L.save_current_level();(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,changed=changed,added=added,windows=windows,boundaries_cm=boundaries,side_members=members,playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_reference_proportions.py'))
