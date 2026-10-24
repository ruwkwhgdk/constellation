import unreal as u,json
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/SchoolGymDoor/Polish_v001'
A=u.get_editor_subsystem(u.EditorActorSubsystem)
B='/Game/Constellation/Environments/School/Blueprints/BP_School_Gate'
bp=u.load_asset(B)
def component(c):
 return dict(name=c.get_name(),path=c.get_path_name(),mesh=c.static_mesh.get_path_name() if c.static_mesh else None,transform=str(c.get_relative_transform()),materials=[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],collision=str(c.get_collision_enabled()))
data={'templates':[component(c) for c in u.ObjectIterator(u.StaticMeshComponent) if c.get_path_name().startswith(B+'.')],'meshes':{},'actors':[]}
paths=['/Game/ModulAbandJPSchool/Meshes/BuildingModules/Gymnasium/SM_GymDoor01','/Game/ModulAbandJPSchool/Meshes/BuildingModules/Gymnasium/SM_GymDoor02','/Game/Constellation/Environments/School/Sets/GymCorridor/SM_GymDoorLeaf']
paths+=list(set(x['mesh'].split('.')[0] for x in data['templates'] if x['mesh']))
for path in paths:
 m=u.load_asset(path)
 if not m:continue
 mats=[s.material_interface for s in m.static_materials]
 data['meshes'][path]={'bounds':str(m.get_bounding_box()),'materials':[]}
 for mat in mats:
  info={'path':mat.get_path_name(),'class':mat.get_class().get_name()}
  if isinstance(mat,u.MaterialInstanceConstant):
   info['parent']=str(mat.get_editor_property('parent'))
   info['textures']=[{'name':str(p.parameter_info.name),'value':p.parameter_value.get_path_name() if p.parameter_value else None} for p in mat.get_editor_property('texture_parameter_values')]
   info['vectors']=[str(p) for p in mat.get_editor_property('vector_parameter_values')]
  data['meshes'][path]['materials'].append(info)
 task=u.AssetExportTask();task.object=m;task.filename=str(P/'Source'/(m.get_name()+'.fbx'));task.automated=True;task.prompt=False;task.replace_identical=True;task.exporter=u.StaticMeshExporterFBX();u.Exporter.run_asset_export_task(task)
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
for a in A.get_all_level_actors():
 comps=a.get_components_by_class(u.StaticMeshComponent)
 if a.get_class()==bp.generated_class() or any(c.static_mesh and 'GymDoor' in c.static_mesh.get_name() for c in comps):
  data['actors'].append({'label':a.get_actor_label(),'path':a.get_path_name(),'class':a.get_class().get_path_name(),'transform':str(a.get_actor_transform()),'components':[component(c) for c in comps]})
(P/'Reports/audit.json').write_text(json.dumps(data,indent=2),encoding='utf8')
u.log('GYM_DOOR_AUDIT_DONE')
