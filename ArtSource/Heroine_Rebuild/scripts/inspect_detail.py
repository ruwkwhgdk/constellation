exec(compile(open(__file__.replace('inspect_detail.py','audit_source.py'),encoding='utf-8').read().split('for name,loc in')[0],__file__,'exec'))
pts=[mesh.matrix_world@v.co for v in mesh.data.vertices]
print('BOUNDS',[(min(v[i] for v in pts),max(v[i] for v in pts)) for i in range(3)])
print('RIG',[(b.name,list(rig.matrix_world@b.head_local)) for b in rig.data.bones])
print('IMAGES',[(i.name,i.filepath,list(i.size)) for i in bpy.data.images])
print('LINKS',[(l.from_node.type,l.from_socket.name,l.to_node.type,l.to_socket.name) for l in mesh.data.materials[0].node_tree.links])
sc.cycles.samples=20
for name,loc,target,scale in [('full_front',(0,-5,0),(0,0,0),2.12),('head',(0,-5,.72),(0,0,.72),.55),('head_side',(5,0,.72),(0,0,.72),.55)]:
    cam.location=loc; point(cam,target); cam.data.ortho_scale=scale
    sc.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
