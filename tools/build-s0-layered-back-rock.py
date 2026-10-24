"""Author closed wall-integrated rock candidates; never edits the Unreal map."""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'ArtSource/SchoolOpening/WetFloor/LayeredBackRock/Revision02'
OUT.mkdir(parents=True,exist_ok=True)
assert not (OUT/'LayeredBackRock.blend').exists(), 'Preserve reviewed source'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
mat=bpy.data.materials.new('PreviewStone');mat.diffuse_color=(.14,.18,.19,1)
mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.14,.18,.19,1);bs.inputs['Roughness'].default_value=.85
report=[]
for variant,(width,height) in enumerate([(14.8,11.5),(13.3,8.0)]):
    verts=[];faces=[]
    # Broken, sloping strata: front profile varies across the width; rear embeds in wall.
    levels=[(0,1,-4.4),(.15,.98,-4.25),(.20,.94,-3.7),(.39,.91,-3.55),(.44,.86,-2.9),(.64,.79,-2.6),(.70,.72,-1.65),(.88,.59,-1.4),(1,.44,-.6)]
    n=12
    for layer,(z,span,front) in enumerate(levels):
        for j in range(n):
            if j<9:
                t=j/8
                x=(t-.5)*width*span + .22*math.sin(layer*.9+variant)
                y=front+ .9*math.sin(t*8+variant+layer*.47)+.5*math.cos(t*17+layer*.9)
                zz=z*height+(0 if layer==0 else 1.05*math.sin(t*5+variant)+.6*(t-.5)+.18*math.sin(t*19+layer*.5))
            else:
                t=(j-9)/2
                x=(.5-t)*width*span
                y=6.0;zz=z*height
            verts.append((x,y,zz))
        if layer:
            a=(layer-1)*n;b=layer*n
            for j in range(n):faces.append((a+j,a+(j+1)%n,b+(j+1)%n,b+j))
    faces.extend([tuple(reversed(range(n))),tuple((len(levels)-1)*n+j for j in range(n))])
    mesh=bpy.data.meshes.new('LayeredRock');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('SM_S0_LayeredBackRock_'+str(variant),mesh);scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
    bevel=obj.modifiers.new('Worn strata edges','BEVEL');bevel.width=.045;bevel.segments=2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(obj.data)
    boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
    obj.data.calc_loop_triangles()
    assert boundary==0 and nonmanifold==0 and volume>0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},apply_unit_scale=True,add_leaf_bones=False,axis_forward='-Y',axis_up='Z')
    report.append(dict(name=obj.name,triangles=len(obj.data.loop_triangles),boundary_edges=boundary,nonmanifold_edges=nonmanifold,volume_m3=volume,dimensions_m=list(obj.dimensions)))
    obj.select_set(False);obj.location.x=(variant-.5)*17
bpy.ops.object.camera_add(location=(24,-38,24))
camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,4))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=39;scene.camera=camera
for pos,power,size in [((0,-12,22),7000,15),((-20,5,18),5000,12)]:
    bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=power;light.data.size=size;light.rotation_euler=(Vector((0,0,4))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world.color=(.15,.15,.15);scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.filepath=str(OUT/'Preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'LayeredBackRock.blend'))
(OUT/'audit.json').write_text(json.dumps(report,indent=2))
bpy.ops.render.render(write_still=True)

