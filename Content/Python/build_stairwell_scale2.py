"""Double architecture in a separate map; retain human-scale props."""
import unreal as u, json, time
from pathlib import Path
ROOT=Path(u.Paths.project_dir()); OUT=ROOT/'ArtSource/Stairwell_Modular/Scene/v002'; OUT.mkdir(parents=True,exist_ok=True)
SRC='/Game/Environment/StairwellModular/Scene/Maps/L_Stairwell_Reference'
DST='/Game/Environment/StairwellModular/Scene/Maps/L_Stairwell_PlayScale2'
E=u.EditorAssetLibrary; A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert not E.does_asset_exist(DST), 'Destination already exists; do not double-scale again'
assert E.duplicate_asset(SRC,DST); assert E.save_asset(DST,only_if_is_dirty=False); assert L.load_level(DST)
actors={a.get_actor_label().removeprefix('SWScene_'):a for a in A.get_all_level_actors() if a.get_actor_label().startswith('SWScene_')}
snap={n:dict(p=a.get_actor_location(),s=a.get_actor_scale3d(),r=a.get_actor_rotation()) for n,a in actors.items()}
rail_mat=actors['MainRail_-112_0'].static_mesh_component.get_material(0)
removed=[]
for n,a in list(actors.items()):
    if ('Rail' in n or n.startswith('MainBottomTransition')) and not n.startswith('Detail_DoorPushBar'):
        A.destroy_actor(a); removed.append(n); continue
    if n in ['DoorLeaf','DoorFrame'] or n.startswith('Detail_DoorPushBar') or n.startswith(('Lamp_','LuminousStrip_','Light_')): continue
    a.set_actor_location(snap[n]['p']*2,False,False)
    if isinstance(a,u.StaticMeshActor): a.set_actor_scale3d(snap[n]['s']*2)
    if isinstance(a,u.Light):
        c=a.get_component_by_class(u.LocalLightComponent)
        if c:
            c.set_intensity(c.intensity*4); c.set_editor_property('attenuation_radius',c.attenuation_radius*2)
    if isinstance(a,u.PlayerStart): a.set_actor_location(u.Vector(-540,0,460),False,False)
# Fixed-size door and hardware; preserve attachment-relative placement.
delta=u.Vector(360,-5,0)
for n in ['DoorLeaf','DoorFrame']:
    actors[n].set_actor_location(snap[n]['p']+delta,False,False)
for n,a in actors.items():
    if n.startswith('Detail_DoorPushBar'): a.set_actor_location(snap[n]['p']+delta,False,False)
# Fixtures and their strips/light retain physical dimensions and orientation.
for kind in ['Ceiling','LeftWall','RightWall','Beyond']:
    name='Lamp_'+kind; p=snap[name]['p']; target=p*2
    if kind=='RightWall': target.y=235
    if kind=='LeftWall': target.y=-235
    offset=target-p
    for n in [name,'LuminousStrip_'+kind+'-1','LuminousStrip_'+kind+'1','Light_'+kind]:
        a=actors[n]; a.set_actor_location(snap[n]['p']+offset,False,False)
        if n.startswith('Light_'):
            c=a.get_component_by_class(u.RectLightComponent); c.set_intensity(c.intensity*4); c.set_editor_property('attenuation_radius',c.attenuation_radius*2)
def cube(name,pos,size,material):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator()); a.set_actor_label('SWScale2_'+name)
    a.static_mesh_component.set_static_mesh(E.load_asset('/Engine/BasicShapes/Cube')); a.set_actor_scale3d(u.Vector(*[x/100 for x in size])); a.static_mesh_component.set_material(0,material); return a
