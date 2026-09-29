import bpy,json,hashlib,array
from pathlib import Path
P=Path(__file__).resolve().parent
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path))
 o=bpy.data.objects['Heroine_DetailFinish2'];uv=array.array('f',[0])*(len(o.data.uv_layers.active.data)*2);o.data.uv_layers.active.data.foreach_get('uv',uv)
 return {'v':[tuple(v.co) for v in o.data.vertices],'uv':uv.tobytes(),'faces':[(tuple(p.vertices),p.material_index) for p in o.data.polygons],'images':{i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file}}
a=snapshot(P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend');b=snapshot(P/'Delivery/Heroine_AnimationRig.blend');ids=json.loads((P.parent/'DetailFinish2/components.json').read_text())['ids']
result={'protected_body_components_exact':all(x==y for i,(x,y) in enumerate(zip(a['v'],b['v'])) if ids[i] not in [3,4,32]),'uv_exact':a['uv']==b['uv'],'topology_and_materials_exact':a['faces']==b['faces'],'packed_textures_exact':a['images']==b['images']}
assert all(result.values());result['pass']=True
(P/'Delivery/preservation_validation.json').write_text(json.dumps(result,indent=2));print(result)
