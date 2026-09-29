import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
r=bpy.data.objects['Heroine_AnimationRig'];sc=bpy.context.scene;o=bpy.data.objects['Heroine_DetailFinish2']
d=json.loads((P/'reference_motion.json').read_text())['samples']
shoe={}
for s in ['L','R']:
 gs={g.index for g in o.vertex_groups if g.name in ['DEF-foot.'+s,'DEF-toe.'+s]}
 shoe[s]=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in gs)>.7]
def source_lift(s,u):
 word='Left' if s=='L' else 'Right';x=u*72;i=min(int(x),71);v=x-i
 def z(n):return (1-v)*d[i]['bones'][n]['head'][2]+v*d[i+1]['bones'][n]['head'][2]
 return max(0,min(z(word+'Foot')-d[0]['bones'][word+'Foot']['head'][2],z(word+'ToeBase')-d[0]['bones'][word+'ToeBase']['head'][2]))*.83614
def rotate_segment(n,direction):
 p=r.pose.bones[n];q=p.matrix.to_quaternion();delta=(p.tail-p.head).normalized().rotation_difference(direction.normalized());p.matrix=Matrix.LocRotScale(p.matrix.translation,delta@q,p.matrix.to_scale());bpy.context.view_layer.update()
cache=[]
for f in range(1,62):
 sc.frame_set(f);cache.append({n:p.matrix.copy() for n,p in r.pose.bones.items() if n in ['head','torso'] or n.startswith(('thigh_fk.','shin_fk.','foot_fk.','toe_fk.'))})
report=[]
for f in range(1,62):
 sc.frame_set(f)
 # Keep the reference head yaw, reduce its large lateral tilt during the cut.
 p=r.pose.bones['head'];q=p.matrix.to_quaternion();axis=q@Vector((0,1,0));target=axis.lerp(Vector((0,0,1)),.55).normalized();p.matrix=Matrix.LocRotScale(p.matrix.translation,axis.rotation_difference(target)@q,p.matrix.to_scale());bpy.context.view_layer.update()
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low={s:min((o.matrix_world@me.vertices[j].co).z for j in ids) for s,ids in shoe.items()};ev.to_mesh_clear()
 targets={}
 for s in ['L','R']:
  a=r.pose.bones['thigh_fk.'+s].head.copy();b=r.pose.bones['shin_fk.'+s].head.copy();c=r.pose.bones['foot_fk.'+s].head.copy()
  goal=c+r.matrix_world.inverted().to_3x3()@Vector((0,0,.001+source_lift(s,(f-1)/60)-low[s]))
  targets[s]=(a,b,c,goal,(b-a).length,(c-b).length)
 # Lower the pelvis only if needed to retain a small bend at full extension.
 drop=0
 for a,b,c,g,l1,l2 in targets.values():
  reach=(l1+l2)*.993;xy=(g.x-a.x)**2+(g.y-a.y)**2
  if xy<reach*reach:drop=max(drop,a.z-g.z-math.sqrt(reach*reach-xy))
 if drop>0:
  p=r.pose.bones['torso'];m=p.matrix.copy();m.translation.z-=drop;p.matrix=m;bpy.context.view_layer.update()
 for s,(old_a,old_b,old_c,g,l1,l2) in targets.items():
  a=r.pose.bones['thigh_fk.'+s].head.copy();b=r.pose.bones['shin_fk.'+s].head.copy();c=r.pose.bones['foot_fk.'+s].head.copy()
  foot=r.pose.bones['foot_fk.'+s].matrix.to_quaternion();toe=r.pose.bones['toe_fk.'+s].matrix.to_quaternion()
  direction=g-a;dist=direction.length;direction.normalize();dist=min(dist,l1+l2-.0001)
  bend=b-a-direction*(b-a).dot(direction)
  if bend.length<.0001:bend=Vector((0,-1,0))-direction*direction.dot(Vector((0,-1,0)))
  bend.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);h=math.sqrt(max(.000001,l1*l1-along*along));knee=a+direction*along+bend*h
  rotate_segment('thigh_fk.'+s,knee-a);rotate_segment('shin_fk.'+s,g-r.pose.bones['shin_fk.'+s].head)
  for n,q in [('foot_fk.'+s,foot),('toe_fk.'+s,toe)]:
   p=r.pose.bones[n];p.matrix=Matrix.LocRotScale(p.matrix.translation,q,p.matrix.to_scale());bpy.context.view_layer.update()
 for n in ['head','torso']+[n+'.'+s for n in ['thigh_fk','shin_fk','foot_fk','toe_fk'] for s in ['L','R']]:
  p=r.pose.bones[n]
  for field in ['location','rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler']:p.keyframe_insert(field,frame=f,group=n)
 report.append({'frame':f,'extra_pelvis_drop_m':drop*r.scale.x,'reference_foot_lift_m':{s:source_lift(s,(f-1)/60) for s in ['L','R']}})
sc.frame_set(1)
before=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(P/'Reference_Sword.fbx'))
objects=set(bpy.data.objects)-before
for ob in list(objects):
 if ob.name.startswith('UCX_'):bpy.data.objects.remove(ob,do_unlink=True)
w=next(ob for ob in objects if ob.name.startswith('SM_Weapon'))
w.name='Preview_Sword';w.data.transform(w.matrix_world);w.matrix_world=Matrix.Identity(4)
# Original sword has its grip at +Z .65m, blade extends toward -Z.
shaft=(r.pose.bones['f_index.01.R'].head-r.pose.bones['f_pinky.01.R'].head).normalized()
z=-shaft;x=(r.pose.bones['hand_fk.R'].tail-r.pose.bones['hand_fk.R'].head).normalized();x=(x-z*x.dot(z)).normalized();y=z.cross(x).normalized()
grip=(r.pose.bones['f_middle.02.R'].head+r.pose.bones['f_ring.02.R'].head)/2
grip+=r.pose.bones['hand_fk.R'].matrix.to_quaternion()@Vector((0,0,-.010))
rot=Matrix((x,y,z)).transposed().to_4x4();rot.translation=r.matrix_world@grip
world=rot@Matrix.Scale(.5,4)@Matrix.Translation((0,0,-.65))
handworld=r.matrix_world@r.pose.bones['DEF-hand.R'].matrix
offset=handworld.inverted()@world
for f in range(1,62):
 sc.frame_set(f);w.matrix_world=r.matrix_world@r.pose.bones['DEF-hand.R'].matrix@offset
 w.rotation_mode='QUATERNION'
 for field in ['location','rotation_quaternion','scale']:w.keyframe_insert(field,frame=f)
mat=bpy.data.materials.new('Preview_Sword_Steel');mat.use_nodes=True
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.22,.26,.32,1);bs.inputs['Metallic'].default_value=.8;bs.inputs['Roughness'].default_value=.28
w.data.materials.clear();w.data.materials.append(mat)
(P/'polish_report.json').write_text(json.dumps({'feet':report,'sword_scale':.5,'sword_hand_offset':[list(row) for row in offset]},indent=2))
for layer in r.animation_data.action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
sc.render.fps=60;sc.render.fps_base=1.;sc.frame_start=1;sc.frame_end=61
sc.frame_set(23);bpy.ops.wm.save_as_mainfile(filepath=str(P/'Heroine_Attack01.blend'))
print('ATTACK_POLISHED')
