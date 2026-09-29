import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'renders';OUT.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'source/anime+character+3d+model.fbx'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.context.view_layer.update()
original_matrix=[list(r) for r in o.matrix_world]
# Presentation transform only: compensate the imported quarter-turn.
# Imported world transform is already upright after dependency-graph update.
bpy.context.view_layer.update()
pts=[o.matrix_world@v.co for v in o.data.vertices]
mins=Vector([min(p[i] for p in pts) for i in range(3)]);maxs=Vector([max(p[i] for p in pts) for i in range(3)])
center=(mins+maxs)/2;height=maxs.z-mins.z
bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
seen=set();components=[]
for v in bm.verts:
    if v.index in seen:continue
    stack=[v];seen.add(v.index);count=0
    while stack:
        q=stack.pop();count+=1
        for e in q.link_edges:
            n=e.other_vert(q)
            if n.index not in seen:seen.add(n.index);stack.append(n)
    components.append(count)
report={'source':'anime character 3d model.zip','vertices':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'meshes':1,'armatures':sum(x.type=='ARMATURE' for x in bpy.context.scene.objects),'uv_layers':[u.name for u in o.data.uv_layers],'materials':len(o.data.materials),'connected_component_vertex_counts':sorted(components,reverse=True),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'original_object_matrix':original_matrix,'presentation_rotation':'Imported transform preserved; source file unchanged','upright_bounds':[list(mins),list(maxs)],'images':[{'name':i.name,'size':list(i.size),'path':i.filepath} for i in bpy.data.images if i.source=='FILE'],'material_nodes':[]}
bm.free()
for m in o.data.materials:
    report['material_nodes'].append({'name':m.name,'nodes':[n.type for n in m.node_tree.nodes],'links':[(l.from_node.type,l.from_socket.name,l.to_node.type,l.to_socket.name) for l in m.node_tree.links]})
(ROOT/'source_audit.json').write_text(json.dumps(report,indent=2))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=24
sc.render.resolution_x=900;sc.render.resolution_y=1100;sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX';sc.world.color=(.25,.25,.25)
def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
for name,relative,power in [('Key',(-1.8,-2.6,2.2),110),('Fill',(1.8,-1.5,.8),70),('Rim',(0,2,1.7),140)]:
    bpy.ops.object.light_add(type='AREA',location=center+Vector(relative)*height);l=bpy.context.object;l.name=name;l.data.energy=power*height*height;l.data.size=height*2;aim(l,center)
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=height*1.25
for name,rel in [('front',(0,-3,0)),('back',(0,3,0)),('side',(3,0,0)),('three_quarter',(2,-3,0))]:
    cam.location=center+Vector(rel)*height;aim(cam,center);sc.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
target=center+Vector((0,0,height*.34));cam.location=target+Vector((0,-3,0))*height;aim(cam,target);cam.data.ortho_scale=height*.30
sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.filepath=str(OUT/'face.png');bpy.ops.render.render(write_still=True)
cam.location=center+Vector((0,-3,0))*height;aim(cam,center);cam.data.ortho_scale=height*1.25
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Tripo_Source_Inspection.blend'))
print('SOURCE_INSPECTION_COMPLETE',json.dumps(report))
