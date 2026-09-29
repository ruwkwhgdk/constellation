import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
def signature():
 o=bpy.data.objects['Heroine_DetailFinish2'];m=o.data
 geo=hashlib.sha256(str([tuple(v.co) for v in m.vertices]).encode()).hexdigest()
 uv=hashlib.sha256(str([[tuple(x.uv) for x in layer.data] for layer in m.uv_layers]).encode()).hexdigest()
 topo=hashlib.sha256(str([(tuple(p.vertices),p.material_index) for p in m.polygons]).encode()).hexdigest()
 textures={im.name:hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
 return {'positions':geo,'uv':uv,'topology_material_indices':topo,'textures':textures}
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'RigReferenceFit/Delivery/Heroine_AnimationRig.blend'));before=signature()
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Walk_Timid.blend'));after=signature()
o=bpy.data.objects['Heroine_DetailFinish2'];fix=json.loads((P/'garment_weight_fix.json').read_text())
counts=[len(v.groups) for v in o.data.vertices];err=max(abs(sum(g.weight for g in v.groups)-1) for v in o.data.vertices)
report={'geometry_uv_textures_preserved':before==after,'max_influences':max(counts),'unweighted_vertices':sum(n==0 for n in counts),'max_weight_sum_error':err,'changed_skirt_vertices':fix['changed_vertices']}
report['pass']=before==after and max(counts)<=4 and min(counts)>0 and err<1e-5
(P/'preview_mesh_audit.json').write_text(json.dumps(report,indent=2));print(report);assert report['pass']
