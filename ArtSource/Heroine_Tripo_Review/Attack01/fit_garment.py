import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];o=bpy.data.objects['Heroine_DetailFinish2'];sc=bpy.context.scene
for f in range(1,62):
 sc.frame_set(f)
 delta=r.pose.bones['DEF-spine'].matrix@r.data.bones['DEF-spine'].matrix_local.inverted()
 local_dirs={s:delta.to_quaternion().inverted()@(r.pose.bones['DEF-shin.'+s].head-r.pose.bones['DEF-thigh.'+s].head).normalized() for s in ['L','R']}
 pitches={s:math.atan2(v.y,-v.z) for s,v in local_dirs.items()}
 for i in range(8):
  side=min(local_dirs,key=lambda s:local_dirs[s].y) if i==0 else max(local_dirs,key=lambda s:local_dirs[s].y) if i==4 else 'L' if i<4 else 'R'
  pivot=r.data.bones['DEF-thigh.'+side].head_local
  axis=(r.data.bones['DEF-thigh.'+side].tail_local-pivot).normalized()
  swing=axis.rotation_difference(local_dirs[side])
  follow=Matrix.Translation(pivot)@swing.to_matrix().to_4x4()@Matrix.Translation(-pivot)
  for j in [1,2]:
   n=f'skirt_{i:02}.{j:02}';p=r.pose.bones[n];p.matrix=delta@follow@r.data.bones[n].matrix_local;bpy.context.view_layer.update()
   p.keyframe_insert('location',frame=f,group=n);p.keyframe_insert('rotation_quaternion',frame=f,group=n)
cloth=sorted({i for p in o.data.polygons if p.material_index==3 for i in p.vertices if o.data.vertices[i].co.z<.575})
skin=[list(p.vertices) for p in o.data.polygons if p.material_index in [2,4] and all(.30<o.data.vertices[i].co.z<.615 for i in p.vertices)]
weights={}
for vid in cloth:
 a=np.zeros(8)
 for g in o.data.vertices[vid].groups:
  n=o.vertex_groups[g.group].name
  if n.startswith('DEF-skirt_'):a[int(n.split('_')[1].split('.')[0])]+=g.weight
 weights[vid]=a
reports=[]
for f in range(1,62):
 sc.frame_set(f);center=(r.matrix_world@r.pose.bones['DEF-thigh.L'].head+r.matrix_world@r.pose.bones['DEF-thigh.R'].head)/2
 delta=r.pose.bones['DEF-spine'].matrix@r.data.bones['DEF-spine'].matrix_local.inverted();dirs=[]
 for i in range(8):
  d=r.matrix_world.to_3x3()@delta.to_3x3()@Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),0));d.z=0;d.normalize();dirs.append(d)
 total=np.zeros(8)
 for iteration in range(8):
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[o.matrix_world@v.co for v in me.vertices];tree=BVHTree.FromPolygons(co,skin,all_triangles=False);A=[];b=[]
  for vid in cloth:
   radial=co[vid]-center;radial.z=0
   if radial.length<.001:continue
   radial.normalize();hit,n,poly,d=tree.ray_cast(co[vid]+radial*.4,-radial,.8)
   if hit is None:continue
   gap=.003-(co[vid]-hit).dot(radial)
   if gap>0:A.append(weights[vid]*np.array([radial.dot(v) for v in dirs]));b.append(gap)
  ev.to_mesh_clear()
  if not A:break
  step=np.linalg.lstsq(np.vstack([np.array(A),np.eye(8)*.3]),np.r_[b,np.zeros(8)],rcond=None)[0]
  step=np.clip(step,0,np.minimum(.018,.065-total));total+=step
  for i in range(8):
   matrices=[r.pose.bones[f'skirt_{i:02}.{j:02}'].matrix.copy() for j in [1,2]]
   for j,m in zip([1,2],matrices):
    p=r.pose.bones[f'skirt_{i:02}.{j:02}'];m.translation+=r.matrix_world.inverted().to_3x3()@(dirs[i]*float(step[i]));p.matrix=m;bpy.context.view_layer.update()
 for i in range(8):
  for j in [1,2]:
   p=r.pose.bones[f'skirt_{i:02}.{j:02}'];p.keyframe_insert('location',frame=f,group=p.name)
 reports.append({'frame':f,'outward_correction_m':total.tolist()})
(P/'garment_report.json').write_text(json.dumps(reports,indent=2))
sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
print('GARMENT_ALIGNED_TO_DEFORM_PELVIS')
