"""Build the adopted modular kit with shared dimensions, UVs, and UCX collision.

Run only through tools/run-blender.ps1. Existing raw sources are never modified.
"""
import bpy, bmesh, math, json, os
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'Production'/'v001'
for p in ['FBX','renders','reports','textures']: (OUT/p).mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
materials={}; specs={}; assets=[]; parts=[]; collision=[]
def material(name,color,metal=0,rough=.7,noise=True,emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; p=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    if noise:
        tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=45; tex.inputs['Detail'].default_value=3
        coord=n.new('ShaderNodeTexCoord'); l.new(coord.outputs['Object'],tex.inputs['Vector'])
        mix=n.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[0].default_value=.28; mix.inputs[1].default_value=(*color,1)
        l.new(tex.outputs['Fac'],mix.inputs[2]); l.new(mix.outputs[0],p.inputs['Base Color'])
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.15; bump.inputs['Distance'].default_value=.001
        l.new(tex.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs[0],p.inputs['Normal'])
    if emission: p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    materials[name]=m; specs[name]=dict(color=color,metallic=metal,roughness=rough,noise=noise,emission=emission)
    return m
concrete=material('M_Kit_Concrete',(.27,.29,.30),rough=.88)
grout=material('M_Kit_Grout',(.12,.14,.14),rough=.95)
floor=material('M_Kit_FloorTile',(.43,.47,.47),rough=.67)
wall=material('M_Kit_WallTile',(.65,.66,.61),rough=.43)
yellow=material('M_Kit_Tactile',(.66,.49,.035),rough=.62)
steel=material('M_Kit_RailSteel',(.38,.43,.45),metal=.85,rough=.32)
dark=material('M_Kit_DarkTrim',(.055,.065,.07),metal=.25,rough=.66)
paint=material('M_Kit_MetalPaint',(.25,.27,.28),metal=.05,rough=.72)
glow=material('M_Kit_LampEmission',(.78,.92,1),rough=.3,noise=False,emission=3)
def mesh(name,verts,faces,mat=None,coll=False):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); scene.collection.objects.link(o)
    if mat: me.materials.append(mat)
    uv=me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        axis=max(range(3),key=lambda i:abs(poly.normal[i])); axes=[i for i in range(3) if i!=axis]
        for li in poly.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=(co[axes[0]],co[axes[1]])
    (collision if coll else parts).append(o)
    return o
