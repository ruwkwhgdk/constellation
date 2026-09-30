from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u,json,runpy
from pathlib import Path
ROOT=Path(u.Paths.project_dir());OUT=ROOT/'ArtSource/OvergrownHall/TripoReplacement/v003';D='/Game/Constellation/Environments/OvergrownHall/TripoFull';MAP='/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull'
E=u.EditorAssetLibrary;AT=u.AssetToolsHelpers.get_asset_tools();L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(MAP)
u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),'Interchange.FeatureFlags.Import.FBX 0')
meshes={}
for r in load_current_json((OUT/'structure_manifest.json').read_text()):
    opts=u.FbxImportUI();opts.automated_import_should_detect_type=False;opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
    opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True
    t=u.AssetImportTask();t.filename=str(OUT/(r['mesh']+'.fbx'));t.destination_path=D+'/Meshes';t.automated=True;t.save=True;t.replace_existing=True;t.options=opts;t.factory=u.FbxFactory();AT.import_asset_tasks([t]);m=E.load_asset(t.imported_object_paths[0]);m.set_material(0,E.load_asset(D+'/Materials/M_OH_T_'+r['id']))
    m.get_editor_property('body_setup').set_editor_property('collision_trace_flag',u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE);E.save_loaded_asset(m,only_if_is_dirty=False);meshes[r['id']]=m
changed={id:0 for id in meshes}
for a in A.get_all_level_actors():
    label=a.get_actor_label()
    for id,m in meshes.items():
        if label.startswith('OH_FULL_'+id+'_'):a.static_mesh_component.set_static_mesh(m);changed[id]+=1
    if label.startswith('OH_FULL_03_'):
        a.set_actor_scale3d(u.Vector(.8,.8,.7))
    if label.startswith('OH_STRUCTURE_Roof_'):A.destroy_actor(a)
roof=E.load_asset(D+'/Meshes/SM_OH_T_26_RoofPanel')
positions=[(x,y) for x in [-4.5,-1.5] for y in [2,6,10,14,18]]+[(x,y) for x in [1.5,4.5] for y in [2,6]]
for i,(x,y) in enumerate(positions):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(-x*100,y*100,(11.95-abs(x)*2/7.6)*100),u.Rotator(pitch=0,yaw=(i%3-1)*2,roll=14 if x>0 else -14));a.set_actor_label('OH_STRUCTURE_Roof_%02d'%i);a.static_mesh_component.set_static_mesh(roof);a.set_actor_scale3d(u.Vector(1,2.03,1));a.static_mesh_component.set_collision_profile_name('BlockAll')
assert changed=={'06':8,'04':8};assert L.save_current_level()
(OUT/'applied.json').write_text(json.dumps(dict(map=MAP,replaced=changed,roof_fragments=14,window_grid='3 interior vertical and3 horizontal bars',playtest=False),indent=2))
runpy.run_path(str(ROOT/'Content/Python/verify_tripo_full_hall.py'))
script=ROOT/'Content/Python/capture_hall_exposure.py'
source=script.read_text().replace('ArtSource/OvergrownHall/Scene/v001','ArtSource/OvergrownHall/TripoReplacement/v003').replace('/Game/Constellation/Environments/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',MAP).replace('unreal_exposure_fixed.png','unreal_structure.png')
exec(compile(source,str(script),'exec'))
