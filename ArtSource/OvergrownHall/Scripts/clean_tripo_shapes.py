"""Source-guided architectural retopology, Tripo color bake, organic cleanup.

Architecture is rebuilt to the adopted Tripo dimensions and silhouettes; this
is deliberate retopology, not a claim that smoothing can restore straight edges.
Original sources remain untouched. Organic geometry retains original topology/UV.
"""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'TripoReplacement/v005'; OUT.mkdir(parents=True,exist_ok=True)
ROWS=json.loads((ROOT/'TripoReplacement/v002/kit_manifest.json').read_text())
ROWS += [dict(id='02',name='Pillar',dimensions_m=[.65,.65,3],budget=12000),dict(id='19',name='Tree',dimensions_m=[5.210341,4.571686,6],budget=30000)]
REPORT=[]

def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o

def box(parts,center,dims,bevel=.008):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    o=bpy.context.object;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Small readable bevel','BEVEL');m.width=bevel;m.segments=2
        bpy.ops.object.modifier_apply(modifier=m.name)
    parts.append(o);return o

def rod(parts,a,b,width,depth=None):
    a,b=Vector(a),Vector(b);d=b-a
    o=box(parts,(a+b)/2,(width,depth or width,d.length),min(width*.12,.006))
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return o

def arc(parts,rx,rz,zbase,thickness,depth,segments=32):
    # Closed rectangular cross-section arch; hard front/side edges, smooth curve.
    verts=[];faces=[]
    for i in range(segments+1):
        t=math.pi*i/segments
        for radx,radz,y in [(rx,rz,-depth/2),(rx-thickness,rz-thickness,-depth/2),(rx-thickness,rz-thickness,depth/2),(rx,rz,depth/2)]:
            verts.append((radx*math.cos(t),y,zbase+radz*math.sin(t)))
    for i in range(segments):
        for j in range(4): faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    faces += [(3,2,1,0),(segments*4,segments*4+1,segments*4+2,segments*4+3)]
    me=bpy.data.meshes.new('ArchRetopology');me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new('Arch',me);bpy.context.collection.objects.link(o);parts.append(o)
    activate(o);m=o.modifiers.new('Arch edge bevel','BEVEL');m.width=min(.008,thickness*.12);m.segments=2
    bpy.ops.object.modifier_apply(modifier=m.name)

