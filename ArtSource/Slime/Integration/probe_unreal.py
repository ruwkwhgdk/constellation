import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
sk=u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Normal/SK_Slime_Normal')
rp=sk.get_reference_pose()
out={'ref':str(rp),'ref_api':dir(rp),'ref_doc':str(type(rp).__doc__), 'sk_ref_doc':str(sk.get_reference_pose.__doc__)}
for cls in [u.AnimDataController,u.MaterialEditingLibrary,u.EditorAssetLibrary,u.EditorLoadingAndSavingUtils,u.BlueprintEditorLibrary]:
 out[cls.__name__]=[x for x in dir(cls) if not x.startswith('_')]
for path in ['/Game/Constellation/Characters/Enemies/Blueprints/BP_Slime_Base','/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Slime','/Game/Constellation/Characters/NPC/Blueprints/BP_NPC_Slime']:
 bp=u.load_asset(path); cdo=u.get_default_object(bp.generated_class())
 out[path]={'capsule':str(cdo.get_component_by_class(u.CapsuleComponent)), 'components':[]}
 cap=cdo.get_component_by_class(u.CapsuleComponent)
 if cap:out[path]['capsule_size']=[cap.get_unscaled_capsule_radius(),cap.get_unscaled_capsule_half_height()]
 for c in cdo.get_components_by_class(u.SkeletalMeshComponent):
  out[path]['components'].append({'mesh':str(c.get_editor_property('skeletal_mesh_asset')),'transform':str(c.get_relative_transform()),'materials':str(c.get_editor_property('override_materials'))})
out['material_api']={n:str(getattr(u.MaterialEditingLibrary,n).__doc__) for n in ['create_material_expression','connect_material_property','set_material_usage']}
(P/'probe.json').write_text(json.dumps(out,indent=2))
