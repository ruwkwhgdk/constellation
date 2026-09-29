"""v011: UV-mapped ripple sheet and local, closed architectural break variants."""
import bpy,bmesh,math,json
from pathlib import Path
ROOT=Path('C:/Users/User/Documents/UnrealProjects/Constellation/ArtSource/OvergrownHall')
OUT=ROOT/'TripoReplacement/v011';OUT.mkdir(exist_ok=True)
rows=[]
def active(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def export(o,name,kind):
    active(o);o.name=name;bpy.context.preferences.filepaths.save_version=0
    bm=bmesh.new();bm.from_mesh(o.data)
    boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges);bm.free()
    if kind!='water':assert nonmanifold==0,(name,nonmanifold)
    bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'.blend')))
    rows.append(dict(mesh=name,kind=kind,triangles=sum(len(p.vertices)-2 for p in o.data.polygons),boundary_edges=boundary,nonmanifold_edges=nonmanifold,dimensions_m=list(o.dimensions)))
for variant in ['A','B']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'TripoReplacement/v005/04_SideArch/clean.blend'))
    o=next(o for o in bpy.context.scene.objects if o.type=='MESH');active(o)
    # Break through only an upper shoulder; retain both load-bearing feet and the walk-through.
    sign=1 if variant=='A' else -1
    for i,(x,z,r,stretch) in enumerate([(sign*1.55,5.75,.85,(1.0,2.8,1.0)),(sign*1.72,5.03,.55,(1.0,3.2,1.2))]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=(x,0,z))
        cut=bpy.context.object;cut.scale=stretch;cut.rotation_euler=(.19,.31,.47+i*.7)
        active(o);mod=o.modifiers.new('Irregular through break','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
    # Boolean intersections can leave detached chips. Remove only small elevated islands;
    # the source's large, separate arch/leg sections must stay intact.
    bm=bmesh.new();bm.from_mesh(o.data);pending=set(bm.verts);discard=[];removed=[]
    while pending:
        seed=pending.pop();group={seed};stack=[seed]
        while stack:
            v=stack.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in pending:pending.remove(other);group.add(other);stack.append(other)
        span=[max(v.co[i] for v in group)-min(v.co[i] for v in group) for i in range(3)]
        if min(v.co.z for v in group)>.5 and span[1]<.39 and span[0]*span[1]*span[2]<.12 and max(span)<1.25:
            discard.extend(group);removed.append(span)
    bmesh.ops.delete(bm,geom=discard,context='VERTS');bm.to_mesh(o.data);bm.free()
    export(o,'SM_OH_BrokenArch'+variant,'arch');rows[-1]['removed_floating_islands']=removed
bpy.ops.wm.read_factory_settings(use_empty=True)
# Concentric topology follows the approved outline, with valid UVs and small triangles for WPO.
N=160;R=40;verts=[(0,-7,.022)];faces=[]
for j in range(1,R+1):
    r=j/R
    for i in range(N):
        a=math.tau*i/N
        verts.append((r*6.25*math.cos(a)*(1+.025*math.sin(11*a)),-7-r*(8.6*math.sin(a)+.18*math.sin(13*a)),.022))
for i in range(N):faces.append((0,1+(i+1)%N,1+i))
for j in range(1,R):
    a=1+(j-1)*N;b=1+j*N
    for i in range(N):
        n=(i+1)%N;faces.append((a+i,a+n,b+n,b+i))
mesh=bpy.data.meshes.new('RippleSheet');mesh.from_pydata(verts,[],faces);mesh.update()
uv=mesh.uv_layers.new(name='WaterUV')
for p in mesh.polygons:
    p.use_smooth=True
    for li in p.loop_indices:
        v=mesh.vertices[mesh.loops[li].vertex_index].co;uv.data[li].uv=((v.x+6.5)/13,(-v.y+2)/18)
o=bpy.data.objects.new('RippleSheet',mesh);bpy.context.collection.objects.link(o)
export(o,'SM_OH_RippleSheet','water')
(OUT/'assets.json').write_text(json.dumps(rows,indent=2));print('WATER_RUINS_ASSETS',rows)
