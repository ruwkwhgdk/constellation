import unreal as u,json
from pathlib import Path
root=Path(u.Paths.project_dir());out=root/'ArtSource/OvergrownHall/TripoReplacement/v006';out.mkdir(parents=True,exist_ok=True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);assert L.load_level('/Game/Constellation/Worlds/OvergrownHall/Maps/L_OvergrownHall_TripoFull')
rows=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    n=a.get_actor_label()
    if n.startswith(('OH_FULL_02','OH_FULL_03','OH_FULL_04','OH_FULL_05','OH_FULL_18','OH_FULL_13','OH_FULL_09')) or n in ['OH_SM_OH_Blockout_21','OH_ReferenceCamera','OH_Exposure']:
        c,e=a.get_actor_bounds(False);p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
        row=dict(name=n,position=[p.x,p.y,p.z],rotation=[r.pitch,r.yaw,r.roll],scale=[s.x,s.y,s.z],center=[c.x,c.y,c.z],extent=[e.x,e.y,e.z])
        if n=='OH_Exposure':
            pp=a.get_editor_property('settings');row['reflection_method']=str(pp.reflection_method);row['gi_method']=str(pp.dynamic_global_illumination_method)
        rows.append(row)
mat=u.MaterialFactoryNew().factory_create_new('/Engine/Transient/GrowthProbe') if False else u.new_object(u.Material)
ML=u.MaterialEditingLibrary
output=ML.create_material_expression(mat,u.MaterialExpressionSingleLayerWaterMaterialOutput)
report=dict(actors=rows,water_inputs=list(ML.get_material_expression_input_names(output)))
(out/'inspection.json').write_text(json.dumps(report,indent=2))
u.log('HALL_GROWTH_INSPECTED')
