"""Retain Tripo surface detail while preparing dimensioned game meshes."""
import bpy,json,math,bmesh
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1]/'TripoReplacement/v001'
bpy.context.preferences.filepaths.save_version=0
for kind,target,limit in [('Pillar',3.0,12000),('Tree',6.0,30000)]:
    out=BASE/kind; out.mkdir(exist_ok=True)
    source=next((out/'Original').glob('*.fbx'))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
    bpy.ops.import_scene.fbx(filepath=str(source))
    objs=[o for o in scene.objects if o.type=='MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); obj=bpy.context.object
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    lo=Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)]); hi=Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
    size=hi-lo; center=(lo+hi)/2
    original_triangles=sum(len(p.vertices)-2 for p in obj.data.polygons)
    if kind=='Pillar':
        # Keep the central shaft, preserving the untouched source with its capital/base.
        bm=bmesh.new(); bm.from_mesh(obj.data)
        bottom=lo.z+size.z*.18; top=lo.z+size.z*.80
        for z,normal in [(bottom,(0,0,1)),(top,(0,0,-1))]:
            result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,z),plane_no=normal,clear_inner=True,clear_outer=False)
            edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
            if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
        bm.to_mesh(obj.data); bm.free()
        lo=Vector([min(v.co[i] for v in obj.data.vertices) for i in range(3)]); hi=Vector([max(v.co[i] for v in obj.data.vertices) for i in range(3)])
        size=hi-lo; center=(lo+hi)/2
    factor=Vector((.65/size.x,.65/size.y,target/size.z)) if kind=='Pillar' else Vector((target/size.z,)*3)
    for v in obj.data.vertices:
        v.co=Vector(((v.co.x-center.x)*factor.x,(v.co.y-center.y)*factor.y,(v.co.z-lo.z)*factor.z))
        if kind=='Pillar':
            if v.co.z<.025:v.co.z=0
            elif v.co.z>target-.025:v.co.z=target
    obj.name='SM_OH_Tripo_'+kind
    before=sum(len(p.vertices)-2 for p in obj.data.polygons)
    if before>limit:
        mod=obj.modifiers.new('GameTriangleBudget','DECIMATE'); mod.ratio=(limit-20)/before
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.update()
    textures=[]
    bpy.data.images.load(str(next((out/'Original').rglob('*_rm.JPEG'))))
    for im in bpy.data.images:
        if im.type=='IMAGE' and im.size[0]>0:
            suffix='basecolor' if 'basecolor' in im.name.lower() else 'normal' if 'normal' in im.name.lower() else 'rm' if '_rm' in im.name.lower() else im.name.split('.')[0]
            im.filepath_raw=str(out/(suffix+'.png')); im.file_format='PNG'; im.save(); textures.append(dict(file=suffix+'.png',size=list(im.size)))
    # Material naming survives FBX; UE will use the preserved PBR maps explicitly.
    assert len(obj.data.materials)==1,'Multiple materials require explicit texture mapping'
    obj.data.materials[0].name='M_OH_Tripo_'+kind
    count=sum(len(p.vertices)-2 for p in obj.data.polygons)
    assert count<=limit and len(obj.data.uv_layers)>0
    assert all(math.isfinite(x) for v in obj.data.vertices for x in v.co)
    dims=[max(v.co[i] for v in obj.data.vertices)-min(v.co[i] for v in obj.data.vertices) for i in range(3)]
    # Simple trunk/shaft collision, not per-leaf collision.
    bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,1.5 if kind=='Pillar' else 1.3))
    col=bpy.context.object; col.name='UCX_'+obj.name+'_00'; col.dimensions=(.65,.65,3) if kind=='Pillar' else (.40,.40,2.6)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); col.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(out/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,bake_anim=False)
    col.hide_render=True; col.hide_set(True)
    scene.world=bpy.data.worlds.new('World'); scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    center=Vector((0,0,target/2)); size=max(dims)
    for offset,power in [((1,-2,3),500),((-2,1,2),350)]:
        pos=center+Vector(offset)*size
        bpy.ops.object.light_add(type='AREA',location=pos); light=bpy.context.object; light.data.energy=power*size*size; light.data.size=size*2
        light.rotation_euler=(center-pos).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=center+Vector((2,-3,1))*size); cam=bpy.context.object
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=size*1.25; scene.camera=cam
    scene.render.engine='CYCLES'; scene.cycles.samples=20; scene.render.resolution_x=800; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.filepath=str(out/'review.png'); bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'prepared.blend'))
    report=dict(kind=kind,source_triangles=original_triangles,game_triangles=count,dimensions_m=dims,uv_layers=len(obj.data.uv_layers),textures=textures,collision='one simple box',edits=['base-centered ground pivot','dimension normalization','central shaft isolated; cut ends capped and flattened' if kind=='Pillar' else 'uniform scaling'],adoption='pending user appearance review')
    (out/'inspection.json').write_text(json.dumps(report,indent=2))
    print('TRIPO_ENV_PREPARED',json.dumps(report))
