import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'TripoReplacement/v003';OUT.mkdir(exist_ok=True)
bpy.context.preferences.filepaths.save_version=0
reports=[]
for id,name in [('06','WindowLower'),('04','SideArch')]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/('TripoReplacement/v002/'+id+'_'+name+'/prepared.blend')))
    obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');obj.name='SM_OH_Refined_'+name
    if id=='06':
        # Keep the Tripo outer frame and rebuild a sparse grid from its own straight edge.
        original=obj.copy();original.data=obj.data.copy();bpy.context.scene.collection.objects.link(original)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if abs(v.co.x)<1.04 and .11<v.co.z<4.19],context='VERTS')
        bm.to_mesh(obj.data);bm.free()
        bm=bmesh.new();bm.from_mesh(original.data)
        # Isolate a clean mid-height section of the left outer stile.
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.x> -1.04 or not 1.1<v.co.z<2.9],context='VERTS')
        bm.to_mesh(original.data);bm.free()
        lo=Vector([min(v.co[i] for v in original.data.vertices) for i in range(3)]);hi=Vector([max(v.co[i] for v in original.data.vertices) for i in range(3)]);c=(lo+hi)/2;s=hi-lo
        for v in original.data.vertices:v.co=Vector(((v.co.x-c.x)/s.x,(v.co.y-c.y)/s.y,(v.co.z-c.z)/s.z))
        rods=[]
        for x in [-.575,0,.575]:
            o=original.copy();o.data=original.data.copy();bpy.context.scene.collection.objects.link(o);o.location=(x,0,2.15);o.scale=(.05,.10,4.5);rods.append(o)
        for z in [1.075,2.15,3.225]:
            o=original.copy();o.data=original.data.copy();bpy.context.scene.collection.objects.link(o);o.location=(0,0,z);o.scale=(.05,.10,2.5);o.rotation_euler.y=1.57079632679;rods.append(o)
        bpy.data.objects.remove(original,do_unlink=True)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
        for o in rods:o.select_set(True)
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.join()
    else:
        # Reduce protruding masonry ornament without replacing the Tripo arch silhouette.
        for v in obj.data.vertices:
            if v.co.z>5.1:
                v.co.x=max(-1.66,min(1.66,v.co.x));v.co.y*=.7
        bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new('Reduce sculpted noise','SMOOTH');mod.factor=.4;mod.iterations=4;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(OUT/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
    reports.append(dict(id=id,mesh=obj.name,triangles=sum(len(p.vertices)-2 for p in obj.data.polygons)))
(OUT/'structure_manifest.json').write_text(json.dumps(reports,indent=2));print('STRUCTURE_REFINED',reports)
