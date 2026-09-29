import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'comparison_source.blend'))
ref=[o for o in bpy.context.scene.objects if o.name.startswith('REF_')]
new=[o for o in bpy.context.scene.objects if o not in ref]
roots=lambda obs:[o for o in obs if o.parent not in obs]
refscale=1.6/(.9483551383018494+.9507081508636475)
for o in roots(ref):o.matrix_world=Matrix.Translation((0,0,.9507081508636475*refscale))@Matrix.Scale(refscale,4)@o.matrix_world
for o in roots(new):o.matrix_world=Matrix.Rotation(-math.pi/2,4,'Z')@o.matrix_world
bpy.context.view_layer.update()
stats={}
for label,obs in [('reference',ref),('before',new)]:
 points=np.array([list(o.matrix_world@v.co) for o in obs if o.type=='MESH' for v in o.data.vertices])
 rec={}
 for name,zlo,zhi,xlimit in [('head',1.37,1.61,.3),('upper_torso',1.12,1.25,.17),('waist',.98,1.10,.25),('hips',.86,.96,.25),('skirt',.75,.84,.3)]:
  a=points[(points[:,2]>zlo)&(points[:,2]<zhi)&(abs(points[:,0])<xlimit)]
  rec[name]={'width':float(np.ptp(a[:,0])),'depth':float(np.ptp(a[:,1])),'bounds':[a.min(0).tolist(),a.max(0).tolist()]}
 for z in [1.0,1.1,1.15,1.2,1.25,1.3,1.35,1.4,1.5]:
  a=points[(abs(points[:,2]-z)<.006)&(abs(points[:,0])<.20)]
  if len(a):rec[str(z)]={'width':float(np.ptp(a[:,0])),'depth':float(np.ptp(a[:,1]))}
 stats[label]=rec
 for o in roots(obs):o.location.x+=-.79 if label=='reference' else .79
stats['images']=[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'size':list(i.size)} for i in bpy.data.images]
(P/'normalized_measurements.json').write_text(json.dumps(stats,indent=2))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1500;scene.render.resolution_y=950;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('CompareWorld');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.3,.3,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
for pos,power,size in [((1,-3,4),450,4),((-3,-1,2),250,3),((0,2,3),350,3)]:
 data=bpy.data.lights.new('Softbox','AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new('Softbox',data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Comparison');cam=bpy.data.objects.new('Comparison',data);scene.collection.objects.link(cam);cam.location=(0,-5,.83);cam.rotation_euler=(Vector((0,0,.83))-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=3.0;scene.camera=cam
scene.view_settings.view_transform='AgX'
for text,x in [('REFERENCE',-.79),('BEFORE',.79)]:
 curve=bpy.data.curves.new(text,'FONT');curve.body=text;curve.align_x='CENTER';curve.size=.065;ob=bpy.data.objects.new(text,curve);scene.collection.objects.link(ob);ob.location=(x,-.3,1.7);ob.rotation_euler=(math.pi/2,0,0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'comparison_aligned.blend'))
scene.render.filepath=str(P/'comparison_before.png');bpy.ops.render.render(write_still=True)
