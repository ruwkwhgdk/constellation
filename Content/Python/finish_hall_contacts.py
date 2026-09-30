"""v017 bounded contact pass: attach leaf clusters and soften bench slab outline."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,math,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v017';D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
assert L.load_level(MAP);actors={a.get_actor_label():a for a in A.get_all_level_actors()}
names=[n for n in actors if n.startswith('OH_Painterly_WallLeaves_')]
if not (OUT/'baseline.json').exists():
    record={}
    for n in names+['OH_FULL_13_0276']:
        a=actors[n];p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
        record[n]=dict(position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z],mesh=a.static_mesh_component.static_mesh.get_path_name())
    (OUT/'baseline.json').write_text(json.dumps(record,indent=2))
base=load_current_json((OUT/'baseline.json').read_text());contacts=[]
columns=[a for n,a in actors.items() if n.startswith('OH_FULL_02_')]
assert columns and len(names)==13
def clamp(x,a,b):return max(a,min(b,x))
for n in sorted(names):
    leaf=actors[n];p=base[n]['position'];side=abs(p[0])>580;sign=1 if p[0]>0 else -1;candidates=[]
    for column in columns:
        center,ext=column.get_actor_bounds(False)
        if not center.z-ext.z-10<=p[2]<=center.z+ext.z+10:continue
        if side:
            if center.x*sign<450:continue
            face=u.Vector(center.x-sign*ext.x,clamp(p[1],center.y-ext.y+2,center.y+ext.y-2),clamp(p[2],center.z-ext.z+2,center.z+ext.z-2));normal=u.Vector(-sign,0,0)
        else:
            if center.y<1800:continue
            face=u.Vector(clamp(p[0],center.x-ext.x+2,center.x+ext.x-2),center.y-ext.y,clamp(p[2],center.z-ext.z+2,center.z+ext.z-2));normal=u.Vector(0,-1,0)
        distance=sum((v-w)**2 for v,w in zip([face.x,face.y,face.z],p));candidates.append((distance,column,face,normal))
    assert candidates,n
    _,parent,face,normal=min(candidates,key=lambda row:row[0]);leaf.modify();leaf.set_actor_rotation(u.Rotator(),False)
    center,ext=leaf.get_actor_bounds(False);thickness=ext.x if side else ext.y;target=face+normal*(thickness*.55)
    leaf.set_actor_location(leaf.get_actor_location()+target-center,False,False)
    q=leaf.get_actor_location();contacts.append(dict(label=n,parent=parent.get_actor_label(),position=[q.x,q.y,q.z],center=[target.x,target.y,target.z]))
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True;opts.static_mesh_import_data.normal_import_method=u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
t=u.AssetImportTask();t.filename=str(OUT/'SM_OH_BenchShoreFinish.fbx');t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t]);mesh=E.load_asset(t.imported_object_paths[0]);assert mesh
slab=actors['OH_FULL_13_0276'];slab.modify();material=slab.static_mesh_component.get_material(0);mesh.set_material(0,material);mesh.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);assert E.save_loaded_asset(mesh,only_if_is_dirty=False)
slab.static_mesh_component.set_static_mesh(mesh);slab.static_mesh_component.set_material(0,material)
assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,contacts=contacts,slab=slab.get_actor_label(),slab_mesh=mesh.get_path_name(),playtest='user'),indent=2))
runpy.run_path(str(ROOT/'Content/Python/capture_hall_contacts.py'))
