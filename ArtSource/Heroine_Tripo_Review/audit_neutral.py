import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;S=R/'NeutralExpression/Heroine_NeutralExpression.blend';O=R/'NeutralInspection';O.mkdir(exist_ok=True);(O/'renders').mkdir(exist_ok=True)
before=hashlib.sha256(S.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(S));sc=bpy.context.scene;cam=sc.camera;sc.cycles.samples=20
report={'source':str(S),'source_sha256':before,'objects':[],'armatures':[],'images':[]}
for ob in sc.objects:
 if ob.type=='ARMATURE':report['armatures'].append(ob.name)
 if ob.type!='MESH':continue
 me=ob.data;bm=bmesh.new();bm.from_mesh(me)
 rec={'name':ob.name,'vertices':len(me.vertices),'triangles':sum(len(p.vertices)-2 for p in me.polygons),'bounds':[[min(v.co[i] for v in me.vertices),max(v.co[i] for v in me.vertices)] for i in range(3)],'boundary_edges':sum(e.is_boundary for e in bm.edges),'edges_more_than_two_faces':sum(len(e.link_faces)>2 for e in bm.edges),'loose_vertices':sum(not v.link_faces for v in bm.verts),'loose_edges':sum(not e.link_faces for e in bm.edges),'zero_area_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'uv_layers':len(me.uv_layers),'shape_keys':list(me.shape_keys.key_blocks.keys()) if me.shape_keys else [],'modifiers':[(m.name,m.type) for m in ob.modifiers],'materials':[m.name if m else None for m in me.materials]}
 report['objects'].append(rec);bm.free()
for im in bpy.data.images:
 if im.source=='FILE':report['images'].append({'name':im.name,'size':list(im.size),'packed':bool(im.packed_file)})
(O/'mesh_audit.json').write_text(json.dumps(report,indent=2))
def render(name,loc,target,scale,res=(1000,1000)):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.resolution_x,sc.render.resolution_y=res;sc.render.use_border=False;sc.render.filepath=str(O/'renders'/f'{name}.png');bpy.ops.render.render(write_still=True);print('AUDIT_RENDER',name,flush=True)
render('full_front',(0,-3,.5),(0,0,.5),1.13,(1100,1200))
render('full_back',(0,3,.5),(0,0,.5),1.13,(1100,1200))
render('torso',(0,-3,.705),(0,0,.705),.43)
render('head_side',(-3,-.7,.89),(0,0,.89),.26)
render('head_back',(0,3,.89),(0,0,.89),.28)
render('skirt',(0,-3,.505),(0,0,.505),.34)
render('shoes',(0,-3,.067),(0,0,.067),.24)
render('hand_left',(-.42,-3,.79),(-.42,0,.79),.16)
render('hand_right',(.42,-3,.79),(.42,0,.79),.16)
assert hashlib.sha256(S.read_bytes()).hexdigest()==before
print('SOURCE_UNCHANGED',flush=True)
