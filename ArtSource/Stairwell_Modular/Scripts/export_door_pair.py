"""Export independent frame/leaf with hinge pivot and explicit convex collision."""
import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Export'/'DoorPair'
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Models/14_Door/door14_review_v001.blend'))
leaf=next(o for o in bpy.context.scene.objects if o.type=='MESH')
for o in list(bpy.context.scene.objects):
    if o!=leaf: bpy.data.objects.remove(o,do_unlink=True)
leaf.name='SM_Stairwell_DoorLeaf14'
# Preserve UV and front silhouette; use physical door dimensions instead of generated scale.
for v in leaf.data.vertices:
    p=leaf.matrix_world@v.co
    p.x=p.x/1.10283351*.988-.5
    p.z=p.z/2.1*2.094+1.05
    # Body thickness 4cm, knobs project 5cm on each side.
    y=p.y; a=abs(y)
    p.y=(1 if y>=0 else -1)*(.02*min(a/.04975587,1)+max(0,a-.04975587)*(.05/.1036234))+.02
    v.co=p
leaf.matrix_world.identity()
leaf.data.update()
for m in leaf.data.materials:
    if m and m.node_tree:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image:
                n.image.filepath_raw=str(OUT/'T_Stairwell_Door14_BaseColor.png'); n.image.file_format='PNG'; n.image.save()
def box(name,loc,size):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object; o.name=name; o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o
lc=box('UCX_SM_Stairwell_DoorLeaf14_00',(-.5,.02,1.05),(.988,.04,2.094))
frame_parts=[box('FrameLeft',(-1.025,.02,1.075),(.05,.15,2.15)),box('FrameRight',(.025,.02,1.075),(.05,.15,2.15)),box('FrameTop',(-.5,.02,2.125),(1,.15,.05))]
bpy.ops.object.select_all(action='DESELECT')
for o in frame_parts: o.select_set(True)
bpy.context.view_layer.objects.active=frame_parts[0]; bpy.ops.object.join()
frame=bpy.context.object; frame.name='SM_Stairwell_DoorFrame13'
bpy.context.scene.cursor.location=(0,0,0); bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
fc=[box('UCX_SM_Stairwell_DoorFrame13_00',(-1.025,.02,1.075),(.05,.15,2.15)),box('UCX_SM_Stairwell_DoorFrame13_01',(.025,.02,1.075),(.05,.15,2.15)),box('UCX_SM_Stairwell_DoorFrame13_02',(-.5,.02,2.125),(1,.15,.05))]
for mesh,colliders in [(leaf,[lc]),(frame,fc)]:
    bpy.ops.object.select_all(action='DESELECT')
    for o in [mesh]+colliders: o.select_set(True)
    bpy.context.view_layer.objects.active=mesh
    bpy.ops.export_scene.fbx(filepath=str(OUT/(mesh.name+'.fbx')),use_selection=True,object_types={'MESH'},add_leaf_bones=False,apply_unit_scale=True,axis_forward='-Y',axis_up='Z',bake_anim=False)
for o in [lc]+fc: o.hide_render=True; o.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'door_pair_source.blend'))
leaf.data.calc_loop_triangles()
report=dict(leaf_triangles=len(leaf.data.loop_triangles),opening_cm=[100,210],leaf_body_cm=[98.8,4,209.4],clearance_cm=.6,pivot='Right hinge at origin, bottom Z=0. Local leaf extends toward negative X; front is negative Y.',frame_collision_hulls=3,leaf_collision_hulls=1,frame_source='Procedural fitted frame based on approved asset 13; not Tripo generated',material='Leaf basecolor from Tripo; frame uses constant painted metal',status='ready_for_unreal_import')
(OUT/'export_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DOOR_PAIR_EXPORTED',json.dumps(report))