def architecture(key,d):
    p=[];w,depth,h=d
    if key in ['01','03']:
        # Stepped plinth/capital copied from the source's major profile.
        tiers=[(0,.10,1),(.10,.22,.90),(.22,.84,.73),(.84,.92,.87),(.92,1,1)] if key=='01' else [(0,.13,.80),(.13,.60,.68),(.60,.76,.84),(.76,1,1)]
        for low,high,scale in tiers:box(p,(0,0,(low+high)*h/2),(w*scale,depth*scale,(high-low)*h),.012)
        if key=='01':
            for x in [-1,1]:box(p,(x*w*.31,-depth*.38,h*.53),(w*.08,depth*.06,h*.55),.004)
    elif key=='02':
        box(p,(0,0,h/2),(w,depth,h),.012)
    elif key in ['04','12']:
        zspring=h*.73 if key=='04' else h*.64
        rx=w*.47;rz=h-zspring-.035
        thick=w*.13 if key=='04' else w*.15
        for side in [-1,1]:
            box(p,(side*(rx-thick/2),0,zspring/2),(thick,depth,zspring),.012)
            box(p,(side*(rx-thick/2),0,.075),(thick*1.16,depth*1.08,.15),.012)
            box(p,(side*(rx-thick/2),0,zspring-.06),(thick*1.20,depth*1.12,.12),.008)
        arc(p,rx,rz,zspring,thick,depth)
        if key=='04':box(p,(0,0,h-.055),(w,depth*1.03,.11),.008)
    elif key=='05':
        box(p,(0,0,h*.46),(w,depth*.84,h*.92),.01)
        box(p,(0,0,h-.055),(w,depth,.11),.009)
        box(p,(0,0,.045),(w,depth*.96,.09),.006)
    elif key=='06':
        t=.055
        for x in [-w/2+t/2,w/2-t/2]:box(p,(x,0,h/2),(t,depth,h),.004)
        for z in [t/2,h-t/2]:box(p,(0,0,z),(w,depth,t),.004)
        for x in [-w/4,0,w/4]:box(p,(x,0,h/2),(.038,depth*.66,h-t*2),.003)
        for z in [h/4,h/2,3*h/4]:box(p,(0,0,z),(w-t*2,depth*.70,.038),.003)
    elif key=='07':
        arc(p,w/2,h-.025,.025,.055,depth)
        box(p,(0,0,.025),(w,depth,.05),.003)
        for x in [-w/4,0,w/4]:
            high=(h-.08)*math.sqrt(max(0,1-(x/(w/2-.055))**2))+.025
            box(p,(x,0,(high+.05)/2),(.038,depth*.66,high-.05),.002)
    elif key=='08':box(p,(0,0,h/2),(w,depth,h),.004)
    elif key in ['09','11']:
        box(p,(0,0,h/2),(w,depth,h),.009)
        # Restrained terminal damage only, no wavy structural span.
        if key=='11':
            for v in p[0].data.vertices:
                if v.co.x>w*.38:v.co.x-=.045*(.5+.5*math.sin(v.co.z*41+v.co.y*23))
    elif key=='10':
        rod(p,(-w/2,0,.05),(w/2,0,.05),.085,depth)
        rod(p,(-w/2,0,.05),(0,0,h-.05),.09,depth)
        rod(p,(0,0,h-.05),(w/2,0,.05),.09,depth)
        rod(p,(0,0,.05),(0,0,h-.05),.11,depth)
    elif key in ['13','26']:
        if key=='13':
            for x in [-w/4,w/4]:
                for y in [-depth/4,depth/4]:box(p,(x,y,h/2),(w/2-.009,depth/2-.009,h),.006)
        else:
            for i in range(6):box(p,(-w/2+w*(i+.5)/6,0,h/2),(w/6-.012,depth,h),.004)
    elif key=='14':
        # Original slatted wooden bench silhouette and 180 cm seating scale.
        for z in [.60,.73,.86]:box(p,(0,depth*.36,z),(w,.045,.105),.009)
        for y in [-depth*.33,0,depth*.33]:box(p,(0,y,.43),(w,depth*.29,.065),.008)
        for x in [-w*.39,w*.39]:
            for y in [-depth*.31,depth*.31]:box(p,(x,y,.205),(.055,.06,.41),.005)
            box(p,(x,depth*.37,.63),(.05,.05,.53),.004)
            box(p,(x,0,.37),(.06,depth*.80,.07),.005)
    elif key=='25':
        for x in [-w/2+.04,w/2-.04]:
            box(p,(x,0,h/2),(.06,depth*.7,h),.005)
            box(p,(x,0,.02),(.12,depth,.04),.004)
        for z in [.10,.36,.63,.88]:box(p,(0,0,z*h),(w-.07,.035,.035),.003)
    else:raise ValueError(key)
    bpy.ops.object.select_all(action='DESELECT')
    for o in p:o.select_set(True)
    bpy.context.view_layer.objects.active=p[0];bpy.ops.object.join();o=bpy.context.object
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    # Exact original module extents and ground pivot keep existing placements valid.
    co=np.array([v.co[:] for v in o.data.vertices]);lo=co.min(axis=0);hi=co.max(axis=0)
    co=(co-(lo+hi)/2)*np.array(d)/(hi-lo);co[:,2]+=h/2
    for v,xyz in zip(o.data.vertices,co):v.co=xyz
    return o

def recalc(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()

def render_shape(o,path):
    scene=bpy.context.scene
    for other in scene.objects:other.hide_render=other!=o
    lo=Vector([min(v.co[i] for v in o.data.vertices) for i in range(3)]);hi=Vector([max(v.co[i] for v in o.data.vertices) for i in range(3)])
    center=(lo+hi)/2;size=max(hi-lo)
    bpy.ops.object.camera_add(location=center+Vector((1,-3,.9))*size)
    cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=size*1.25;scene.camera=cam
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.59,.63,.55)
    scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH'
    scene.render.resolution_x=600;scene.render.resolution_y=600;scene.render.resolution_percentage=100;scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)

