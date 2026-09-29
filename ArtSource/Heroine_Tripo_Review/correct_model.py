"""Conservative, reproducible corrections to the supplied Tripo character.
No remesh, decimation, replacement body parts, or global subdivision."""
import bpy,bmesh,math,json,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'Corrected';OUT.mkdir(exist_ok=True)
for d in ['textures','renders']:(OUT/d).mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Tripo_Source_Inspection.blend'))
bpy.context.preferences.filepaths.save_version=0
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');o.name='Heroine_Tripo_Corrected'
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
srcmat=o.data.materials[0]
source=next(n.image for n in srcmat.node_tree.nodes if n.type=='TEX_IMAGE')
sourcepath=ROOT/'source/anime+character+3d+model.fbm/anime+character+3d+model_basecolor.jpg'
shutil.copy2(sourcepath,OUT/'textures/T_BaseColor_Original.jpg')
source.filepath=str(OUT/'textures/T_BaseColor_Original.jpg')

bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
components=[];seen=set()
for v in bm.verts:
    if v.index in seen:continue
    stack=[v];seen.add(v.index);vs=[];fs=set()
    while stack:
        q=stack.pop();vs.append(q);fs.update(q.link_faces)
        for e in q.link_edges:
            n=e.other_vert(q)
            if n.index not in seen:seen.add(n.index);stack.append(n)
    components.append((vs,fs))
components.sort(key=lambda p:-len(p[0]))
names=['Hair','Cardigan','Skin','Skirt','Stockings','Shoes','Ribbon','Shirt','Eyes','Details']
indices={n:i for i,n in enumerate(names)}
mapping={0:'Hair',1:'Cardigan',2:'Skin',3:'Skirt',4:'Stockings',5:'Stockings',6:'Skin',7:'Skin',8:'Skin',9:'Ribbon',10:'Ribbon',11:'Ribbon',12:'Skin',13:'Eyes',14:'Eyes',15:'Hair',16:'Hair',17:'Hair',18:'Shirt',19:'Shirt',20:'Skin',26:'Hair'}
original_positions={v:v.co.copy() for v in bm.verts}
for ci,(vs,fs) in enumerate(components):
    label=mapping.get(ci,'Details')
    for f in fs:
        use=label;c=f.calc_center_median()
        if ci in [4,5] and c.z<.060:use='Shoes'
        if ci==1 and c.z>.77 and abs(c.x)<.043:use='Shirt'
        f.material_index=indices[use]
    # Slightly relax the lower cardigan silhouette; follow attached buttons.
    if ci==1 or ci in [21,22,23,24,25]:
        for v in vs:
            x,y,z=v.co
            w=math.exp(-((z-.617)/.071)**4)*math.exp(-(abs(x)/.105)**8)
            v.co.x*=1+.035*w;v.co.y*=1+.022*w
    # Original art has a restrained neutral mouth, not raised corners.
    if ci in [2,12,20]:
        for v in vs:
            x,y,z=v.co
            w=math.exp(-((z-.860)/.0038)**2)*math.exp(-((y+.052)/.014)**2)*math.exp(-(abs(x)/.016)**8)
            v.co.z-=.00065*min(1,(abs(x)/.011)**1.5)*w
    # Only relax interior cheek/chin vertices. Preserve all open boundaries.
    if ci==2:
        updates=[]
        for v in vs:
            x,y,z=v.co
            if .829<z<.884 and y<-.023 and not v.is_boundary and all(e.is_manifold for e in v.link_edges):
                ns=[e.other_vert(v).co for e in v.link_edges]
                if ns:
                    avg=sum(ns,Vector())/len(ns);delta=(avg-v.co)*.10
                    if delta.length>.00018:delta=delta.normalized()*.00018
                    updates.append((v,v.co+delta))
        for v,pos in updates:v.co=pos

micro_fragments=[f for ci,(vs,fs) in enumerate(components) if ci>=38 and len(vs)<=16 for f in fs]
micro_count=len(micro_fragments)
bmesh.ops.delete(bm,geom=micro_fragments,context='FACES_ONLY')
degenerate=[f for f in bm.faces if f.calc_area()<1e-12]
removed=len(degenerate)
bmesh.ops.delete(bm,geom=degenerate,context='FACES_ONLY')
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
displacements=[(v.co-original_positions[v]).length for v in bm.verts if v in original_positions]
bm.to_mesh(o.data);bm.free()

# Each semantic region retains the supplied color texture. Correct only warm
# contamination on the hair and ribbon using a smooth color mask, then bake
# the result to a portable albedo map. This is not a relighting bake.
settings={'Hair':(.62,.24),'Cardigan':(.91,.17),'Skin':(.72,.23),'Skirt':(.88,.19),'Stockings':(.76,.27),'Shoes':(.47,.34),'Ribbon':(.67,.25),'Shirt':(.87,.18),'Eyes':(.34,.35),'Details':(.68,.23)}
materials=[];color_outputs=[]
def node(m,kind):return m.node_tree.nodes.new(kind)
def mathnode(m,op,a,b=None):
    n=node(m,'ShaderNodeMath');n.operation=op
    for inp,val in zip(n.inputs,[a,b]):
        if val is not None:
            if isinstance(val,(float,int)):inp.default_value=val
            else:m.node_tree.links.new(val,inp)
    return n.outputs[0]