def box(loc,size,mat=concrete,coll=False):
    x,y,z=loc; a,b,c=[s/2 for s in size]
    v=[(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh('Box',v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,coll)
def tube(points,tangents,r=.02,mat=steel,coll=False,sides=12):
    vs=[]; fs=[]
    for pt,tan in zip(points,tangents):
        p=Vector(pt); t=Vector(tan).normalized(); ref=Vector((0,0,1)) if abs(t.z)<.95 else Vector((0,1,0))
        a=t.cross(ref).normalized(); b=t.cross(a).normalized()
        vs.extend(p+r*(math.cos(j*2*math.pi/sides)*a+math.sin(j*2*math.pi/sides)*b) for j in range(sides))
    for k in range(len(points)-1):
        for j in range(sides):
            a=k*sides+j; b=k*sides+(j+1)%sides; fs.append((a,b,b+sides,a+sides))
    fs.append(tuple(reversed(range(sides)))); fs.append(tuple((len(points)-1)*sides+j for j in range(sides)))
    o=mesh('Pipe',vs,fs,mat,coll)
    for p in o.data.polygons[:-2]: p.use_smooth=True
    return o
def line(a,b,r=.02,mat=steel,coll=False):
    t=(Vector(b)-Vector(a)).normalized(); return tube([a,b],[t,t],r,mat,coll,8 if coll else 12)
def cylinder_z(x,y,z,r,h,mat): return line((x,y,z),(x,y,z+h),r,mat)
def join(objs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join(); o=bpy.context.object; o.name=name
    return o
def finish(id,label,budget=4000,extra=None):
    global parts,collision
    name=f'SM_SW_{id}_{label}'; o=join(parts,name)
    # Manifold check per object, retaining intentional independent surface islands.
    bm=bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(o.data)
    boundary=sum(e.is_boundary for e in bm.edges); nonmanifold=sum(not e.is_manifold for e in bm.edges); bm.free()
    o.data.calc_loop_triangles(); tris=len(o.data.loop_triangles)
    assert tris<=budget,(name,tris,budget)
    assert all(math.isfinite(c) for v in o.data.vertices for c in v.co),name
    for i,c in enumerate(collision): c.name=f'UCX_{name}_{i:02d}'
    bpy.ops.object.select_all(action='DESELECT')
    for c in [o]+collision: c.select_set(True)
    bpy.context.view_layer.objects.active=o
    # Store actual centimeter vertices, not a root scale that legacy UE may discard.
    for c in [o]+collision:
        for v in c.data.vertices: v.co*=100
        c.data.update()
    scene.unit_settings.scale_length=.01
    bpy.ops.export_scene.fbx(filepath=str(OUT/'FBX'/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='-Y',axis_up='Z',apply_unit_scale=True,mesh_smooth_type='FACE',bake_anim=False)
    for c in [o]+collision:
        for v in c.data.vertices: v.co/=100
        c.data.update()
    scene.unit_settings.scale_length=1
    bpy.context.view_layer.update()
    row=dict(id=id,name=name,triangles=tris,budget=budget,dimensions_cm=[round(x*100,4) for x in o.dimensions],collision_hulls=len(collision),boundary_edges=boundary,nonmanifold_edges=nonmanifold,materials=[m.name for m in o.data.materials],route='procedural_blender',appearance='review_pending',technical='pass',uv_layers=len(o.data.uv_layers),notes=extra or {})
    assets.append((o,row))
    for c in collision: bpy.data.objects.remove(c,do_unlink=True)
    parts=[]; collision=[]; o.hide_render=True
    return o
def tiled_floor(w,l,tactile=False):
    box((w/2,l/2,-.055),(w,l,.09),grout)
    # Anchor a 30cm world grid; crop edge pieces rather than stretch.
    xcuts=[0,.1,.4,.7,1,1.3,1.4] if abs(w-1.4)<1e-6 else [min(i*.3,w) for i in range(math.ceil(w/.3)+1)]
    for i in range(len(xcuts)-1):
        for j in range(math.ceil(l/.3)):
            x=xcuts[i]; y=j*.3; sx=xcuts[i+1]-x-.003; sy=min(.3,l-y)-.003
            box((x+.0015+sx/2,y+.0015+sy/2,-.005),(sx,sy,.01),yellow if tactile else floor)
            if tactile:
                for dx in [.06,.105,.15,.195,.24]:
                    for dy in [.06,.105,.15,.195,.24]:
                        if dx<sx and dy<sy: cylinder_z(x+dx,y+dy,0,.0125,.004,yellow)
    box((w/2,l/2,-.05),(w,l,.10),coll=True)
for id,label,w,l,t in [('02','Landing180',1.8,1.8,False),('02','Landing140',1.4,1.8,False),('03','Floor60',.6,.6,False),('04','Tactile60',.6,.6,True)]:
    tiled_floor(w,l,t); finish(id,label,8000 if t else 4000,dict(tile_pitch_cm=30,grout_cm=.3))
for n in [1,6]:
    for i in range(n):
        h=.15*(i+1); box((.3*(i+.5),.7,h/2),(.3,1.4,h),concrete)
    for i in range(n):
        h=.15*(i+1); box((.3*(i+.5),.7,h/2),(.3,1.4,h),coll=True)
    finish('01',f'Stair{n}',6000,dict(rise_cm=15,tread_cm=30,collision='one convex box per step; 15cm step below heroine 45cm MaxStepHeight; PIE not yet tested'))
def wall_panel(w=1.2,h=2.4):
    box((w/2,.075,h/2),(w,.15,h),grout)
    for x in range(round(w/.1)):
        for z in range(round(h/.1)):
            box((.05+.1*x,-.003,.05+.1*z),(.097,.006,.097),wall)
    box((w/2,.075,h/2),(w,.15,h),coll=True)
wall_panel(); finish('05','Wall120',4000,dict(wall_tile_pitch_cm=10,wall_grout_cm=.3))
for id,label,angle in [('06','WallInnerCorner',90),('20','WallOuterCorner',-90)]:
    wall_panel(.6); before=len(parts); cb=len(collision); wall_panel(.6)
    for o in parts[before:]+collision[cb:]:
        for v in o.data.vertices:
            x,y,z=v.co
            v.co=(-y,-x,z) if id=='06' else (y,x,z)
    if id=='06':
        box((-.075,.075,1.2),(.15,.15,2.4),grout)
        box((-.075,.075,1.2),(.15,.15,2.4),coll=True)
    else:
        # The second core owns the shared 15cm square; eliminate coplanar overlap.
        for o in [parts[0],collision[0]]:
            for v in o.data.vertices:
                if abs(v.co.x)<1e-6: v.co.x=.15
    finish(id,label,4000,dict(wall_tile_pitch_cm=10,corner_angle_deg=angle))
box((.075,.075,1.2),(.15,.15,2.4),grout)
for z in range(24): box((.075,-.003,.05+.1*z),(.147,.006,.097),wall)
box((.075,.075,1.2),(.15,.15,2.4),coll=True)
finish('21','WallEndCap',4000,dict(width_cm=15))
for id,label,size,mat in [('07','Ceiling120',(1.2,1.2,.10),concrete),('08','Beam140',(1.4,.30,.25),concrete),('22','Skirting120',(1.2,.025,.12),dark)]:
    center=[s/2 for s in size]; box(center,size,mat); box(center,size,coll=True); finish(id,label)
for ang in [90,-90]:
    box((.3,.0125,.06),(.6,.025,.12),dark); box((.0125,.3*(1 if ang==90 else -1),.06),(.025,.6,.12),dark)
    box((.3,.0125,.06),(.6,.025,.12),coll=True); box((.0125,.3*(1 if ang==90 else -1),.06),(.025,.6,.12),coll=True)
    finish('22','Skirting'+('Inner' if ang==90 else 'Outer'))
# Nosing, top at stair surface+6mm. Grooves modeled at modest cost.
box((.0175,.7,.003),(.035,1.4,.006),dark)
for x in [.005,.013,.021,.029]: box((x,.7,.006),(.003,1.4,.002),steel)
box((.0175,.7,.004),(.035,1.4,.008),coll=True); finish('16','Nosing140')
def add_rails(pts,tans,brackets=False):
    for height in [0,.25]:
        p=[Vector(v)+Vector((0,0,height)) for v in pts]; tube(p,tans)
        for a,b in zip(p,p[1:]): line(a,b,coll=True)
        if brackets:
            for k in [0,len(p)-1]:
                a=p[k]+Vector((0,0,-.015)); b=a+Vector((0,.08,0)); line(a,b,r=.008)
                box((b.x,b.y,b.z),(.055,.006,.06),steel)
def straight_points(a,b):
    t=(Vector(b)-Vector(a)).normalized(); return [Vector(a),Vector(b)],[t,t]
for id,label,end in [('09','RailHorizontal',(1.2,0,0)),('09','RailHorizontal60',(.6,0,0)),('10','RailSlope',(1.2,0,.6)),('10','RailSlope60',(.6,0,.3))]:
    p,t=straight_points((0,0,0),end); add_rails(p,t,True)
    finish(id,label,4000,dict(start=[0,0,0],end=list(end),tangent=list(t[0]),diameter_cm=4,vertical_spacing_cm=25,rail_origin='lower rail center at start'))
def arc(start,tangent,axis,angle,radius,n):
    t=Vector(tangent).normalized(); ax=Vector(axis).normalized(); p=Vector(start); rad=-ax.cross(t)*radius; center=p-rad
    return [center+Quaternion(ax,angle*i/n)@rad for i in range(n+1)],[Quaternion(ax,angle*i/n)@t for i in range(n+1)]
for sign in [1,-1]:
    p,t=arc((0,0,0),(1,0,0),(0,0,sign),math.pi/2,.08,8); add_rails(p,t)
    finish('11','RailCorner'+('Left' if sign==1 else 'Right'),4000,dict(start=list(p[0]),end=list(p[-1]),start_tangent=list(t[0]),end_tangent=list(t[-1]),radius_cm=8))
theta=math.atan(.5)
for id,label,starttan,axis in [('17','SlopeToLevel',(math.cos(theta),0,math.sin(theta)),(0,1,0)),('18','LevelToDown',(1,0,0),(0,1,0))]:
    p,t=arc((0,0,0),starttan,axis,theta,.08,4); add_rails(p,t)
    finish(id,label,4000,dict(start=list(p[0]),end=list(p[-1]),start_tangent=list(t[0]),end_tangent=list(t[-1]),radius_cm=8))
for id,label,tilt in [('12','RailReturnHorizontal',0),('19','RailReturnSlope',theta)]:
    for sign in [1,-1]:
        tangent=Vector((math.cos(tilt),0,math.sin(tilt))); normal=Vector((0,sign,0)); ax=tangent.cross(normal)
        p,t=arc((0,0,0),tangent,ax,math.pi/2,.06,8)
        p.append(p[-1]+normal*.02); t.append(normal); add_rails(p,t)
        for h in [0,.25]:
            e=p[-1]+Vector((0,0,h)); box(e,(.065,.008,.065),steel)
        finish(id,label+('Left' if sign==1 else 'Right'),4000,dict(start=list(p[0]),end=list(p[-1]),start_tangent=list(t[0]),end_tangent=list(t[-1]),radius_cm=6,wall_center_offset_cm=8))
# Door pair is preserved from the approved import source.
with bpy.data.libraries.load(str(ROOT/'Export/DoorPair/door_pair_source.blend'),link=False) as (a,b):
    b.objects=[n for n in a.objects if n in ['SM_Stairwell_DoorLeaf14','SM_Stairwell_DoorFrame13']]
for obj in b.objects:
    scene.collection.objects.link(obj); obj.hide_render=True
    id='14' if 'Leaf' in obj.name else '13'; obj.data.calc_loop_triangles()
    assets.append((obj,dict(id=id,name=obj.name,triangles=len(obj.data.loop_triangles),budget=3000,dimensions_cm=[round(v*100,4) for v in obj.dimensions],collision_hulls=1 if id=='14' else 3,route='tripo_web_corrected' if id=='14' else 'procedural_blender',appearance='import_approved',technical='previous_import_verified',materials=[m.name for m in obj.data.materials],notes={'existing_unreal_asset':True})))
# Generated light retained for review; emissive surfaces are independent material geometry.
with bpy.data.libraries.load(str(ROOT/'Models/15_Light/light15_review_v002.blend'),link=False) as (a,b):
    b.objects=[n for n in a.objects if n.startswith('SM_Stairwell_Light15')]
for obj in b.objects:
    scene.collection.objects.link(obj); parts.append(obj)
    # Replace corrupted upper-housing texels with a shared painted-metal surface.
    obj.data.materials.append(paint); top_slot=len(obj.data.materials)-1
    for poly in obj.data.polygons:
        center=obj.matrix_world@poly.center
        if center.z>.04 and poly.normal.z>.5: poly.material_index=top_slot
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    mod=obj.modifiers.new('EmissionBudget','DECIMATE'); mod.ratio=.94; bpy.ops.object.modifier_apply(modifier=mod.name)
for y in [-.055,.055]: line((-.52,y,-.085),(.52,y,-.085),r=.013,mat=glow)
# A separate 3mm cover closes the generated upper-housing slit without altering the raw mesh.
box((0,0,.103),(1.2,.27,.003),paint)
box((0,0,.002),(1.2,.271,.205),coll=True)
light=finish('15','LightFixture',3000,dict(source='Tripo API light15 v002; not regenerated',repair='Added 3mm painted upper cover over source slit and two emissive surfaces',review_note='Cover and emissive alignment require appearance review; generated mesh retains boundary edges'))
assets[-1][1]['route']='tripo_api_corrected'; assets[-1][1]['technical']='pass_with_documented_source_boundaries'
# Export images embedded in generated sources without resampling or repainting.
for img in bpy.data.images:
    if img.type=='IMAGE' and img.size[0]>0 and img.packed_file:
        img.filepath_raw=str(OUT/'textures'/(img.name.replace('/','_')+'.png')); img.file_format='PNG'; img.save()
ids={r['id'] for o,r in assets}; assert ids=={f'{i:02d}' for i in range(1,23)},ids
report={'version':'v001','status':'technical_build_complete_appearance_review_pending','assets':[r for o,r in assets], 'shared_spec':dict(floor_pitch_cm=30,wall_pitch_cm=10,grout_cm=.3,rail_diameter_cm=4,rail_spacing_cm=25),'limitations':['No human appearance approval for new kit yet','Light housing uses procedural repair paint; source boundaries documented','No PIE movement/camera validation','Full source-scene reconstruction is a later assembly stage']}
(OUT/'reports/asset_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(OUT/'reports/material_spec.json').write_text(json.dumps(specs,indent=2),encoding='utf-8')
# Neutral review renders at identical lighting; each asset framed independently.
scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'); bg.inputs[0].default_value=(.16,.18,.20,1); bg.inputs[1].default_value=.6
for pos,energy in [((3,-4,6),650),((-3,2,4),450)]:
    d=bpy.data.lights.new('Softbox','AREA'); d.energy=energy; d.size=5
    ob=bpy.data.objects.new('Softbox',d); scene.collection.objects.link(ob); ob.location=pos; ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('ReviewCamera'); cam=bpy.data.objects.new('ReviewCamera',d); scene.collection.objects.link(cam); scene.camera=cam; d.type='ORTHO'
scene.render.engine='CYCLES'; scene.cycles.samples=16; scene.cycles.use_denoising=True
scene.render.resolution_x=640; scene.render.resolution_y=640; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'
for o,row in assets:
    selected=os.environ.get('STAIRWELL_KIT_RENDER_IDS','')
    if selected and row['id'] not in selected.split(','): continue
    o.hide_render=False; pts=[o.matrix_world@Vector(v) for v in o.bound_box]; lo=Vector([min(v[k] for v in pts) for k in range(3)]); hi=Vector([max(v[k] for v in pts) for k in range(3)]); center=(lo+hi)/2
    cam.location=center+Vector((-3,-4,3) if row['id']=='20' else (3,-4,3)); cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler(); d.ortho_scale=max(hi-lo)*1.65
    scene.render.filepath=str(OUT/'renders'/(row['name']+'.png')); bpy.ops.render.render(write_still=True)
    if row['id']=='15':
        cam.location=center+Vector((3,-4,-3)); cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/'renders'/(row['name']+'_underside.png')); bpy.ops.render.render(write_still=True)
    o.hide_render=True
# Save a browsable, labeled gallery .blend, with meshes physically separated.
for i,(o,row) in enumerate(assets):
    o.hide_render=False; o.location+=Vector(((i%6)*3.8,-(i//6)*4.2,0))
    td=bpy.data.curves.new('Label','FONT'); td.body=row['id']+' '+row['name'].replace('SM_SW_',''); td.size=.13
    to=bpy.data.objects.new('Label',td); scene.collection.objects.link(to); to.location=(o.location.x,o.location.y-.45,-.15); to.rotation_euler=(math.pi/2,0,0)
bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'stairwell_kit_review_v001.blend'))
print('KIT_BUILD_COMPLETE',len(assets),'assets',len(ids),'IDs')
