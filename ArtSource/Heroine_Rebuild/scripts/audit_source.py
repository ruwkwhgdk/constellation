import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reference'; OUT.mkdir(parents=True,exist_ok=True)
SOURCE='C:/Users/User/Desktop/Portfolio/Project Constellation/modeling/player_heroine/Player_Heroine.fbx'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=SOURCE)
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
report={'mesh':mesh.name,'mesh_matrix':[list(r) for r in mesh.matrix_world], 'vertices':len(mesh.data.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'uvs':[u.name for u in mesh.data.uv_layers], 'groups':[g.name for g in mesh.vertex_groups], 'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(rig.matrix_world@b.head_local),'tail':list(rig.matrix_world@b.tail_local)} for b in rig.data.bones], 'images':[{'name':i.name,'path':i.filepath,'size':list(i.size)} for i in bpy.data.images], 'materials':[]}
for mat in mesh.data.materials:
    report['materials'].append({'name':mat.name,'nodes':[{'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in mat.node_tree.nodes]})
(OUT/'source_audit.json').write_text(json.dumps(report,indent=2))
rig.animation_data_clear()
for p in rig.pose.bones: p.matrix_basis.identity()
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=24
sc.render.resolution_x=800; sc.render.resolution_y=1000; sc.render.resolution_percentage=100
sc.world.color=(0.3,0.3,0.3)
sc.view_settings.view_transform='Standard'
def point(o,p): o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for loc,power,size in [((3,-4,5),450,4),((-3,-2,3),300,3),((0,3,4),500,3)]:
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=power; l.data.shape='DISK'; l.data.size=size; point(l,(0,0,1))
bpy.ops.object.camera_add(); cam=bpy.context.object; sc.camera=cam; cam.data.type='ORTHO'; cam.data.ortho_scale=2.2
for name,loc in [('front',(0,-5,1)),('side',(5,0,1)),('back',(0,5,1))]:
    cam.location=loc; point(cam,(0,0,1)); sc.render.filepath=str(OUT/(name+'.png')); bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Source_Inspection.blend'))
print('AUDIT_COMPLETE')
