import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Run_Soft.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];o=bpy.data.objects['Heroine_DetailFinish2'];sc=bpy.context.scene
def knee(a,b,c):return 180-math.degrees((a-b).angle(c-b))
shoe={}
for side in ['L','R']:
 gs={g.index for g in o.vertex_groups if g.name in ['DEF-foot.'+side,'DEF-toe.'+side]}
 shoe[side]=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in gs)>.7]
cloth=sorted({i for p in o.data.polygons if p.material_index==3 for i in p.vertices if o.data.vertices[i].co.z<.575})
skin=[list(p.vertices) for p in o.data.polygons if p.material_index in [2,4] and all(.30<o.data.vertices[i].co.z<.615 for i in p.vertices)]
samples=[];poses=[]
for i in range(121):
 f=1+i/4;sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=[o.matrix_world@v.co for v in mesh.vertices]
 row={'frame':f,'knees':{},'soles':{s:min(co[j].z for j in ids) for s,ids in shoe.items()},'toes':{}}
 for s in ['L','R']:
  row['knees'][s]=knee(*[r.matrix_world@r.pose.bones[n+'.'+s].head for n in ['DEF-thigh','DEF-shin','DEF-foot']])
  row['toes'][s]=list(r.matrix_world@r.pose.bones['DEF-toe.'+s].head)
 center=(r.matrix_world@r.pose.bones['DEF-thigh.L'].head+r.matrix_world@r.pose.bones['DEF-thigh.R'].head)/2
 tree=BVHTree.FromPolygons(co,skin,all_triangles=False);clearance=[]
 for vid in cloth:
  radial=co[vid]-center;radial.z=0
  if radial.length<.001:continue
  radial.normalize();hit,n,poly,d=tree.ray_cast(co[vid]+radial*.4,-radial,.8)
  if hit is not None:clearance.append((co[vid]-hit).dot(radial))
 row['minimum_tested_cloth_clearance_m']=min(clearance,default=1)
 ev.to_mesh_clear();samples.append(row)
 poses.append({p.name:r.matrix_world@p.matrix for p in r.pose.bones if p.name.startswith('DEF-')})
contact=json.loads((P/'contact_design.json').read_text());speed=contact['suggested_speed_cm_s']/100
slip={}
for side,frames in contact['contact_windows']:
 start=frames[0]-1;end=start+len(frames)-1;points=[]
 for j in range(start*5,end*5+1):
  v=Vector(samples[j%120]['toes'][side]);v.y-=speed*(j-start*5)/120;points.append(v)
 origin=points[0];slip[side]=max(math.hypot(v.x-origin.x,v.y-origin.y) for v in points)
loop=max((poses[0][n].translation-poses[-1][n].translation).length for n in poses[0])
angles=max(math.degrees(2*math.acos(min(1,abs(poses[0][n].to_quaternion().dot(poses[-1][n].to_quaternion()))))) for n in poses[0])
report={'sample_rate_hz':120,'duration_s':1.0,'suggested_speed_cm_s':speed*100,'knee_ranges_deg':{s:[min(v['knees'][s] for v in samples),max(v['knees'][s] for v in samples)] for s in ['L','R']},'loop_position_error_m':loop,'loop_rotation_error_deg':angles,'minimum_sole_height_m':min(z for v in samples for z in v['soles'].values()),'minimum_tested_cloth_clearance_m':min(v['minimum_tested_cloth_clearance_m'] for v in samples),'planted_toe_world_slip_m':slip,'collision_scope':'Radial thigh-envelope tests on skirt vertices below bind z=.575; does not prove absence of every triangle intersection.','samples':samples}
report['checks_pass']=loop<.0001 and angles<.15 and min(v[0] for v in report['knee_ranges_deg'].values())>10 and report['minimum_sole_height_m']>-.002 and max(slip.values())<.003 and report['minimum_tested_cloth_clearance_m']>-.002
(P/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));assert report['checks_pass']
