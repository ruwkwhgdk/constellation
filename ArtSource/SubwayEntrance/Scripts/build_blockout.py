"""Metric entrance blockout. Run via tools/run-blender.ps1. No level changes."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Blockout/v001';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
def mat(name,c):
    m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=.7
    return m
stone=mat('Stone',(.46,.49,.46));metal=mat('Silver',(.39,.46,.46));cream=mat('Soffit',(.78,.77,.65));dark=mat('Trim',(.075,.13,.15));yellow=mat('Tactile',(.85,.64,.13));glass=mat('Glass_placeholder',(.3,.54,.56));teal=mat('Scale_marker',(.07,.46,.5));red=mat('Travel_zone_preview',(.8,.2,.12))
glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.72
glass.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.14
parts=[];right=[];roof=[];guides=[]
def box(name,xyz,dims,m,group=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz);o=bpy.context.object;o.name=name;o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    bevel=o.modifiers.new('Soft edge','BEVEL');bevel.width=.018;bevel.segments=2
    o.modifiers.new('Normals','WEIGHTED_NORMAL');parts.append(o)
    if group is not None:group.append(o)
    return o
def pipe(name,a,b,r=.024,group=None):
    a,b=Vector(a),Vector(b);d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(metal);parts.append(o)
    if group is not None:group.append(o)
    return o
# Local Blender: opening at -Y; descend toward +Y. Walking grade Z=0.
W=4.2;HALF=W/2;FRONT=-4.7;TOP=.48;COUNT=18;RISE=.16;TREAD=.30
for i in range(3):
    z=(i+1)*.16;box('E06_ExteriorStep_%02d'%i,(0,FRONT-.9+(i+.5)*.3,z/2),(W+.8,.3,z),stone)
box('E06_UpperLanding',(0,-4.1,TOP/2),(W,1.2,TOP),stone)
box('E07_Tactile',(0,-3.8,TOP+.012),(W,.3,.024),yellow)
for i in range(COUNT):
    z=TOP-(i+1)*RISE;y=-3.5+(i+.5)*TREAD
    box('E08_DescendingStep_%02d'%i,(0,y,z-.13),(W,TREAD,.26),stone)
bottom=TOP-COUNT*RISE
box('E08_LowerLanding',(0,2.8,bottom-.18),(W,1.8,.36),stone)
# Closed lower shell: safety floor remains even when travel fails.
box('E09_FailsafeFloor',(0,.2,bottom-.48),(W+.5,7.6,.28),dark)
box('E09_EndWall',(0,3.8,-.2),(W+.5,.25,4.9),stone)
for side in [-1,1]:
    x=side*(HALF+.14);g=right if side==1 else None
    box('E09_ShaftWall',(x,.1,-1.0),(.28,7.4,3.9),cream,g)
    # Above-ground side wall spans canopy length.
    box('E04_StoneWall',(x,-.4,.56),(.32,8.6,1.12),stone,g)
    box('E04_Coping',(x,-.4,1.16),(.44,8.6,.13),stone,g)
    for k in range(6):
        y=-3.92+k*1.4
        box('E05_Glass',(x,y,1.53),(.035,1.31,.62),glass,g)
        box('E05_Frame',(x,y-.69,1.54),(.07,.06,.77),metal,g)
    box('E05_TopRail',(x,-.4,1.89),(.09,8.6,.07),metal,g)
    for y in [-4.35,-.4,3.5]:
        box('E03_Column',(x,y,1.9),(.3,.34,3.8),metal,g)
        box('E03_Base',(x,y,.1),(.42,.46,.2),stone,g)
    # Slope rail follows individual step edges; radius never scaled with width.
    for h in [.72,.98]:
        pipe('E10_SlopeRail',(side*(HALF-.1),-3.5,TOP+h),(side*(HALF-.1),1.9,bottom+h),group=g)
        pipe('E10_UpperReturn',(side*(HALF-.1),-3.85,TOP+h),(side*(HALF-.1),-3.5,TOP+h),group=g)
        pipe('E10_LowerReturn',(side*(HALF-.1),1.9,bottom+h),(side*(HALF-.1),2.4,bottom+h),group=g)
    for y in [-3.3,-1.8,-.3,1.2]:
        z=TOP-(y+3.5)/TREAD*RISE+.85
        pipe('E10_Bracket',(side*(HALF-.1),y,z),(side*(HALF+.02),y,z),.018,g)
box('E01_Canopy',(0,-.35,3.95),(W+1.5,10.1,.28),metal,roof)
for i in range(8):
    for j in range(4):box('E02_SoffitPanel',(-2.1+j*1.4,-4.8+i*1.26,3.795),(1.37,1.23,.028),cream,roof)
box('E12_FrontSign',(0,-5.409,3.96),(4.6,.025,.24),dark,roof)
box('E11_SidePanel',(HALF+.22,-4.6,1.1),(.12,1.4,1.24),metal,right)
for y in [-5.8,-4.8]:pipe('E11_OuterGuardPost',(HALF+.65,y,0),(HALF+.65,y,1.12))
pipe('E11_OuterGuardRail',(HALF+.65,-5.8,1.12),(HALF+.65,-4.8,1.12))
box('E13_MapBox',(-HALF-.42,-4.0,.9),(.24,.65,.8),cream)
for side in [-1,1]:
    for y in [-4.35,-.4,3.5]:box('E13_ColumnLamp',(side*(HALF-.2),y,3.25),(.15,.3,.3),dark,right if side==1 else None)
# Ground represented only outside shaft. No single plane seals the opening.
for x in [-5,5]:box('PreviewGroundSide',(x,-.3,-.08),(5.3,15,.16),cream,guides)
box('PreviewGroundFront',(0,-6.55,-.08),(4.7,5.3,.16),cream,guides)
box('PreviewGroundBack',(0,5.7,-.08),(4.7,3.4,.16),cream,guides)
# 170 cm measuring mannequin. Preview only, excluded from assets.
for name,p in [('Entry',(0,-6.3,0)),('Descent',(.6,.3,TOP-13*RISE))]:
    x,y,z=p;pipe('Guide_'+name+'_170cm',(x,y,z+.05),(x,y,z+1.46),.19,guides)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.12,location=(x,y,z+1.58));o=bpy.context.object;o.name='Guide_Head';o.data.materials.append(teal);guides.append(o)
zone=box('Guide_TravelZone_NotRuntime',(0,2.6,bottom+.05),(W,1.0,.06),red,guides)
dimensions=dict(units='meters',status='blockout_review_not_production',clear_width=W,canopy_width=W+1.5,canopy_length=10.1,soffit_height=3.78,entry_riser=.16,entry_tread=.30,entry_steps=3,upper_landing_height=TOP,descending_steps=COUNT,descending_riser=RISE,descending_tread=TREAD,lower_landing_height=bottom,travel_zone='preview only; runtime code not implemented',travel_floor_margin=.0,safety_floor_top=bottom-.34,ground_opening_width=4.2,ground_opening_y=[-3.5,3.7],world_dummy_anchor=[3900,-19500,10530],world_ground_z_candidate=10000,anchor_note='Preserve target anchor; floor alignment requires 530cm pivot offset, not placing walking grade at anchor Z.',dummy_scale_not_reused=30,hidden_structure='inferred closed shaft',play_tested=False)
(OUT/'dimensions.json').write_text(json.dumps(dimensions,indent=2),encoding='utf-8')
assert abs(TOP-COUNT*RISE-bottom)<1e-6
assert W-.2>=3.6 and 3.78-TOP>2.5
for o in parts:
    assert all(math.isfinite(v) for v in o.dimensions),o.name
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True
s.render.resolution_x=1440;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world.color=(.45,.45,.45)
bpy.ops.object.light_add(type='AREA',location=(1,-3,12));bpy.context.object.data.energy=2200;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=9
bpy.ops.object.light_add(type='SUN',location=(0,0,9));bpy.context.object.rotation_euler=(.5,-.4,-.4);bpy.context.object.data.energy=2
def camera(name,loc,target,ortho):
    bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.name=name;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=ortho;s.camera=c
    s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
camera('exterior',(13,-18,11),(0,-.7,1),17)
camera('rear',(-12,15,9),(0,-.3,1),16)
for o in roof+right:o.hide_render=True
for o in guides:
    if o.name.startswith('PreviewGround'):o.hide_render=True
camera('section',(15,-9,8),(0,-.4,.3),14)
for o in roof+right+guides:o.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'entrance_blockout.blend'))
(OUT/'verification.json').write_text(json.dumps(dict(object_count=len(parts),finite_dimensions=True,clear_width_between_rails=W-.2,headroom_upper_landing=3.78-TOP,rendered=['exterior','rear','section'],unreal_imported=False,collision_runtime_verified=False),indent=2),encoding='utf-8')
print('SUBWAY_BLOCKOUT_OK')