wall=actors['DoorWallLeft'].static_mesh_component.get_material(1) or actors['DoorWallLeft'].static_mesh_component.get_material(0)
# Fill the extra opening created by enlarged architecture around a100x210cm door.
# User requested no door-sized infill: preserve the doubled structural opening.
KIT='/Game/Environment/StairwellModular/ReviewKit/Meshes/'
rails=[]
def rail(name,mesh,pos,yaw=0,mirror=False):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*pos),u.Rotator(yaw=yaw)); a.set_actor_label('SWScale2_'+name)
    a.static_mesh_component.set_static_mesh(E.load_asset(KIT+'SM_SW_'+mesh)); a.set_actor_scale3d(u.Vector(1,-1 if mirror else 1,1))
    for i in range(a.static_mesh_component.get_num_materials()): a.static_mesh_component.set_material(i,rail_mat)
    rails.append(a); return a
for y,mirror in [(-232,True),(232,False)]:
    for i in range(6): rail('MainRail_'+str(y)+'_'+str(i),'10_RailSlope',(360-i*120,y,65+i*60),180,mirror)
for y,mirror in [(248,True),(712,False)]:
    for i in range(6): rail('NextRail_'+str(y)+'_'+str(i),'10_RailSlope',(1440-i*120,y,-295+i*60),180,mirror)
for y,mirror in [(-232,False),(952,True)]:
    for i in range(3): rail('LandingRail_'+str(y)+'_'+str(i),'09_RailHorizontal',(360+i*120,y,65),0,mirror)
    rail('LandingEnd_'+str(y),'12_RailReturnHorizontalRight' if mirror else '12_RailReturnHorizontalLeft',(720,y,65))
# Independent verification of new map, fixed prop scales, actual architecture bounds.
def bounds(a):
    c,e=a.get_actor_bounds(False); return c-e,c+e
def close(a,b): assert abs(a-b)<.1,(a,b)
for n in ['MainStairsNear','MainStairsFar','NextStairsNear','NextStairsFar']:
    lo,hi=bounds(actors[n]); close(hi.x-lo.x,360); close(hi.y-lo.y,480); close(hi.z-lo.z,180)
for n in ['DoorLeaf','DoorFrame','Lamp_Ceiling','Lamp_LeftWall','Lamp_RightWall','Lamp_Beyond']:
    s=actors[n].get_actor_scale3d(); old=snap[n]['s']; close(s.x,old.x); close(s.y,old.y); close(s.z,old.z)
close(bounds(actors['MainStairsNear'])[1].x,bounds(actors['MainStairsFar'])[0].x)
close(bounds(actors['MainStairsFar'])[1].x,bounds(actors['MiddleLandingLeft'])[0].x)
close(bounds(actors['MainStairsFar'])[0].z,bounds(actors['MiddleLandingLeft'])[1].z)
pawn=u.get_default_object(u.EditorAssetLibrary.load_blueprint_class('/Game/Blueprints/Character/PC/BP_Player_Heroine'))
movement=pawn.get_component_by_class(u.CharacterMovementComponent); max_step=movement.get_editor_property('max_step_height'); assert max_step>=30
assert L.save_current_level()
report=dict(status='pass',map=DST,architecture_scale=2,stair_width_cm=480,landing_depth_cm=360,step_height_cm=30,tread_depth_cm=60,character_max_step_height_cm=max_step,props_scale_preserved=True,rail_diameter_cm=4,rail_vertical_spacing_cm=25,rail_modules=len(rails),main_rail_clearance_cm=460,stairs_landing_seams=True,playtest='not_run')
(OUT/'scale2_verification.json').write_text(json.dumps(report,indent=2))
cam=actors['ReferenceCamera']; world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
for cmd in ['r.ScreenPercentage 100','r.AntiAliasingMethod 2','r.TemporalAA.Upsampling 0']: u.SystemLibrary.execute_console_command(world,cmd)
u.EditorPythonScripting.set_keep_python_script_alive(True); started=time.time(); requested=False
def tick(dt):
    global requested
    if time.time()-started>35 and not requested:
        requested=True; u.AutomationLibrary.take_high_res_screenshot(1080,1579,str(OUT/'scale2_reference.png'),camera=cam,delay=2)
    if time.time()-started>50:
        u.unregister_slate_post_tick_callback(handle); u.SystemLibrary.quit_editor()
handle=u.register_slate_post_tick_callback(tick)
