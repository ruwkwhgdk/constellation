"""Prepare downloaded Tripo sources, preserving originals and UV detail."""
import bpy,bmesh,csv,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
BASE=Path(__file__).resolve().parents[1]/'TripoReplacement/v002'
SPECS={'01':(.8,.85,1.2,8000),'03':(.95,1,.5,8000),'04':(3.7,.4,7.1,12000),'05':(3,.4,1.5,6000),'06':(2.3,.14,4.3,12000),'07':(2.3,.14,1.2,8000),'08':(.07,.1,3,2000),'09':(4,.5,.4,6000),'10':(12.7,.22,2,12000),'11':(1.5,.3,.35,6000),'12':(1.7,.5,2.2,10000),'13':(2,2,.15,4000),'14':(1.8,.65,.9,12000),'15':(1.2,1,.45,8000),'16':(.7,.7,.45,9000),'17':(1.5,1.3,1.2,15000),'18':(.65,.15,2,12000),'25':(2,.12,1,8000),'26':(3,2,.15,7000)}
def bounds(obj):
    return [Vector([f(v.co[i] for v in obj.data.vertices) for i in range(3)]) for f in [min,max]]
def clip(obj,z,above=True):
    bm=bmesh.new();bm.from_mesh(obj.data)
    result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.000001,plane_co=(0,0,z),plane_no=(0,0,1 if above else -1),clear_inner=True)
    cut=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
    if cut:bmesh.ops.holes_fill(bm,edges=cut,sides=0)
    bm.to_mesh(obj.data);bm.free()
reports=[]
for row in csv.DictReader((BASE/'jobs.csv').open()):
    id=row['id'];out=BASE/(id+'_'+row['name']); dims=Vector(SPECS[id][:3]);limit=SPECS[id][3]
    if '--resume' in sys.argv and (out/'prepared.png').exists():
        reports.append(json.loads((out/'inspection.json').read_text()));continue
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene;scene.unit_settings.system='METRIC'
    bpy.ops.import_scene.fbx(filepath=str(next((out/'Original').glob('*.fbx'))))
    objects=[o for o in scene.objects if o.type=='MESH'];bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    if len(objects)>1:bpy.ops.object.join()
    obj=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    before=sum(len(p.vertices)-2 for p in obj.data.polygons);edits=[]
    if id in ['09','14']:
        obj.data.transform(Matrix.Rotation(math.pi/2,4,'Z'));edits.append('longitudinal axis to X')
    if id=='26':
        obj.data.transform(Matrix.Rotation(math.pi/2,4,'X'));edits.append('roof panel horizontal')
    lo,hi=bounds(obj)
    if id=='07':
        clip(obj,(lo.z+hi.z)*.5);edits.append('upper semicircle isolated for arched window crown')
    if id=='08':
        clip(obj,lo.z+(hi.z-lo.z)*.15);clip(obj,lo.z+(hi.z-lo.z)*.85,False);edits.append('ornamental end plates removed')
    if id=='04':
        bm=bmesh.new();bm.from_mesh(obj.data);c=(lo+hi)/2;s=hi-lo
        remove=[v for v in bm.verts if abs((v.co.x-c.x)/s.x)<.245 and (v.co.z-lo.z)/s.z<.64]
        bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(obj.data);bm.free();edits.append('unwanted central gate removed')
    lo,hi=bounds(obj);s=hi-lo;c=(lo+hi)/2
    for v in obj.data.vertices:v.co=Vector(((v.co.x-c.x)*dims.x/s.x,(v.co.y-c.y)*dims.y/s.y,(v.co.z-lo.z)*dims.z/s.z))
    if id=='13':
        for v in obj.data.vertices:
            if v.co.z>dims.z*.7:v.co.z=dims.z
        edits.append('walkable top flattened')
    # Remove zero-area geometric faces, preserve intended foliage/open framing boundaries.
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.dissolve_degenerate(bm,dist=.000001,edges=list(bm.edges));bm.to_mesh(obj.data);bm.free()
    count=sum(len(p.vertices)-2 for p in obj.data.polygons)
    if count>limit:
        mod=obj.modifiers.new('GameBudget','DECIMATE');mod.ratio=(limit-30)/count;bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.name='SM_OH_T_'+id+'_'+row['name'];obj.data.update()
    assert len(obj.data.materials)==1
    obj.data.materials[0].name='M_OH_T_'+id
    textures=[]
    for suffix in ['basecolor','normal','rm']:
        files=[p for p in (out/'Original').rglob('*') if p.is_file() and p.stem.lower().endswith('_'+suffix)]
        assert len(files)==1,(id,suffix)
        assert (out/(suffix+'.png')).exists();textures.append(suffix+'.png')
    lo,hi=bounds(obj);count=sum(len(p.vertices)-2 for p in obj.data.polygons)
    assert count<=limit and obj.data.uv_layers and all(math.isfinite(x) for v in obj.data.vertices for x in v.co)
    bm=bmesh.new();bm.from_mesh(obj.data);boundaries=sum(e.is_boundary for e in bm.edges);bm.free()
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    if id=='13':
        bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,dims.z/2));col=bpy.context.object;col.name='UCX_'+obj.name+'_00';col.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.export_scene.fbx(filepath=str(out/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    if id=='13':col.hide_render=True;col.hide_set(True)
    report=dict(id=id,name=row['name'],mesh=obj.name,source_triangles=before,triangles=count,budget=limit,dimensions_m=list(hi-lo),boundary_edges=boundaries,uv_layers=len(obj.data.uv_layers),edits=edits,textures=textures)
    reports.append(report);(out/'inspection.json').write_text(json.dumps(report,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'prepared.blend'))
    size=max(dims);center=Vector((0,0,dims.z/2));scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
    for off,power in [((1,-2,3),500),((-2,1,2),350)]:
        p=center+Vector(off)*size;bpy.ops.object.light_add(type='AREA',location=p);l=bpy.context.object;l.data.energy=power*size*size;l.data.size=size*2;l.rotation_euler=(center-p).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=center+Vector((1,-3,.9))*size);cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.3;scene.camera=cam
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.render.resolution_x=400;scene.render.resolution_y=400;scene.render.resolution_percentage=100;scene.render.filepath=str(out/'prepared.png');bpy.ops.render.render(write_still=True)
(BASE/'kit_manifest.json').write_text(json.dumps(reports,indent=2));print('TRIPO_FULL_KIT_READY',len(reports))
