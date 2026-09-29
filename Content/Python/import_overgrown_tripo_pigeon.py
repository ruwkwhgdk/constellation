"""Dedicated pigeon skeleton and four animation sequences, no character edits."""
import unreal as u,json
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); SRC=ROOT/'ArtSource/OvergrownHall/Bird/Tripo_Rig_v001'; DEST='/Game/Environment/OvergrownHall/Bird/Tripo'
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
textures={}
for suffix in ['basecolor','normal','rm']:
    t=u.AssetImportTask(); t.filename=str(SRC/('OH_Pigeon_Tripo_v001_'+suffix+'.png')); t.destination_path=DEST+'/Textures'; t.automated=True; t.save=True; t.replace_existing=True
    AT.import_asset_tasks([t]); tex=E.load_asset(t.imported_object_paths[0]); textures[suffix]=tex
    if suffix!='basecolor': tex.set_editor_property('srgb',False)
    if suffix=='normal':
        tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property('flip_green_channel',True)
    E.save_loaded_asset(tex)
material=E.load_asset(DEST+'/Materials/M_Pigeon_Tripo') if E.does_asset_exist(DEST+'/Materials/M_Pigeon_Tripo') else AT.create_asset('M_Pigeon_Tripo',DEST+'/Materials',u.Material,u.MaterialFactoryNew())
ML=u.MaterialEditingLibrary; ML.delete_all_material_expressions(material)
for suffix,tex in textures.items():
    node=ML.create_material_expression(material,u.MaterialExpressionTextureSample,0,0); node.texture=tex
    if suffix=='normal': node.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
    elif suffix=='rm': node.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    if suffix=='basecolor': ML.connect_material_property(node,'RGB',u.MaterialProperty.MP_BASE_COLOR)
    elif suffix=='normal': ML.connect_material_property(node,'RGB',u.MaterialProperty.MP_NORMAL)
    else:
        ML.connect_material_property(node,'G',u.MaterialProperty.MP_ROUGHNESS)
        ML.connect_material_property(node,'B',u.MaterialProperty.MP_METALLIC)
ML.recompile_material(material)
mesh.modify()
slots=mesh.get_editor_property('materials')
for i in range(len(slots)):
    slot=slots[i]; slot.set_editor_property('material_interface',material); slots[i]=slot
mesh.set_editor_property('materials',slots)
E.save_loaded_asset(mesh,only_if_is_dirty=False)
E.save_loaded_asset(material,only_if_is_dirty=False)
assert E.save_directory(DEST,only_if_is_dirty=True,recursive=True)
report=dict(status='skeletal_import_pass',mesh=mesh.get_path_name(),skeleton=skeleton.get_path_name(),clips=clips,playback_verification='pending',flight_paths='not_created',appearance='approved Tripo geometry with new rig')
(SRC/'unreal_import.json').write_text(json.dumps(report,indent=2))
u.log('PIGEON_IMPORT_PASS '+json.dumps(report))
