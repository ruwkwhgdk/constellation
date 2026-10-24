import unreal as u
import json
from pathlib import Path

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / 'ArtSource/Slime/Integration'
OUT.mkdir(parents=True, exist_ok=True)
reg = u.AssetRegistryHelpers.get_asset_registry()
reg.search_all_assets(True)
base = '/Game/Constellation/Characters/Enemies'
assets = reg.get_assets_by_path(base, recursive=True)
report = {'assets': {}, 'api': {}}
for data in assets:
    path = str(data.package_name)
    obj = data.get_asset()
    entry = {'class': obj.get_class().get_name(), 'referencers': [str(x) for x in reg.get_referencers(path, u.AssetRegistryDependencyOptions(True,True,False,False,False))]}
    for prop in ['skeleton','physics_asset','preview_skeletal_mesh','materials','animation_class']:
        try: entry[prop] = str(obj.get_editor_property(prop))
        except Exception: pass
    if isinstance(obj, u.AnimSequence):
        entry['duration'] = obj.get_play_length()
        entry['tracks'] = [str(x) for x in u.AnimationLibrary.get_animation_track_names(obj)]
        entry['poses'] = {str(t): {str(b):str(u.AnimationLibrary.get_bone_pose_for_time(obj,b,t,False)) for b in entry['tracks']} for t in [0,obj.get_play_length()*.5]}
    if isinstance(obj,u.Blueprint):
        try:
            cdo = u.get_default_object(obj.generated_class())
            entry['cdo'] = {}
            for c in cdo.get_components_by_class(u.SkeletalMeshComponent):
                entry['cdo'][c.get_name()] = {'mesh':str(c.get_editor_property('skeletal_mesh_asset')), 'transform': str(c.get_relative_transform()), 'materials':str(c.get_editor_property('override_materials')), 'anim_class':str(c.get_editor_property('anim_class'))}
        except Exception as e: entry['cdo_error'] = str(e)
    report['assets'][path] = entry
mesh=u.load_asset(base+'/Slime_Normal/SKM_Slime_Normal')
for cls in [u.SkeletalMesh, u.Skeleton, u.AnimationLibrary, u.EditorAssetLibrary, u.SkeletalMeshEditorSubsystem, u.AnimSequence]:
    report['api'][cls.__name__] = [x for x in dir(cls) if any(s in x.lower() for s in ['bone','pose','export','skeleton','retarget','consolidat','preview'])]
task=u.AssetExportTask()
task.object=mesh
task.filename=str(OUT/'OldSlimeReference.fbx')
task.automated=True
task.prompt=False
task.replace_identical=True
task.options=u.FbxExportOption()
(OUT/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
report['exported']=u.Exporter.run_asset_export_task(task)
(OUT/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
u.log('SLIME_AUDIT_DONE')
