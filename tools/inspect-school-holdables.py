import unreal as u
import json
from pathlib import Path
out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview/SchoolFurniture'; out.mkdir(parents=True,exist_ok=True)
sub=u.get_engine_subsystem(u.SubobjectDataSubsystem)
fn=u.SubobjectDataBlueprintFunctionLibrary
rows=[]
for name in ('BP_School_Chair','BP_School_Desk'):
    bp=u.load_asset('/Game/Constellation/Environments/School/Blueprints/'+name)
    row={'name':name,'components':[]}
    for handle in sub.k2_gather_subobject_data_for_blueprint(bp):
        obj=fn.get_object(fn.get_data(handle))
        data={'name':obj.get_name(),'class':obj.get_class().get_name()}
        if isinstance(obj,u.SceneComponent):
            data.update(transform=str(obj.get_relative_transform()),mobility=str(obj.mobility))
        if isinstance(obj,u.StaticMeshComponent):
            mesh=obj.static_mesh
            data.update(mesh=mesh.get_path_name() if mesh else None,collision=str(obj.get_collision_enabled()),simulate=obj.is_simulating_physics())
            if mesh:
                body=mesh.get_editor_property('body_setup')
                data.update(bounds=str(mesh.get_bounds()),collision_trace=str(body.get_editor_property('collision_trace_flag')),geometry=str(body.get_editor_property('agg_geom')))
        row['components'].append(data)
    (out/(name+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding='utf-8')
    rows.append(row)
(out/'inspection.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
u.log('SCHOOL_HOLDABLE_INSPECTION '+json.dumps(rows))