for name in names:
    m=bpy.data.materials.new('M_'+name);m.use_nodes=True
    shader=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    shader.inputs['Roughness'].default_value,shader.inputs['Specular IOR Level'].default_value=settings[name]
    shader.inputs['Metallic'].default_value=0
    t=node(m,'ShaderNodeTexImage');t.image=source;col=t.outputs['Color']
    if name in ['Hair','Ribbon']:
        sep=node(m,'ShaderNodeSeparateColor');sep.mode='RGB';m.node_tree.links.new(col,sep.inputs[0])
        # Purple/silver pins and cool blue ribbon stripes are outside this mask.
        warm=mathnode(m,'SUBTRACT',sep.outputs['Red'],mathnode(m,'MULTIPLY',sep.outputs['Blue'],1.18))
        mask=mathnode(m,'MULTIPLY',mathnode(m,'MAXIMUM',warm,0),80)
        mask=mathnode(m,'MINIMUM',mask,1)
        mix=node(m,'ShaderNodeMixRGB');mix.blend_type='MIX';m.node_tree.links.new(mask,mix.inputs[0]);m.node_tree.links.new(col,mix.inputs[1])
        mix.inputs[2].default_value=(.017,.012,.024,1) if name=='Hair' else (.025,.068,.125,1)
        col=mix.outputs[0]
    m.node_tree.links.new(col,shader.inputs['Base Color']);materials.append(m);color_outputs.append(col)
region_indices=[p.material_index for p in o.data.polygons]
o.data.materials.clear()
for m in materials:o.data.materials.append(m)
for p,index in zip(o.data.polygons,region_indices):p.material_index=index

sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=1
image=bpy.data.images.new('T_Heroine_BaseColor_Corrected',4096,4096,alpha=False)
image.filepath_raw=str(OUT/'textures/T_Heroine_BaseColor_Corrected.png');image.file_format='PNG'
for m,col in zip(materials,color_outputs):
    out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
    em=node(m,'ShaderNodeEmission');m.node_tree.links.new(col,em.inputs['Color']);m.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
    target=node(m,'ShaderNodeTexImage');target.name='BAKE_TARGET';target.image=image;m.node_tree.nodes.active=target
sc.render.bake.margin=12
bpy.ops.object.bake(type='EMIT');image.save()
for m in materials:
    shader=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL')
    m.node_tree.links.new(shader.outputs['BSDF'],out.inputs['Surface'])
    target=m.node_tree.nodes.get('BAKE_TARGET');m.node_tree.links.new(target.outputs['Color'],shader.inputs['Base Color'])
    for n in list(m.node_tree.nodes):
        if n not in [shader,out,target]:m.node_tree.nodes.remove(n)

# Export a static corrected source model. Rigging is deliberately a later task.
pearlmat=bpy.data.materials.new('M_Pearl');pearlmat.use_nodes=True
ps=next(n for n in pearlmat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');ps.inputs['Base Color'].default_value=(.72,.68,.62,1);ps.inputs['Roughness'].default_value=.34;ps.inputs['Specular IOR Level'].default_value=.3
samples=[v.co for v in o.data.vertices if abs(v.co.x+.363)<.003]
cy=(min(v.y for v in samples)+max(v.y for v in samples))/2;cz=(min(v.z for v in samples)+max(v.z for v in samples))/2
ry=(max(v.y for v in samples)-min(v.y for v in samples))/2+.0014;rz=(max(v.z for v in samples)-min(v.z for v in samples))/2+.0014
beads=[]
for i in range(14):
    a=i/14*2*math.pi
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.0018,location=(-.363,cy+ry*math.cos(a),cz+rz*math.sin(a)))
    bead=bpy.context.object;bead.data.materials.append(pearlmat)
    for p in bead.data.polygons:p.use_smooth=True
    beads.append(bead)
bpy.ops.object.select_all(action='DESELECT')
for bead in beads:bead.select_set(True)
bpy.context.view_layer.objects.active=beads[0];bpy.ops.object.join();bracelet=bpy.context.object;bracelet.name='Heroine_Pearl_Bracelet'
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bracelet.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.export_scene.fbx(filepath=str(OUT/'Heroine_Tripo_Corrected.fbx'),use_selection=True,object_types={'MESH'},bake_anim=False,path_mode='COPY',embed_textures=True,axis_forward='-Z',axis_up='Y')
sc.cycles.samples=32;image.pack()
cam=sc.camera;target=Vector((0,0,.5));cam.location=(0,-3,.5);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.25
sc.render.resolution_x=900;sc.render.resolution_y=1100
for s in bpy.data.screens:
    for a in s.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Heroine_Tripo_Corrected.blend'))
stats={'source_triangles':51898,'corrected_body_triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'corrected_triangles':sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in [o,bracelet]),'vertices':sum(len(ob.data.vertices) for ob in [o,bracelet]),'degenerate_faces_removed':removed,'under_eye_fragment_faces_removed':micro_count,'max_displacement_normalized_units':max(displacements),'material_slots':len(o.data.materials)+1,'uv_layers':[u.name for u in o.data.uv_layers],'rigged':False,'source_texture_unchanged':True,'color_correction':'Warm color contamination masked only in Hair and Ribbon materials, then baked to original UV layout.'}
(OUT/'correction_stats.json').write_text(json.dumps(stats,indent=2))
import sys
if '--skip-renders' in sys.argv:
    print('CORRECTION_COMPLETE',json.dumps(stats))
    sys.exit(0)
for name,loc,target,scale,res in [('front',(0,-3,.5),(0,0,.5),1.25,(900,1100)),('face',(0,-3,.862),(0,0,.862),.30,(1100,1100)),('three_quarter',(2,-3,.5),(0,0,.5),1.25,(900,1100)),('back',(0,3,.5),(0,0,.5),1.25,(900,1100)),('side',(3,0,.5),(0,0,.5),1.25,(900,1100))]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    sc.render.resolution_x,sc.render.resolution_y=res;sc.render.filepath=str(OUT/'renders'/(name+'.png'));bpy.ops.render.render(write_still=True)
print('CORRECTION_COMPLETE',json.dumps(stats))
