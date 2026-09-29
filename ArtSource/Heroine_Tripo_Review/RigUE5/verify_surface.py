import bpy,hashlib,json,array
from pathlib import Path
P=Path(__file__).resolve().parent
def state(path):
 bpy.ops.wm.open_mainfile(filepath=str(path))
 result={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or o.name.startswith('WGT-'):continue
  h=hashlib.sha256()
  for collection,prop,size,typ in [(o.data.vertices,'co',3,'f'),(o.data.loops,'vertex_index',1,'i'),(o.data.polygons,'material_index',1,'i')]:
   buf=array.array(typ,[0])*(len(collection)*size);collection.foreach_get(prop,buf);h.update(buf.tobytes())
  for uv in o.data.uv_layers:
   buf=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',buf);h.update(buf.tobytes())
  result[o.name]=h.hexdigest()
 images={i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file}
 return result,images
a,ai=state(P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend');b,bi=state(P/'Delivery/Heroine_AnimationRig.blend')
out={'surface_geometry_uv_material_indices_exact':a==b,'packed_texture_bytes_exact':all(bi.get(k)==v for k,v in ai.items()),'mesh_count':len(a),'texture_count':len(ai)}
assert all([out['surface_geometry_uv_material_indices_exact'],out['packed_texture_bytes_exact']])
(P/'Delivery/surface_preservation.json').write_text(json.dumps(out,indent=2));print(out)
