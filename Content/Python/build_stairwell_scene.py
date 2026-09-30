"""Assemble adopted kit into a separate reference-scene map. Units: centimeters."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u
import json, math
from pathlib import Path
ROOT=Path(u.Paths.project_dir())/'ArtSource/Stairwell_Modular'
OUT=ROOT/'Scene/v001'; OUT.mkdir(parents=True,exist_ok=True)
KIT='/Game/Constellation/Environments/Stairwell/ReviewKit'
DEST='/Game/Constellation/Environments/Stairwell/Scene'
E=u.EditorAssetLibrary; A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
MAP='/Game/Constellation/Review/Stairwell/Maps/L_Stairwell_Reference'
# Maintained source rebuild; retired intermediate backups are not recreated.
assert L.load_level(MAP) if E.does_asset_exist(MAP) else L.new_level(MAP)
for a in A.get_all_level_actors():
    if str(a.get_actor_label()).startswith('SWScene_'): A.destroy_actor(a)
records=[]
M=u.MaterialEditingLibrary; AT=u.AssetToolsHelpers.get_asset_tools(); scene_materials={}
spec=load_current_json((ROOT/'Production/v001/reports/material_spec.json').read_text(encoding='utf-8-sig'))
for name,s in spec.items():
    path=DEST+'/Materials/'+name
    mat=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,DEST+'/Materials',u.Material,u.MaterialFactoryNew())
    M.delete_all_material_expressions(mat)
    base=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector); base.constant=u.LinearColor(*s['color'],1)
    if s['noise']:
        noise=M.create_material_expression(mat,u.MaterialExpressionNoise); noise.set_editor_property('scale',.025); noise.set_editor_property('levels',2)
        factor=M.create_material_expression(mat,u.MaterialExpressionConstant); factor.r=.06
        mul=M.create_material_expression(mat,u.MaterialExpressionMultiply); M.connect_material_expressions(noise,'',mul,'A'); M.connect_material_expressions(factor,'',mul,'B')
        bias=M.create_material_expression(mat,u.MaterialExpressionConstant); bias.r=.94
        add=M.create_material_expression(mat,u.MaterialExpressionAdd); M.connect_material_expressions(mul,'',add,'A'); M.connect_material_expressions(bias,'',add,'B')
        tint=M.create_material_expression(mat,u.MaterialExpressionMultiply); M.connect_material_expressions(base,'',tint,'A'); M.connect_material_expressions(add,'',tint,'B'); base=tint
    M.connect_material_property(base,'',u.MaterialProperty.MP_BASE_COLOR)
    for value,prop in [(s['roughness'],u.MaterialProperty.MP_ROUGHNESS),(s['metallic'],u.MaterialProperty.MP_METALLIC)]:
        n=M.create_material_expression(mat,u.MaterialExpressionConstant); n.r=value; M.connect_material_property(n,'',prop)
    if s['emission']:
        n=M.create_material_expression(mat,u.MaterialExpressionConstant3Vector); n.constant=u.LinearColor(2000,2400,2600,1); M.connect_material_property(n,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
    M.recompile_material(mat); E.save_loaded_asset(mat); scene_materials[name]=mat
def spawn(name,mesh,pos,yaw=0,scale=(1,1,1)):
    path=mesh if mesh.startswith('/') else KIT+'/Meshes/SM_SW_'+mesh
    obj=E.load_asset(path); assert obj,path
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(pitch=0,yaw=yaw,roll=0))
    a.set_actor_label('SWScene_'+name); a.static_mesh_component.set_static_mesh(obj); a.set_actor_scale3d(u.Vector(*scale))
    for i,s in enumerate(obj.get_editor_property('static_materials')):
        key=str(s.material_slot_name).split('.')[0]
        if key in scene_materials: a.static_mesh_component.set_material(i,scene_materials[key])
    records.append(dict(name=name,mesh=path,position=pos,yaw=yaw,scale=scale))
    return a
def actor(cls,name,pos,rot=(0,0,0)):
    a=A.spawn_actor_from_class(cls,u.Vector(*pos),u.Rotator(pitch=rot[0],yaw=rot[1],roll=rot[2])); a.set_actor_label('SWScene_'+name); return a
def wall_run(name,x0,x1,y,z=-30,reverse=False):
    for i,x in enumerate(range(x0,x1,120)):
        for h in [z,z+240]: spawn(name+str(i)+'_'+str(h),'05_Wall120',(x+120 if reverse else x,y,h),180 if reverse else 0)
def floor_band(name,x,y,z,width=240):
    for j in range(width//60): spawn(name+str(j),'04_Tactile60',(x,y+j*60+60,z))

def landing(name,x,y,z,width=240):
    # Unscaled modules: 30cm tile pitch, 180cm depth, no stretched grout or UVs.
    for i in range(3):
        for j in range(width//60):
            label=name if i==0 and j==0 else name+'_Tile_'+str(i)+'_'+str(j)
            spawn(label,'03_Floor60',(x+i*60,y+(j+1)*60,z))
def rail_flight(name,x,y,z,segments=3,mirror=False):
    # Start at the low end and rise toward -X, matching the reversed stair flights.
    for i in range(segments):
        spawn(name+str(i),'10_RailSlope',(x-i*120,y,z+i*60),180,(1,-1 if mirror else 1,1))

# Twelve descending steps from the camera to the middle landing.
spawn('MainStairsNear','01_Stair6',(0,-120,90),180,(1,240/140,1))
spawn('MainStairsFar','01_Stair6',(180,-120,0),180,(1,240/140,1))
for i in range(12): spawn('MainNosing'+str(i),'16_Nosing140',(180-i*30,-120,(i+1)*15),180,(1,240/140,1))
landing('UpperLanding',-360,-120,180)
landing('MiddleLandingLeft',180,-120,0)
landing('MiddleLandingRight',180,120,0)
landing('MiddleLandingExtension',180,360,0,width=120)
floor_band('TactileMain_',180,-120,.2)
floor_band('TactileNext_',300,120,.2)
# Second flight beyond the right half of the landing.
spawn('NextStairsNear','01_Stair6',(540,120,-90),180,(1,240/140,1))
spawn('NextStairsFar','01_Stair6',(720,120,-180),180,(1,240/140,1))
for i in range(12): spawn('NextNosing'+str(i),'16_Nosing140',(720-i*30,120,-180+(i+1)*15),180,(1,240/140,1))
landing('LowerLanding',720,120,-180)
wall_run('LeftWall_',-360,360,-120)
wall_run('MainRightWall_',-300,60,120,reverse=True)
wall_run('FarRightWall_',180,1020,480,z=-210,reverse=True)
wall_run('NextDivider_',360,960,120,z=-210)
wall_run('NextOuter_',360,960,360,z=-210,reverse=True)
# Complete the back wall between the door and the relocated next flight.
spawn('LandingBackWall','05_Wall120',(360,360,0),90)
# Continue the side floor below the newly opened stair guardrail.
for x in [60,120]:
    for y in [180,240,300,360,420,480]: spawn('SideFloor_'+str(x)+'_'+str(y),'03_Floor60',(x,y,0))
# Door wall: leave a real 100cm opening; separate jamb meshes and lintel.
spawn('DoorWallLeft','21_WallEndCap',(360,-70,0),90)
spawn('DoorWallRight','21_WallEndCap',(360,45,0),90)
for y in [-130,-115,-100,-85,60,75,90,105]: spawn('DoorSideTrim'+str(y),'21_WallEndCap',(360,y,0),90)
spawn('DoorWallOver','08_Beam140',(360,-120,215),90,(240/140,1,8.6))
doorbase='/Game/Constellation/Environments/Stairwell/Meshes/'
spawn('DoorFrame',doorbase+'SM_Stairwell_DoorFrame13',(358,45,0),90)
spawn('DoorLeaf',doorbase+'SM_Stairwell_DoorLeaf14',(358,45,0),90)
# Ceiling and the dark cross-beam seen above the landing.
for i in range(5):
    for y in [-120,0,120,240,360,480]:
        roof=spawn('Ceiling_Slope_'+str(i)+'_'+str(y),'07_Ceiling120',(-360+i*107.331263,y,550-i*53.665631))
        roof.set_actor_rotation(u.Rotator(pitch=-26.565051,yaw=0,roll=0),False)
        records[-1]['pitch']=-26.565051
for x in [196,316]:
    for y in [-120,0,120,240,360,480]: spawn('Ceiling_Landing_'+str(x)+'_'+str(y),'07_Ceiling120',(x,y,285))
beam=spawn('CrossBeam','08_Beam140',(172,-120,260),90,(600/140,.8,1))
dark=E.load_asset(KIT+'/Materials/M_Kit_DarkTrim'); beam.static_mesh_component.set_material(0,dark)
for y,mirror in [(-112,True),(112,False)]: rail_flight('MainRail_'+str(y)+'_',180,y,65,mirror=mirror)
for y,mirror in [(128,True),(352,False)]: rail_flight('NextRail_'+str(y)+'_',720,y,-115,mirror=mirror)
# Exposed final stair section retains its guardrail; supports replace the removed wall.
for x,z in [(60,60),(180,0)]:
    post=spawn('OpenEdgeRailPost'+str(x),'/Engine/BasicShapes/Cube',(x,120,z+46),0,(.04,.04,.92))
    post.static_mesh_component.set_material(0,scene_materials['M_Kit_RailSteel'])
for y in [-112,112]: spawn('MainBottomTransition_'+str(y),'17_SlopeToLevel',(180,y,90),0,(1,1,-1))
# Left landing rail ends before the door. Opposite rail runs to the next stair.
for y,mir in [(-112,1),(472,-1)]:
    spawn('LandingRail_'+str(y),'09_RailHorizontal',(183.5777088,y,64.1554175),0,(1,mir,1))
    spawn('LandingRailEnd_'+str(y),'12_RailReturnHorizontalLeft' if mir==1 else '12_RailReturnHorizontalRight',(303.5777088,y,64.1554175))
# Wall base trim modules.
for x in range(-300,300,120): spawn('LeftSkirt'+str(x),'22_Skirting120',(x,-119,0))

for name,pos,yaw,watts in [('Ceiling',(-30,0,374),90,2400),('LeftWall',(-80,-108,385),0,1300),('RightWall',(-80,108,385),0,1300),('Beyond',(620,240,210),90,1000)]:
    spawn('Lamp_'+name,'15_LightFixture',pos,yaw)
    for side in [-1,1]:
        angle=math.radians(yaw)
        strip=spawn('LuminousStrip_'+name+str(side),'/Engine/BasicShapes/Cube',(pos[0]-math.sin(angle)*side*5.5,pos[1]+math.cos(angle)*side*5.5,pos[2]-10.7),yaw,(1.04,.026,.006))
        strip.static_mesh_component.set_material(0,scene_materials['M_Kit_LampEmission']); strip.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    light=actor(u.RectLight,'Light_'+name,(pos[0],pos[1],pos[2]-15),(-90,yaw,0))
    c=light.get_component_by_class(u.RectLightComponent); c.set_mobility(u.ComponentMobility.MOVABLE); c.set_intensity(watts)
    c.set_light_color(u.LinearColor(.69,.88,1,1)); c.set_editor_property('source_width',110); c.set_editor_property('source_height',16)
    c.set_editor_property('attenuation_radius',650)
# Soft fill approximates bounce for deterministic preview, independent of baked lighting.
fill=actor(u.PointLight,'LandingBounce',(245,40,170)); fc=fill.get_component_by_class(u.PointLightComponent); fc.set_mobility(u.ComponentMobility.MOVABLE); fc.set_intensity(700); fc.set_light_color(u.LinearColor(.48,.68,.76,1)); fc.set_editor_property('attenuation_radius',550)
camera_config_path=OUT/'camera_revision.json'
camera_config=load_current_json(camera_config_path.read_text(encoding='utf-8')) if camera_config_path.exists() else dict(position=[-160,-60,330],rotation=[-30,18,0],fov=68,aspect=1080/1579)
camera=actor(u.CameraActor,'ReferenceCamera',camera_config['position'],camera_config['rotation'])
cc=camera.get_component_by_class(u.CameraComponent); cc.set_field_of_view(camera_config['fov']); cc.set_aspect_ratio(camera_config['aspect'])
cc.set_editor_property('constrain_aspect_ratio',True)
pp=actor(u.PostProcessVolume,'Exposure',(200,0,100)); pp.set_editor_property('unbound',True)
settings=pp.get_editor_property('settings')
settings.set_editor_property('override_auto_exposure_method',True); settings.set_editor_property('auto_exposure_method',u.AutoExposureMethod.AEM_MANUAL)
settings.set_editor_property('override_auto_exposure_bias',True); settings.set_editor_property('auto_exposure_bias',.7)
pp.set_editor_property('settings',settings)
actor(u.PlayerStart,'PlayerStart',(-270,0,280),(0,0,0))
if (OUT/'lighting_revision.json').exists():
    lighting_script=Path(u.Paths.project_dir())/'Content/Python/stairwell_lighting_settings.py'
    lighting_namespace={}
    exec(compile(lighting_script.read_text(),str(lighting_script),'exec'),lighting_namespace)
    lighting_namespace['apply_lighting']()
if (OUT/'material_revision_enabled.json').exists():
    material_script=Path(u.Paths.project_dir())/'Content/Python/stairwell_material_settings.py'
    material_namespace={}
    exec(compile(material_script.read_text(),str(material_script),'exec'),material_namespace)
    material_namespace['apply_materials']()
if (OUT/'reference_details_enabled.json').exists():
    detail_script=Path(u.Paths.project_dir())/'Content/Python/stairwell_reference_details.py'
    detail_namespace={}
    exec(compile(detail_script.read_text(),str(detail_script),'exec'),detail_namespace)
    detail_namespace['apply_details']()
if (OUT/'finish_revision_enabled.json').exists():
    finish_script=Path(u.Paths.project_dir())/'Content/Python/stairwell_finish_settings.py'
    finish_namespace={}
    exec(compile(finish_script.read_text(),str(finish_script),'exec'),finish_namespace)
    finish_namespace['apply_finish']()
L.save_current_level(); E.save_directory(DEST,only_if_is_dirty=True,recursive=True)
(OUT/'scene_manifest.json').write_text(json.dumps(dict(map=MAP,mesh_instances=records,camera=camera_config,status='assembled_pending_visual_verification',assumptions=['Depth inferred from one image; two twelve-step flights','15/30cm stairs, 240cm scene width; 220cm rail clearance; source stair/nosing scaled only in width','Sloped ceiling follows stair pitch; landing ceiling 285cm','Scene material overrides: subdued world noise and brighter emission; final weathering pending']),indent=2),encoding='utf-8')
u.log('STAIRWELL_SCENE_ASSEMBLED '+str(len(records)))
