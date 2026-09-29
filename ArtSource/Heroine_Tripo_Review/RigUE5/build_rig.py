"""Fit a Rigify animation rig without editing accepted surface geometry."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P.parent/'DetailFinish2/Delivery/Heroine_DetailFinish2.blend'))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.preferences.addon_enable(module='rigify')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.armature_human_metarig_add()
meta=bpy.context.object;meta.name='Heroine_Metarig'
bpy.ops.object.mode_set(mode='EDIT');eb=meta.data.edit_bones
connected={b.name:b.use_connect for b in eb}
remove=set(['face','breast.L','breast.R','pelvis.L','pelvis.R'])
remove.update(b.name for b in eb if any(p.name=='face' for p in b.parent_recursive))
for n in list(remove):
 if n in eb:eb.remove(eb[n])
def fit(n,h,t):
 b=eb[n];b.use_connect=False;b.head=h;b.tail=t
points=[(0,.008,.553),(0,.005,.610),(0,.001,.673),(0,.002,.728),(0,.003,.796),(0,.002,.818),(0,.003,.842),(0,.003,.956)]
for i in range(7):fit('spine'+('.%03d'%i if i else ''),points[i],points[i+1])
for side,s in [('L',1),('R',-1)]:
 def v(x,y,z):return(s*x,y,z)
 fit('shoulder.'+side,v(.015,.004,.786),v(.100,.003,.786))
 fit('upper_arm.'+side,v(.10,.003,.786),v(.229,.012,.784))
 fit('forearm.'+side,v(.229,.012,.784),v(.350,.001,.784))
 fit('hand.'+side,v(.350,.001,.784),v(.389,.001,.784))
 fingers=[('f_index',-.019,.427),('f_middle',-.001,.433),('f_ring',.015,.425),('f_pinky',.029,.410)]
 for k,(name,y,end) in enumerate(fingers):
  start=.387 if k<3 else .382
  p0=v(.357,y*.40,.784);p1=v(start,y*.7,.784)
  fit(f'palm.{k+1:02}.{side}',p0,p1)
  pts=[p1,v(start+(end-start)*.43,y*.84,.784),v(start+(end-start)*.76,y*.94,.784),v(end,y,.784)]
  for j in range(3):fit(f'{name}.{j+1:02}.{side}',pts[j],pts[j+1])
 pts=[v(.357,-.013,.783),v(.371,-.022,.782),v(.380,-.030,.781),v(.388,-.035,.781)]
 for j in range(3):fit(f'thumb.{j+1:02}.{side}',pts[j],pts[j+1])
 fit('thigh.'+side,v(.046,.004,.550),v(.044,-.010,.286))
 fit('shin.'+side,v(.044,-.010,.286),v(.045,.005,.056))
 fit('foot.'+side,v(.045,.005,.056),v(.045,-.043,.022))
 fit('toe.'+side,v(.045,-.043,.022),v(.045,-.079,.020))
 fit('heel.02.'+side,v(.024,.030,.010),v(.065,.030,.010))
 for n in ['upper_arm','forearm','hand']:
  eb[n+'.'+side].align_roll(Vector((0,0,1)))
 for n in ['thigh','shin']:eb[n+'.'+side].align_roll(Vector((0,1,0)))
 for name,_,_ in fingers:
  for j in range(3):eb[f'{name}.{j+1:02}.{side}'].align_roll(Vector((0,0,1)))
 for j in range(3):eb[f'thumb.{j+1:02}.{side}'].align_roll(Vector((0,0,1)))
for b in eb:
 if connected.get(b.name):b.use_connect=True
def chain(name,pts,parent):
 for i in range(len(pts)-1):
  b=eb.new(f'{name}.{i+1:02}');b.head=pts[i];b.tail=pts[i+1];b.parent=eb[parent if i==0 else f'{name}.{i:02}'];b.use_connect=i>0
for i in range(8):
 a=2*math.pi*i/8;x,y=math.sin(a),-math.cos(a)
 chain(f'skirt_{i:02}',[(x*.067,y*.048,.561),(x*.082,y*.062,.511),(x*.097,y*.073,.466)],'spine')
for name,x,y in [('hair_side_L',.074,0),('hair_side_R',-.074,0),('hair_back_L',.040,.063),('hair_back_R',-.040,.063)]:
 chain(name,[(x*.8,y*.8,.958),(x,y,.904),(x*.88,y*.84,.844)],'spine.006')
bpy.ops.object.mode_set(mode='OBJECT')
for p in meta.pose.bones:
 if p.rigify_type in ['limbs.arm','limbs.leg']:
  p.rigify_parameters.segments=2;p.rigify_parameters.bbones=1
 if p.name.startswith(('skirt_','hair_')) and p.name.endswith('.01'):p.rigify_type='basic.copy_chain'
meta.show_in_front=True
bpy.ops.pose.rigify_generate()
rig=bpy.context.object;rig.name='Heroine_AnimationRig'
for b in rig.data.bones:b.bbone_segments=1
meta.hide_render=True;meta.hide_set(True)
for p in rig.pose.bones:
 if 'IK_FK' in p:p['IK_FK']=1.0
 if 'IK_Stretch' in p:p['IK_Stretch']=0.0
rig.show_in_front=True
bpy.context.view_layer.update()
data=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform,'props':dict(rig.pose.bones[b.name].items())} for b in rig.data.bones]
(P/'generated_bones.json').write_text(json.dumps(data,indent=2,default=str))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'rig_unbound.blend'))
print('RIG_GENERATED',len(data),sum(b.use_deform for b in rig.data.bones),flush=True)
