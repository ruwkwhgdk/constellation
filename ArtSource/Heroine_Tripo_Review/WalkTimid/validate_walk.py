import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Walk_Timid.blend'))
rig=bpy.data.objects['Heroine_AnimationRig'];sc=bpy.context.scene
meshes=[o for o in sc.objects if o.type=='MESH' and not o.name.startswith('WGT-')]
shoe_indices={}
for o in meshes:
 for side in ['L','R']:
  groups={g.index for g in o.vertex_groups if g.name in ['DEF-foot.'+side,'DEF-toe.'+side]}
  ids=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.7]
  if ids:shoe_indices[o.name,side]=ids
frames=[];start=None;end=None
for frame in range(1,42):
 sc.frame_set(frame);bpy.context.view_layer.update();world={p.name:rig.matrix_world@p.matrix for p in rig.pose.bones if p.name.startswith('DEF-')}
 if frame==1:start=world
 if frame==41:end=world
 samples={s:[] for s in ['L','R']}
 for o in meshes:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  for side in ['L','R']:
   samples[side].extend(o.matrix_world@m.vertices[i].co for i in shoe_indices.get((o.name,side),[]))
  ev.to_mesh_clear()
 frames.append({'frame':frame,'sole_min_z_m':{s:min(v.z for v in vs) for s,vs in samples.items()},'ankle':{s:list((rig.matrix_world@rig.pose.bones['DEF-foot.'+s].matrix).translation) for s in samples}})
loop_pos=max((start[n].translation-end[n].translation).length for n in start)
loop_angle=max(start[n].to_quaternion().rotation_difference(end[n].to_quaternion()).angle for n in start)
penetration=min(min(f['sole_min_z_m'].values()) for f in frames)
design=json.loads((P/'motion_design.json').read_text());speed=design['speed_cm_s']/100
errors=[]
for side,offset in [('L',0),('R',.5)]:
 for a,b in zip(frames,frames[1:]):
  phase=((a['frame']-1)/40+offset)%1
  # Mid-stance excludes heel/toe pivoting; these samples should translate backwards at walk speed.
  if .125<=phase<=.4:
   dy=b['ankle'][side][1]-a['ankle'][side][1]
   errors.append(abs(dy-speed/30))
report={'loop_position_error_m':loop_pos,'loop_rotation_error_deg':math.degrees(loop_angle),'min_shoe_height_m':penetration,'max_midstance_slide_error_m_per_frame':max(errors),'frames':frames}
report['pass']=loop_pos<1e-5 and loop_angle<1e-4 and penetration>-.002 and max(errors)<.002
(P/'validation.json').write_text(json.dumps(report,indent=2));print('WALK_VALIDATION', {k:v for k,v in report.items() if k!='frames'})
assert report['pass']
