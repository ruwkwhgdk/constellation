import unreal as u, json
from pathlib import Path
P=Path(u.Paths.project_dir())/'ArtSource/Star_Medal/Integration'
old=u.load_asset('/Game/Constellation/Environments/Shared/Props/Star_Coin/SM_Star_Coin')
bp=u.load_asset('/Game/Constellation/Gameplay/Interaction/Actors/BP_CollectableItem_StarCoin')
r=u.AssetRegistryHelpers.get_asset_registry();r.search_all_assets(True)
def desc(c):
 return {'path':c.get_path_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else None,'transform':str(c.get_relative_transform()),'materials':[x.get_path_name() if x else None for x in c.get_editor_property('override_materials')],'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name())}
data={'bounds':str(old.get_bounding_box()),'materials':[str(x.material_interface) for x in old.static_materials],'references':[str(x) for x in r.get_referencers(old.get_path_name().split('.')[0],u.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True))],'components':[desc(c) for c in u.ObjectIterator(u.StaticMeshComponent) if c.static_mesh==old],'body':str(old.get_editor_property('body_setup'))}
(P/'probe.json').write_text(json.dumps(data,indent=2))
u.log('STAR_MEDAL_PROBE '+str(data))
