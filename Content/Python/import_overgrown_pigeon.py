"""Dedicated pigeon skeleton and four animation sequences, no character edits."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); SRC=ROOT/'ArtSource/OvergrownHall/Bird/v001'; DEST='/Game/Constellation/Environments/OvergrownHall/Bird'
E=u.EditorAssetLibrary; AT=u.AssetToolsHelpers.get_asset_tools()
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.FBX 0')
def task(file,opts,folder):
    opts.automated_import_should_detect_type=False
    t=u.AssetImportTask(); t.filename=str(SRC/file); t.destination_path=DEST+'/'+folder; t.automated=True; t.save=True; t.replace_existing=True; t.options=opts; t.factory=u.FbxFactory()
    AT.import_asset_tasks([t]); assert t.imported_object_paths,file; return [E.load_asset(p) for p in t.imported_object_paths]
opts=u.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=True; opts.import_animations=False; opts.import_materials=True; opts.import_textures=False
opts.mesh_type_to_import=u.FBXImportType.FBXIT_SKELETAL_MESH; opts.create_physics_asset=False
opts.skeletal_mesh_import_data.convert_scene_unit=True
assets=task('SK_OH_Pigeon.fbx',opts,'Meshes')
mesh=next(a for a in assets if isinstance(a,u.SkeletalMesh)); skeleton=mesh.get_editor_property('skeleton'); assert skeleton
clips=[]
for name in ['Fly','Glide','FlyToGlide','GlideToFly']:
    target=DEST+'/Clips/A_OH_Pigeon_'+name
    existing=E.load_asset(target) if E.does_asset_exist(target) else None
    if existing and not isinstance(existing,u.AnimSequence):
        assert isinstance(existing,u.SkeletalMesh),target
        assert E.delete_asset(target)
    opts=u.FbxImportUI(); opts.import_mesh=False; opts.import_as_skeletal=True; opts.import_animations=True; opts.import_materials=False; opts.import_textures=False
    opts.mesh_type_to_import=u.FBXImportType.FBXIT_ANIMATION; opts.skeleton=skeleton
    opts.anim_sequence_import_data.set_editor_property('animation_length',u.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
    assets=task('A_OH_Pigeon_'+name+'.fbx',opts,'Clips')
    anim=next(a for a in assets if isinstance(a,u.AnimSequence)); assert anim.get_editor_property('skeleton')==skeleton
    clips.append(dict(name=name,path=anim.get_path_name(),seconds=anim.get_editor_property('sequence_length')))
assert E.save_directory(DEST,only_if_is_dirty=True,recursive=True)
report=dict(status='skeletal_import_pass',mesh=mesh.get_path_name(),skeleton=skeleton.get_path_name(),clips=clips,playback_verification='pending',flight_paths='not_created',appearance='first rigged draft')
(SRC/'unreal_import.json').write_text(json.dumps(report,indent=2))
u.log('PIGEON_IMPORT_PASS '+json.dumps(report))