for row in ROWS:
    key=row['id'];folder=OUT/(key+'_'+row['name']);folder.mkdir(exist_ok=True)
    if (folder/'inspection.json').exists():
        REPORT.append(json.loads((folder/'inspection.json').read_text()));continue
    sourcefolder=ROOT/('TripoReplacement/v001/'+row['name'] if key in ['02','19'] else 'TripoReplacement/v002/'+key+'_'+row['name'])
    bpy.ops.wm.open_mainfile(filepath=str(sourcefolder/'prepared.blend'))
    bpy.context.preferences.filepaths.save_version=0
    source=next(o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.startswith('UCX_'))
    for other in list(bpy.context.scene.objects):
        if other!=source:bpy.data.objects.remove(other,do_unlink=True)
    source.hide_set(False);source.hide_render=False;activate(source)
    before=sum(len(p.vertices)-2 for p in source.data.polygons)
    render_shape(source,folder/'before.png')
    organic=key in ['15','16','17','18','19']
    if organic:
        obj=source
        coords=np.array([v.co[:] for v in obj.data.vertices]);lo=coords.min(axis=0);hi=coords.max(axis=0)
        activate(obj)
        m=obj.modifiers.new('Remove tiny silhouette spikes','SMOOTH');m.factor=.42;m.iterations=3 if key!='15' else 2
        bpy.ops.object.modifier_apply(modifier=m.name)
        # Bound the edit to local details, preserving the tree/branch architecture.
        maxmove=.035 if key=='19' else .018 if key in ['16','18'] else .03
        moved=np.array([v.co[:] for v in obj.data.vertices]);delta=moved-coords
        lengths=np.linalg.norm(delta,axis=1);scale=np.minimum(1,maxmove/np.maximum(lengths,1e-8));moved=coords+delta*scale[:,None]
        nlo=moved.min(axis=0);nhi=moved.max(axis=0);moved=(moved-nlo)/(nhi-nlo)*(hi-lo)+lo
        for v,xyz in zip(obj.data.vertices,moved):v.co=xyz
        # Keep flat/smooth distinctions for rubble; organic leaves use smooth normals.
        if key!='15':
            for face in obj.data.polygons:face.use_smooth=True
        edits=['bounded local spike smoothing; original topology and UV retained']
        texture=None
    else:
        obj=architecture(key,row['dimensions_m']);activate(obj);recalc(obj)
        for poly in obj.data.polygons:poly.use_smooth=False
        # Re-bake the original Tripo base color into the clean topology's new UV.
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
        material=bpy.data.materials.new('CleanBaked_'+key);material.use_nodes=True
        obj.data.materials.clear();obj.data.materials.append(material)
        target=bpy.data.images.new('CleanColor_'+key,width=1024,height=1024,alpha=False)
        nodes=material.node_tree.nodes;image=nodes.new('ShaderNodeTexImage');image.image=target;nodes.active=image
        srcmat=bpy.data.materials.new('SourceColorBake');srcmat.use_nodes=True;source.data.materials.clear();source.data.materials.append(srcmat)
        ns=srcmat.node_tree.nodes;ns.clear();out=ns.new('ShaderNodeOutputMaterial');emit=ns.new('ShaderNodeEmission');tex=ns.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(sourcefolder/'basecolor.png'),check_existing=True)
        srcmat.node_tree.links.new(tex.outputs['Color'],emit.inputs['Color']);srcmat.node_tree.links.new(emit.outputs[0],out.inputs['Surface'])
        scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.device='CPU'
        scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.30 if key not in ['04','12'] else .55;scene.render.bake.max_ray_distance=1.2;scene.render.bake.margin=12
        source.hide_render=False;activate(obj);source.select_set(True)
        bpy.ops.object.bake(type='EMIT')
        # Missing rays on new edge bevels get source-average pigment, not black.
        pixels=np.empty(1024*1024*4,dtype=np.float32);target.pixels.foreach_get(pixels);pixels=pixels.reshape(-1,4)
        missing=np.max(pixels[:,:3],axis=1)<.003
        valid=pixels[~missing,:3];fill=np.median(valid,axis=0) if len(valid) else np.array([.3,.32,.25])
        pixels[missing,:3]=fill;pixels[:,3]=1;target.pixels.foreach_set(pixels.ravel())
        target.filepath_raw=str(folder/'basecolor.png');target.file_format='PNG';target.save()
        material.node_tree.links.new(image.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
        nodes.get('Principled BSDF').inputs['Roughness'].default_value=.87
        bpy.data.objects.remove(source,do_unlink=True);texture='basecolor.png'
        edits=['source-guided hard-surface retopology','straight edges and planar faces','small 2-segment bevels','Tripo base color reprojected to new UV','normal map intentionally omitted: old tangent basis is invalid']
    obj.name='SM_OH_Clean_'+key+'_'+row['name'];recalc(obj);activate(obj)
    obj.hide_render=False
    render_shape(obj,folder/'after.png')
    activate(obj)
    bpy.ops.export_scene.fbx(filepath=str(folder/(obj.name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'clean.blend'))
    coords=np.array([v.co[:] for v in obj.data.vertices]);assert np.isfinite(coords).all()
    bm=bmesh.new();bm.from_mesh(obj.data);boundary=sum(e.is_boundary for e in bm.edges);bm.free()
    triangles=sum(len(p.vertices)-2 for p in obj.data.polygons)
    assert triangles<=row['budget'],(key,triangles,row['budget'])
    report=dict(id=key,name=row['name'],mesh=obj.name,source=str(sourcefolder/'prepared.blend'),source_triangles=before,triangles=triangles,budget=row['budget'],dimensions_m=list(coords.max(axis=0)-coords.min(axis=0)),boundary_edges=boundary,basecolor=texture,organic=organic,edits=edits)
    (folder/'inspection.json').write_text(json.dumps(report,indent=2));REPORT.append(report)
    print('SHAPE_CLEANED',key,triangles,flush=True)
(OUT/'shape_manifest.json').write_text(json.dumps(REPORT,indent=2));print('ALL_SHAPES_COMPLETE',len(REPORT),flush=True)
