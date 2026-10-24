import unreal as u,json
from pathlib import Path
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
stage=next(a for a in actors if isinstance(a,u.JumpAcquisitionStage));star=stage.get_editor_property('star');origin=star.get_actor_location();rows=[]
for a in actors:
 if (a.get_actor_location()-origin).length()>700:continue
 meshes=a.get_components_by_class(u.StaticMeshComponent)+a.get_components_by_class(u.SkeletalMeshComponent)
 rows.append({'name':a.get_name(),'label':a.get_actor_label(),'class':a.get_class().get_name(),'location':str(a.get_actor_location()),'meshes':[{'name':m.get_name(),'asset':str(m.get_editor_property('static_mesh') if isinstance(m,u.StaticMeshComponent) else m.get_skeletal_mesh_asset()),'transform':str(m.get_world_transform()),'bounds':str(m.get_local_bounds()) if isinstance(m,u.StaticMeshComponent) else ''} for m in meshes]})
(Path(u.Paths.project_dir())/'Saved/JumpAcquisition/layout-audit.json').write_text(json.dumps(rows,indent=2))

exec((Path(u.Paths.project_dir())/'tools/integrate-jump-animations.py').read_text(),globals());integrate_jump_animations()
m=star.get_component_by_class(u.StaticMeshComponent);dm=u.DynamicMesh()
r=u.GeometryScript_SceneUtils.copy_mesh_from_component(m,dm,u.GeometryScriptCopyMeshFromComponentOptions(),True)
bvh=u.GeometryScript_MeshSpatial.build_bvh_for_mesh(dm)[1]
q=u.Vector(-13733.91,-2444.48,-666.44)
near=u.GeometryScript_MeshSpatial.find_nearest_point_on_mesh(dm,bvh,q,u.GeometryScriptSpatialQueryOptions())
(Path(u.Paths.project_dir())/'Saved/JumpAcquisition/contact-surface.txt').write_text(str(near))
