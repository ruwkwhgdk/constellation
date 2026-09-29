import bpy, bmesh, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Models'/'15_Light'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'light15_review_v001.blend'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
before=0; after=0; rows=[]
for o in objects:
    o.data.calc_loop_triangles(); before+=len(o.data.loop_triangles)
    # GLB splits attribute seams; coincident geometry can be merged while UV loops remain.
    bm=bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    bpy.context.view_layer.objects.active=o
    mod=o.modifiers.new('Review_Budget_3000','DECIMATE'); mod.ratio=.865
    bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.calc_loop_triangles(); tris=len(o.data.loop_triangles); after+=tris
    bm=bmesh.new(); bm.from_mesh(o.data)
    rows.append({'name':o.name,'triangles':tris,'vertices':len(o.data.vertices),
                 'boundary_edges':sum(e.is_boundary for e in bm.edges),
                 'uv_layers':len(o.data.uv_layers),'material_slots':len(o.material_slots)})
    bm.free()
assert after<=3000,after
scene=bpy.context.scene; cam=scene.camera
for name,loc in [('light15_v002_view_a.png',(1.25,-1.75,1.25)),('light15_v002_view_b.png',(-1.25,1.75,-1.25))]:
    cam.location=loc; cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/name); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'light15_review_v002.blend'))
report={'before_triangles':before,'after_triangles':after,'limit':3000,'face_limit_pass':after<=3000,
        'objects':rows,'status':'awaiting_user_review',
        'known_visual_issue':'Dark stretched mark on upper housing; needs surface correction or explicit acceptance',
        'not_done':['Emission material separation','Unreal import/collision/light setup','Remaining kit assets']}
(OUT/'inspection_v002.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('LIGHT15_BUDGET_PASS',after)
