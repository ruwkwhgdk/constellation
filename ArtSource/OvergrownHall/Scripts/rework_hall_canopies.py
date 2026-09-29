"""Rebuild rounded leaf volumes from accepted Tripo foliage, retaining original stems."""
import bpy,bmesh,numpy as np,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall');OUT=ROOT/'TripoReplacement/v010';OUT.mkdir(exist_ok=True)
reports=[]
def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def preview(o,path):
    for other in bpy.context.scene.objects:other.hide_render=other!=o
    coords=[o.matrix_world@v.co for v in o.data.vertices];lo=Vector([min(p[i] for p in coords) for i in range(3)]);hi=Vector([max(p[i] for p in coords) for i in range(3)]);center=(lo+hi)/2;size=max(hi-lo)
    bpy.ops.object.camera_add(location=center+Vector((1,-3,.6))*size);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.2
    scene=bpy.context.scene;scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True
    scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
def export(o,name):
    activate(o);o.name=name;bpy.context.preferences.filepaths.save_version=0
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
for key,name,voxel in [('19','Tree',.055),('17','Shrub',.022)]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'TripoReplacement/v008/{key}_{name}/soft.blend'))
    source=next(o for o in bpy.context.scene.objects if o.type=='MESH');activate(source)
    preview(source,OUT/(name+'_before.png'))
    texture=ROOT/('TripoReplacement/v001/Tree/basecolor.png' if key=='19' else 'TripoReplacement/v002/17_Shrub/basecolor.png')
    image=bpy.data.images.load(str(texture),check_existing=True);w,h=image.size;pixels=np.array(image.pixels[:],dtype=np.float32).reshape(h,w,4)
    uv=source.data.uv_layers.active
    leaf_faces=[]
    for poly in source.data.polygons:
        samples=[]
        for li in poly.loop_indices:
            u,v=uv.data[li].uv;samples.append(pixels[int(v*h)%h,int(u*w)%w,:3])
        c=np.mean(samples,axis=0);z=sum(source.data.vertices[i].co.z for i in poly.vertices)/len(poly.vertices)
        if c[1]>c[0]*1.015 and c[1]>c[2]*1.08 and z>(1.4 if key=='19' else .12):leaf_faces.append(poly.index)
    assert len(leaf_faces)>len(source.data.polygons)*.15,(key,len(leaf_faces))
    leafset=set(leaf_faces)
    leaves=source.copy();leaves.data=source.data.copy();bpy.context.collection.objects.link(leaves)
    bm=bmesh.new();bm.from_mesh(leaves.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in leafset],context='FACES');bm.to_mesh(leaves.data);bm.free();activate(leaves)
    # Thicken existing leaf clusters before voxel union; this closes small gaps, not new sphere foliage.
    solid=leaves.modifiers.new('Leaf mass thickness','SOLIDIFY');solid.thickness=voxel*1.5;solid.offset=0;bpy.ops.object.modifier_apply(modifier=solid.name)
    remesh=leaves.modifiers.new('Unify overlapping leaf masses','REMESH');remesh.mode='VOXEL';remesh.voxel_size=voxel;remesh.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=remesh.name)
    smooth=leaves.modifiers.new('Broad rounded leaf contour','SMOOTH');smooth.factor=1.1;smooth.iterations=5;bpy.ops.object.modifier_apply(modifier=smooth.name)
    triangles=sum(len(p.vertices)-2 for p in leaves.data.polygons);target=20000 if key=='19' else 10000
    if triangles>target:
        dec=leaves.modifiers.new('Canopy budget','DECIMATE');dec.ratio=target/triangles;bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in leaves.data.polygons:p.use_smooth=True
    # Transfer only broad source pigment, leaving the rebuilt canopy free of old UV seams.
    source.data.calc_loop_triangles();tris=list(source.data.loop_triangles);tree=BVHTree.FromPolygons([v.co for v in source.data.vertices],[t.vertices for t in tris],all_triangles=True)
    attr=leaves.data.color_attributes.new(name='TripoPigment',type='FLOAT_COLOR',domain='POINT')
    for v in leaves.data.vertices:
        hit,normal,idx,dist=tree.find_nearest(v.co)
        t=tris[idx];coords=[source.data.vertices[i].co for i in t.vertices];uvs=[Vector((*uv.data[i].uv,0)) for i in t.loops]
        sample=barycentric_transform(hit,*coords,*uvs);c=pixels[int(sample.y*h)%h,int(sample.x*w)%w,:3]
        value=float(np.clip(np.mean(c),0,1));color=np.array([.11,.25,.07])*(1-value)+np.array([.46,.65,.20])*value
        attr.data[v.index].color=(*color,1)
    leaves.data.color_attributes.active_color=attr
    mat=bpy.data.materials.new('RoundedLeafPigment');mat.diffuse_color=(.30,.47,.13,1);leaves.data.materials.clear();leaves.data.materials.append(mat)
    # Keep only source stems outside the leaf mask, retaining trunk silhouette and existing UV.
    stem=source.copy();stem.data=source.data.copy();bpy.context.collection.objects.link(stem)
    bm=bmesh.new();bm.from_mesh(stem.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index in leafset],context='FACES');bm.to_mesh(stem.data);bm.free()
    source.hide_render=True;source.hide_set(True)
    # Export canopy separately for the already placed distant crowns.
    if key=='19':
        crown=leaves.copy();crown.data=leaves.data.copy();bpy.context.collection.objects.link(crown)
        for v in crown.data.vertices:v.co.z-=3.25
        export(crown,'SM_OH_RoundedCrown');bpy.data.objects.remove(crown,do_unlink=True)
    # Leaf material first; source trunk uses slot1, its old UV remains available.
    leaves.data.materials.append(source.data.materials[0]);stem.data.materials.clear();stem.data.materials.append(source.data.materials[0])
    activate(leaves);stem.select_set(True);bpy.ops.object.join();result=bpy.context.object
    preview(result,OUT/(name+'_after.png'));export(result,'SM_OH_Rounded'+name)
    coords=np.array([v.co[:] for v in result.data.vertices]);assert np.isfinite(coords).all()
    reports.append(dict(id=key,mesh=result.name,source=str(texture.parent/'prepared.blend'),leaf_faces_selected=len(leaf_faces),source_faces=len(source.data.polygons),voxel_cm=voxel*100,triangles=sum(len(p.vertices)-2 for p in result.data.polygons),material_slots=len(result.data.materials),dimensions_m=(coords.max(0)-coords.min(0)).tolist(),stem_uv_preserved=True,leaf_colors='nearest source pigment, palette softened'))
(OUT/'shapes.json').write_text(json.dumps(reports,indent=2));print('ROUNDED_CANOPIES',reports)
