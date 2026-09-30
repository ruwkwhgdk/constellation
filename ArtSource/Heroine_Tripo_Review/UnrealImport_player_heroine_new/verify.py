import unreal,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent; B='/Game/Constellation/Characters/Heroine/Refined';N='player_heroine_new'
mesh=unreal.load_asset(B+'/SK_'+N);skel=unreal.load_asset(B+'/SKEL_'+N);phys=unreal.load_asset(B+'/PHYS_'+N);anim=unreal.load_asset(B+'/Animations/AS_'+N+'_PreviewRelaxed')
helper=unreal.get_default_object(unreal.load_class(None,'/Script/PhysicsToolsets.PhysicsAssetToolset'))
body_names=list(helper.call_method('GetBodyNames',args=(phys,)))
slots=[{'slot':str(s.material_slot_name),'material':s.material_interface.get_path_name() if s.material_interface else None} for s in mesh.materials]
report={'mesh':mesh.get_path_name(),'skeleton':mesh.skeleton.get_path_name(),'physics_asset':mesh.get_editor_property('physics_asset').get_path_name(),'animation':anim.get_path_name(),'height_cm':mesh.get_bounds().box_extent.z*2,'materials':slots,'physics_bodies':body_names,'assets':list(unreal.EditorAssetLibrary.list_assets(B,recursive=True,include_folder=False))}
(P/'import_result.json').write_text(json.dumps(report,indent=2))
assert mesh.skeleton==skel and mesh.get_editor_property('physics_asset')==phys
assert anim.get_editor_property('skeleton')==skel
assert abs(report['height_cm']-160)<.1 and all(s['material'] for s in slots) and body_names
report['pass']=True
(P/'import_result.json').write_text(json.dumps(report,indent=2))
print('IMPORT_VALIDATION_PASSED',json.dumps(report))
