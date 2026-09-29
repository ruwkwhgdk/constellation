import bpy,json,hashlib,array
from pathlib import Path
P=Path(__file__).resolve().parent
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));meshes={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH' or o.name.startswith('WGT-'):continue
  uvs=[]
  for layer in o.data.uv_layers:
   buf=array.array('f',[0])*(len(layer.data)*2);layer.data.foreach_get('uv',buf);uvs.append(buf.tobytes())
  meshes[o.name]={'v':[tuple(v.co) for v in o.data.vertices],'uv':uvs,'faces':[(tuple(p.vertices),p.material_index) for p in o.data.polygons]}
 images={i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file}
 return meshes,images
a,ai=snapshot(P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend');b,bi=snapshot(P/'Delivery/Heroine_AnimationRig.blend');ids=json.loads((P.parent/'DetailFinish2/components.json').read_text())['ids']
av=a['Heroine_DetailFinish2']['v'];bv=b['Heroine_DetailFinish2']['v']
protected=[]
for i,p in enumerate(av):
 c=ids[i]
 if c in [0,1,2,12,19,20,24,25,26,33,34] or (c==4 and p[2]<=.69) or (c==14 and (p[2]<.881 or p[2]>.916 or abs(p[0])<.010 or abs(p[0])>.062)):protected.append(i)
eyes=[n for n in a if n.startswith(('Iris','Sclera','Lower'))]
report={'protected_geometry_exact':all(av[i]==bv[i] for i in protected),'uv_and_topology_exact':all(a[n]['uv']==b[n]['uv'] and a[n]['faces']==b[n]['faces'] for n in a),'eye_front_projection_xz_exact':all(all(x[0]==y[0] and x[2]==y[2] for x,y in zip(a[n]['v'],b[n]['v'])) for n in eyes),'packed_textures_exact':ai==bi,'protected_body_vertex_count':len(protected),'max_eye_depth_change_cm':max(y[1]-x[1] for n in eyes for x,y in zip(a[n]['v'],b[n]['v']))*160.0801,'shoulder_joint_span_cm':.152*160.0801}
report['pass']=all(report[k] for k in ['protected_geometry_exact','uv_and_topology_exact','eye_front_projection_xz_exact','packed_textures_exact'])
(P/'Delivery/preservation_validation.json').write_text(json.dumps(report,indent=2));print(report)
