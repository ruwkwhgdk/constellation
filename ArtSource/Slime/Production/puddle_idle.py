"""Exportable bone-driven, grounded liquid skirt waves."""
import bpy,math

def animate_puddle(scene,body,rig):
    names=[f'puddle_{i:02}' for i in range(8)]
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for i,name in enumerate(names):
        if name not in rig.data.edit_bones:
            a=i*math.tau/8
            b=rig.data.edit_bones.new(name)
            b.head=(.8*math.cos(a),.7*math.sin(a),0)
            b.tail=(b.head.x,b.head.y,.15)
            b.parent=rig.data.edit_bones['root']
    bpy.ops.object.mode_set(mode='OBJECT')
    # Replace only the original root contribution on the skirt; retain upper-body weights.
    groups=[body.vertex_groups.get(n) or body.vertex_groups.new(name=n) for n in names]
    root=body.vertex_groups['root']
    for v in body.data.vertices:
        x,y,z=v.co
        radial=math.sqrt((x/1.05)**2+(y/.85)**2)
        influence=max(0,min(1,(.26-z)/.19))*max(0,min(1,(radial-.45)/.35))
        original=sum(g.weight for g in v.groups if g.group in [root.index]+[q.index for q in groups])
        if original<1e-8:continue
        a=(math.atan2(y/.85,x/1.05)%math.tau)/math.tau*8
        index=int(a)%8;t=a-int(a)
        for g in groups:
            try:g.remove([v.index])
            except RuntimeError:pass
        root.add([v.index],original*(1-influence),'REPLACE')
        groups[index].add([v.index],original*influence*(1-t),'REPLACE')
        groups[(index+1)%8].add([v.index],original*influence*t,'REPLACE')
    for f in range(1,98):
        q=(f-1)/96
        for i,name in enumerate(names):
            a=i*math.tau/8;wave=math.sin(math.tau*q-a)
            pb=rig.pose.bones[name]
            # Bone local Y is world Z. Zero-height vertices remain on the ground.
            pb.scale=(1+.045*wave,1+.20*math.sin(math.tau*q-a+.8),1+.045*wave)
            pb.location=(.012*math.cos(a)*wave,0,-.012*math.sin(a)*wave)
            pb.keyframe_insert('scale',frame=f,group=name)
            pb.keyframe_insert('location',frame=f,group=name)
    scene.frame_set(1)
