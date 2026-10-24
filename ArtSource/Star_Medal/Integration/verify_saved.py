import unreal as u,json,time
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/Star_Medal/Integration'
B='/Game/Constellation/Gameplay/Interaction/Actors/BP_CollectableItem_StarCoin'
D='/Game/Constellation/Environments/Shared/Props/Star_Medal'
bp=u.load_asset(B);mesh=u.load_asset(D+'/SM_Star_Medal');mi=u.load_asset(D+'/MI_Star_Medal')
A=u.get_editor_subsystem(u.EditorActorSubsystem)
world=u.EditorLoadingAndSavingUtils.new_blank_map(False)
actor=A.spawn_actor_from_class(bp.generated_class(),u.Vector(0,0,65))
c=actor.get_component_by_class(u.StaticMeshComponent)
assert c.static_mesh==mesh,c.static_mesh
assert c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
assert abs(c.get_relative_transform().scale3d.z-.5)<.0001
assert all(s.material_interface==mi for s in mesh.static_materials)
M=u.MaterialEditingLibrary
for param,suffix in [('BaseColor','BaseColor'),('Normal','Normal'),('Roughness','Roughness'),('Metalic','Metallic')]:
 assert M.get_material_instance_texture_parameter_value(mi,param)==u.load_asset(D+'/T_Star_Medal_'+suffix)
gold=u.load_asset('/Game/Constellation/Gameplay/Interaction/Actors/BP_CollectableItem_Gold')
gold_actor=A.spawn_actor_from_class(gold.generated_class(),u.Vector(0,0,-10000))
gold_mesh=gold_actor.get_component_by_class(u.StaticMeshComponent).static_mesh
assert gold_mesh!=mesh
A.destroy_actor(gold_actor)
report={'passed':True,'spawned_star_coin_mesh':c.static_mesh.get_path_name(),'transform':str(c.get_relative_transform()),'collision':str(c.get_collision_enabled()),'gold_mesh':gold_mesh.get_path_name(),'components':[{'class':x.get_class().get_name(),'name':x.get_name()} for x in actor.get_components_by_class(u.ActorComponent)],'material_parameters_verified':True,'bounds':str(mesh.get_bounding_box())}
(P/'saved-verification.json').write_text(json.dumps(report,indent=2))

