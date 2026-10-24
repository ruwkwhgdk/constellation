"""Install only the fall component on the current heroine; preserve authored data."""
import unreal as u, json, shutil, hashlib
from pathlib import Path
from datetime import datetime
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/FallSystem'/('install-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
out.mkdir(parents=True)
path='/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine'
disk=root/('Content/'+path.removeprefix('/Game/')+'.uasset')
shutil.copy2(disk,out/disk.name)
bp=u.load_asset(path)
graph=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
(out/'before-graph.txt').write_text(graph,encoding='utf8')
assert 'RouteCarryInput' in graph,'Existing input gate missing; inspect before installing'
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem);fn=u.SubobjectDataBlueprintFunctionLibrary
handles=sub.k2_gather_subobject_data_for_blueprint(bp)
components=[fn.get_object_for_blueprint(fn.get_data(h),bp) for h in handles]
fall=next((o for o in components if isinstance(o,u.PlayerFallComponent)),None)
if fall is None:
    handle,reason=sub.add_new_subobject(u.AddNewSubobjectParams(parent_handle=handles[0],new_class=u.PlayerFallComponent,blueprint_context=bp))
    assert fn.is_handle_valid(handle),str(reason)
    assert sub.rename_subobject(handle,'PlayerFall')
    fall=fn.get_object_for_blueprint(fn.get_data(handle),bp)
    assert fall
u.BlueprintEditorLibrary.compile_blueprint(bp)
assert u.EditorAssetLibrary.save_loaded_asset(bp,False)
report={'asset':path,'component':fall.get_path_name(),'backup':str(out/disk.name),'sha256':hashlib.sha256(disk.read_bytes()).hexdigest()}
(out/'installed.json').write_text(json.dumps(report,indent=2),encoding='utf8')
u.log('FALL_SYSTEM_INSTALLED '+json.dumps(report))
