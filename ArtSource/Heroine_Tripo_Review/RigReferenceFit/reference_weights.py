import bpy,json
from mathutils import Vector
from mathutils.kdtree import KDTree
def transfer(P,body,W,idx,ids,chain_weights):
 with bpy.data.libraries.load(str(P/'comparison_aligned.blend')) as (s,d):d.objects=[n for n in s.objects if n.startswith('REF_')]
 for o in d.objects:bpy.context.scene.collection.objects.link(o)
 bpy.context.view_layer.update()
 ref=next(o for o in d.objects if o.type=='MESH');groups={g.index:g.name.removeprefix('mixamorig:') for g in ref.vertex_groups}
 selected=[]
 for v in ref.data.vertices:
  p=(ref.matrix_world@v.co+Vector((.79,0,0)))/1.6008
  if .69<p.z<.86 and abs(p.x)>.025:selected.append((v,p))
 kd=KDTree(len(selected))
 for i,(v,p) in enumerate(selected):kd.insert(p,i)
 kd.balance();changed=0;distances=[]
 direct={'Hips':'DEF-spine','Spine':'DEF-spine.001','Spine1':'DEF-spine.002','Spine2':'DEF-spine.003','Neck':'DEF-spine.005','Head':'DEF-spine.006'}
 for v in body.data.vertices:
  p=body.matrix_world@v.co
  if ids[v.index]!=4 or p.z<.74 or not .04<abs(p.x)<.26:continue
  row={};total=0.
  for _,i,dist in kd.find_n(p,8):
   if dist>.06:continue
   rv,rp=selected[i];spatial=1/max(dist,.002)**2
   for group in rv.groups:
    name=groups[group.group];mapping={}
    if name in direct:mapping={direct[name]:1.}
    for side,long in [('L','Left'),('R','Right')]:
     if name==long+'Shoulder':mapping={f'DEF-shoulder.{side}':1.}
     elif name==long+'Arm':mapping=chain_weights(p,[f'DEF-upper_arm.{side}',f'DEF-upper_arm.{side}.001'],.018)
     elif name==long+'ForeArm':mapping=chain_weights(p,[f'DEF-forearm.{side}',f'DEF-forearm.{side}.001'],.018)
    for n,w in mapping.items():row[n]=row.get(n,0)+spatial*group.weight*w;total+=spatial*group.weight*w
  if total:
   a=.85*min(1,(abs(p.x)-.04)/.025)*min(1,(p.z-.74)/.025)
   W[v.index]*=1-a
   for n,w in row.items():W[v.index,idx[n]]+=a*w/total
   changed+=1;distances.append(kd.find(p)[2])
 for o in d.objects:bpy.data.objects.remove(o,do_unlink=True)
 (P/'reference_weight_transfer.json').write_text(json.dumps({'vertices':changed,'max_nearest_distance_m_source':max(distances) if distances else None,'method':'8-neighbor existing-model weights blended locally; hand/finger weights retained'},indent=2))
