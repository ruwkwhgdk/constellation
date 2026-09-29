"""Retain Tripo stems; replace jagged leaf shells with bowed, crossed painted leaf cards."""
import bpy,bmesh,numpy as np,json,random,math
from pathlib import Path
from mathutils import Vector,Euler
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall');OUT=ROOT/'TripoReplacement/v010';reports=[]
def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def export(o,name):
    activate(o);o.name=name;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
def cards(points,material,size,seed):
    rng=random.Random(seed);vertices=[];faces=[];uvs=[];normals=[]
    for center in points:
        center=Vector(center);s=size*rng.uniform(.82,1.2)
        for j in range(3):
            rot=Euler((rng.uniform(-.45,.45),j*math.pi/3+rng.uniform(-.2,.2),rng.uniform(0,math.tau))).to_matrix()
            start=len(vertices)
            for y in range(3):
                for x in range(3):
                    local=Vector(((x/2-.5)*s,(y/2-.5)*s,.07*s*(1-(x-1)**2)*(1-(y-1)**2)))
                    vertices.append(center+rot@local);uvs.append((x/2,y/2))
                    normal=Vector((center.x*.25,center.y*.25,1.3)).normalized();normals.append(normal)
            for y in range(2):
                for x in range(2):
                    a=start+y*3+x;faces.append((a,a+1,a+4,a+3))
    mesh=bpy.data.meshes.new('PaintedLeafCards');mesh.from_pydata(vertices,[],faces);mesh.update();obj=bpy.data.objects.new('LeafCards',mesh);bpy.context.collection.objects.link(obj)
    uv=mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
    for p in mesh.polygons:p.use_smooth=True
    mesh.normals_split_custom_set_from_vertices(normals);obj.data.materials.append(material);return obj
def render(o,path):
    scene=bpy.context.scene
    for other in scene.objects:other.hide_render=other!=o
    lo=Vector([min(v.co[i] for v in o.data.vertices) for i in range(3)]);hi=Vector([max(v.co[i] for v in o.data.vertices) for i in range(3)]);center=(lo+hi)/2;size=max(hi-lo)
    bpy.ops.object.camera_add(location=center+Vector((1,-3,.55))*size);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.22;scene.camera=cam
    bpy.ops.object.light_add(type='SUN',location=(3,-4,8));sun=bpy.context.object;sun.data.energy=2;sun.rotation_euler=(.4,-.5,-.4)
    if scene.world is None:scene.world=bpy.data.worlds.new('FoliageReviewWorld')
    scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.35,.42,.48,1);scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.5
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.filepath=str(path);scene.render.film_transparent=False;bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True);bpy.data.objects.remove(sun,do_unlink=True)
for key,name,cell,size in [('19','Tree',.32,.72),('17','Shrub',.125,.28)]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'TripoReplacement/v008/{key}_{name}/soft.blend'))
    source=next(o for o in bpy.context.scene.objects if o.type=='MESH');activate(source)
    texpath=ROOT/('TripoReplacement/v001/Tree/basecolor.png' if key=='19' else 'TripoReplacement/v002/17_Shrub/basecolor.png')
    image=bpy.data.images.load(str(texpath),check_existing=True);w,h=image.size;pixels=np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4);uv=source.data.uv_layers.active
    selected=set();bins={}
    for poly in source.data.polygons:
        cs=[]
        for li in poly.loop_indices:
            u,v=uv.data[li].uv;cs.append(pixels[int(v*h)%h,int(u*w)%w,:3])
        c=np.mean(cs,axis=0);center=sum((source.data.vertices[i].co for i in poly.vertices),Vector())/len(poly.vertices)
        if c[1]>c[0]*1.015 and c[1]>c[2]*1.08 and center.z>(1.4 if key=='19' else .12):
            selected.add(poly.index);bucket=tuple(math.floor(v/cell) for v in center);bins.setdefault(bucket,[]).append(center.copy())
    points=[sum(ps,Vector())/len(ps) for ps in bins.values() if len(ps)>=7]
    assert len(points)>25
    mat=bpy.data.materials.new('PaintedLeaves');mat.use_nodes=True;nodes=mat.node_tree.nodes;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.95
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'painted_leaves.png'),check_existing=True);mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
    leaves=cards(points,mat,size,int(key))
    if key=='19':
        crown=cards([p-Vector((0,0,3.25)) for p in points if p.z>=3.25],mat,size,119);export(crown,'SM_OH_PaintedCrown');bpy.data.objects.remove(crown,do_unlink=True)
    stem=source.copy();stem.data=source.data.copy();bpy.context.collection.objects.link(stem)
    bm=bmesh.new();bm.from_mesh(stem.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index in selected],context='FACES');bm.to_mesh(stem.data);bm.free()
    leaves.data.materials.append(source.data.materials[0]);activate(leaves);stem.select_set(True);bpy.ops.object.join();result=bpy.context.object
    source.hide_render=True;source.hide_set(True)
    export(result,'SM_OH_Painted'+name);render(result,OUT/(name+'_painted.png'))
    reports.append(dict(id=key,mesh=result.name,leaf_clusters=len(points),leaf_card_triangles=len(points)*24,total_triangles=sum(len(p.vertices)-2 for p in result.data.polygons),materials=len(result.data.materials),source_stems='Tripo v008',leaf_texture='painted_leaves.png',source_leaf_shells_replaced=True))
(OUT/'painted_shapes.json').write_text(json.dumps(reports,indent=2));print('PAINTED_FOLIAGE_COMPLETE',reports)
