import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];o=bpy.data.objects['Heroine_DetailFinish2'];w=bpy.data.objects['Preview_Sword'];sc=bpy.context.scene
assert sc.render.fps/sc.render.fps_base==60 and sc.frame_end-sc.frame_start==60
shoe={}
for s in ['L','R']:
 gs={g.index for g in o.vertex_groups if g.name in ['DEF-foot.'+s,'DEF-toe.'+s]};shoe[s]=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in gs)>.7]
cloth=sorted({i for p in o.data.polygons if p.material_index==3 for i in p.vertices if o.data.vertices[i].co.z<.575})
skin=[list(p.vertices) for p in o.data.polygons if p.material_index in [2,4] and all(.30<o.data.vertices[i].co.z<.615 for i in p.vertices)]
rows=[]
for i in range(121):
 f=1+i/2;sc.frame_set(int(f),subframe=f%1)
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[o.matrix_world@v.co for v in me.vertices]
 knees={}
 for s in ['L','R']:
  a,b,c=[r.matrix_world@r.pose.bones[n+'.'+s].head for n in ['DEF-thigh','DEF-shin','DEF-foot']];knees[s]=180-math.degrees((a-b).angle(c-b))
 center=(r.matrix_world@r.pose.bones['DEF-thigh.L'].head+r.matrix_world@r.pose.bones['DEF-thigh.R'].head)/2
 tree=BVHTree.FromPolygons(co,skin,all_triangles=False);clear=[]
 for vid in cloth:
  radial=co[vid]-center;radial.z=0
  if radial.length<.001:continue
  radial.normalize();hit,n,poly,d=tree.ray_cast(co[vid]+radial*.4,-radial,.8)
  if hit is not None:clear.append((co[vid]-hit).dot(radial))
 row={'time':i/120,'knees':knees,'soles':{s:min(co[j].z for j in ids) for s,ids in shoe.items()},'cloth_clearance_m':min(clear,default=1),'head':list(r.matrix_world@r.pose.bones['DEF-spine.006'].head) if 'DEF-spine.006' in r.pose.bones else [],'torso':list(r.matrix_world@r.pose.bones['torso'].head),'sword_tip':list(w.matrix_world@Vector((0,0,-.95))),'right_hand':list(r.matrix_world@r.pose.bones['DEF-hand.R'].head)}
 rows.append(row);ev.to_mesh_clear()
report={'duration_s':1,'sample_rate_hz':120,'minimum_sole_m':min(v for a in rows for v in a['soles'].values()),'knee_ranges_deg':{s:[min(a['knees'][s] for a in rows),max(a['knees'][s] for a in rows)] for s in ['L','R']},'cloth_clearance_m':min(a['cloth_clearance_m'] for a in rows),'body_vertical_range_cm':100*(max(a['torso'][2] for a in rows)-min(a['torso'][2] for a in rows)),'samples':rows}
(P/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
