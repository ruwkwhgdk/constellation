import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
B='/Game/Constellation/Characters/Enemies/Slime_Liquid'
mesh=u.load_asset(B+'/SKM_Slime_Liquid')
reg=u.AssetRegistryHelpers.get_asset_registry()
paths=set(json.loads((P/'replacement-report.json').read_text())['maps'])
paths.update(row['path'] for row in json.loads((P/'asset-verification.json').read_text())['blueprints'])
paths.add('/Game/Constellation/Characters/Enemies/Blueprints/BP_Monster_Patrol')
paths.add('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
objects=[u.load_asset(p) for p in paths]
changes=[]
for c in u.ObjectIterator(u.SkeletalMeshComponent):
 if c.get_editor_property('skeletal_mesh_asset')!=mesh:continue
 owner=c.get_owner()
 if not owner:
  if 'BP_Player_Slime' not in c.get_path_name():continue
  half=64.0
 else:
  cap=owner.get_component_by_class(u.CapsuleComponent)
  if not cap:continue
  half=cap.get_unscaled_capsule_half_height()
 # All authored slime mesh/pivot rest rotations are yaw-only; moving along
 # their local Z preserves the climb pivot's subsequent surface orientation.
 rel=c.get_relative_transform();p=rel.transform_location(u.Vector(0,0,-84.327904))
 parent=c.get_attach_parent();parent_scale=1.0
 while parent and owner and parent!=owner.root_component:
  tr=parent.get_relative_transform();p=tr.transform_location(p);parent_scale*=tr.scale3d.z;parent=parent.get_attach_parent()
 dz=(-half-p.z)/parent_scale
 if abs(dz)>.01:
  loc=c.get_editor_property('relative_location');before=loc.z;loc.z+=dz
  c.modify();c.set_editor_property('relative_location',loc)
  changes.append({'component':c.get_path_name(),'before_z':before,'after_z':loc.z,'capsule_half_height':half})
for obj in objects:
 if isinstance(obj,u.Blueprint):u.BlueprintEditorLibrary.compile_blueprint(obj)
 assert u.EditorAssetLibrary.save_loaded_asset(obj,False)
(P/'ground-fit-report.json').write_text(json.dumps(changes,indent=2))
