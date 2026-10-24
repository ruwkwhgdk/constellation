import unreal as u, json, shutil
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/Star_Medal';E=u.EditorAssetLibrary
D='/Game/Constellation/Environments/Shared/Props/Star_Medal'
B='/Game/Constellation/Gameplay/Interaction/Actors/BP_CollectableItem_StarCoin'
old=u.load_asset('/Game/Constellation/Environments/Shared/Props/Star_Coin/SM_Star_Coin')
raw=json.loads((P/'Integration/import.json').read_text());ob=old.get_bounding_box()
scale=(ob.max.z-ob.min.z)/(raw['max'][2]-raw['min'][2])
center=[(getattr(ob.min,k)+getattr(ob.max,k))/2 for k in ['x','y','z']]
translation=[center[i]-(raw['min'][i]+raw['max'][i])*scale/2 for i in range(3)]
opts=u.FbxImportUI();opts.import_mesh=True;opts.import_as_skeletal=False;opts.import_materials=False;opts.import_textures=False;opts.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH;opts.automated_import_should_detect_type=False
opts.static_mesh_import_data.combine_meshes=True;opts.static_mesh_import_data.auto_generate_collision=False;opts.static_mesh_import_data.convert_scene_unit=True
opts.static_mesh_import_data.import_uniform_scale=scale;opts.static_mesh_import_data.import_translation=u.Vector(*translation)
# Atomic FBX reimport uses the existing asset's import data, even when task
# replacement settings are requested. Update that source of truth explicitly.
existing=u.load_asset(D+'/SM_Star_Medal')
existing.get_editor_property('asset_import_data').set_editor_property('import_uniform_scale',scale)
existing.get_editor_property('asset_import_data').set_editor_property('import_translation',u.Vector(*translation))
u.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
t=u.AssetImportTask();t.filename=str(next((P/'Source').glob('*.fbx')));t.destination_path=D;t.destination_name='SM_Star_Medal';t.automated=True;t.save=True;t.replace_existing=True;t.replace_existing_settings=True;t.options=opts;t.factory=u.FbxFactory()
u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);assert t.imported_object_paths
new=u.load_asset(D+'/SM_Star_Medal');mi=u.load_asset(D+'/MI_Star_Medal')
for i in range(len(new.static_materials)):new.set_material(i,mi)
nb=new.get_bounding_box()
assert abs((nb.max.z-nb.min.z)-(ob.max.z-ob.min.z))<.05,str(nb)
assert abs((nb.max.z+nb.min.z)/2-center[2])<.05,str(nb)
E.save_loaded_asset(new,False)
bp=u.load_asset(B)
backup=P/'Integration/BP_CollectableItem_StarCoin.before.uasset'
if not backup.exists():shutil.copy2(Path(u.Paths.project_content_dir())/'Constellation/Gameplay/Interaction/Actors/BP_CollectableItem_StarCoin.uasset',backup)
def snapshot(c):
 tr=c.get_relative_transform()
 return {'transform':{'translation':[tr.translation.x,tr.translation.y,tr.translation.z],'rotation':[tr.rotation.x,tr.rotation.y,tr.rotation.z,tr.rotation.w],'scale':[tr.scale3d.x,tr.scale3d.y,tr.scale3d.z]},'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),'overlaps':c.get_editor_property('generate_overlap_events'),'materials':[x.get_path_name() if x else None for x in c.get_editor_property('override_materials')]}
components=[c for c in u.ObjectIterator(u.StaticMeshComponent) if c.get_path_name().startswith(B+'.') and c.static_mesh in (old,new)]
assert len(components)==1,[c.get_path_name() for c in components]
before=snapshot(components[0]);components[0].modify();components[0].set_static_mesh(new)
assert snapshot(components[0])==before
u.BlueprintEditorLibrary.compile_blueprint(bp);assert E.save_loaded_asset(bp,False)
report={'mesh':new.get_path_name(),'blueprint':B,'scale':scale,'translation':translation,'old_bounds':str(ob),'new_bounds':str(nb),'visual_settings_preserved':before,'changes':['Visual.static_mesh only'],'gold_blueprint_untouched':True}
(P/'Integration/replacement.json').write_text(json.dumps(report,indent=2))
u.log('STAR_MEDAL_APPLIED '+str(report))

