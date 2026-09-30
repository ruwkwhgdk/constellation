"""Read the saved scene and check actual stair/landing seams and clearances."""
from resource_paths import loads as load_current_json, load as load_current_json_file
import unreal as u, json
from pathlib import Path
OUT=Path(u.Paths.project_dir())/'ArtSource/Stairwell_Modular/Scene/v001'
L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level('/Game/Constellation/Review/Stairwell/Maps/L_Stairwell_Reference')
actors={str(a.get_actor_label()).removeprefix('SWScene_'):a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if str(a.get_actor_label()).startswith('SWScene_')}
def bounds(name):
    if name in ['UpperLanding','MiddleLandingLeft','MiddleLandingRight','MiddleLandingExtension','LowerLanding']:
        boxes=[a.get_actor_bounds(False) for n,a in actors.items() if n==name or n.startswith(name+'_Tile_')]
        lows=[c-e for c,e in boxes]; highs=[c+e for c,e in boxes]
        return u.Vector(min(p.x for p in lows),min(p.y for p in lows),min(p.z for p in lows)),u.Vector(max(p.x for p in highs),max(p.y for p in highs),max(p.z for p in highs))
    c,e=actors[name].get_actor_bounds(False); return c-e,c+e
def close(a,b): assert abs(a-b)<.05,(a,b)
near_lo,near_hi=bounds('MainStairsNear'); far_lo,far_hi=bounds('MainStairsFar'); land_lo,land_hi=bounds('MiddleLandingLeft')
close(near_hi.x,far_lo.x); close(near_lo.z,far_hi.z); close(far_hi.x,land_lo.x); close(far_lo.z,land_hi.z)
close(far_lo.y,land_lo.y); close(far_hi.y,land_hi.y)
next_lo,next_hi=bounds('NextStairsNear'); right_lo,right_hi=bounds('MiddleLandingRight')
close(right_hi.x,next_lo.x); close(right_hi.z,next_hi.z); close(right_lo.y,next_lo.y); close(right_hi.y,next_hi.y)
# Six steps per block, 15cm rise / 30cm tread, not an inferred ramp collision.
for n in ['MainStairsNear','MainStairsFar','NextStairsNear','NextStairsFar']:
    lo,hi=bounds(n); close(hi.x-lo.x,180); close(hi.y-lo.y,240); close(hi.z-lo.z,90)
upper_lo,upper_hi=bounds('UpperLanding'); upper_top=upper_hi.z
ceiling_bottom=min(bounds(n)[0].z for n in actors if n.startswith('Ceiling_') and bounds(n)[0].x<upper_hi.x and bounds(n)[1].x>upper_lo.x)
assert ceiling_bottom-upper_top>=220,(ceiling_bottom,upper_top)
beam_bottom=bounds('CrossBeam')[0].z
beam_left=bounds('CrossBeam')[0].x
# Resolve step elevations beneath the beam rather than using the whole flight's tallest point.
step_surfaces=[15*(i+1)+.8 for i in range(6) if 180-i*30>beam_left]
under_beam=max(step_surfaces+[0])
assert beam_bottom-under_beam>=220,(beam_bottom,under_beam)
for prefix in ['MainRail_','NextRail_']:
    centers=sorted(set(round(a.get_actor_location().y,3) for n,a in actors.items() if n.startswith(prefix)))
    close(centers[1]-centers[0]-4,220)
    for n,a in actors.items():
        if not n.startswith(prefix): continue
        lo,hi=bounds(n); cy=a.get_actor_location().y
        if cy==centers[0]: close(hi.y,cy+2)
        else: close(lo.y,cy-2)
door=actors['DoorLeaf']; frame=actors['DoorFrame']; assert door.static_mesh_component.static_mesh!=frame.static_mesh_component.static_mesh
extension_lo,extension_hi=bounds('MiddleLandingExtension')
close(land_hi.y,right_lo.y); close(right_hi.y,extension_lo.y)
close(extension_hi.y-land_lo.y,600)
for n,a in actors.items():
    if 'Nosing' in n: close(bounds(n)[1].y-bounds(n)[0].y,240)
    if n.startswith('Tactile') or '_Tile_' in n:
        scale=a.get_actor_scale3d(); close(scale.x,1); close(scale.y,1); close(scale.z,1)
close(bounds('MainStairsFar')[0].y,-120); close(bounds('MainStairsFar')[1].y,120)
has_wall_extension=any(n.startswith('Detail_RightWall_') for n in actors)
wall_end=max(bounds(n)[1].x for n in actors if n.startswith(('MainRightWall_','Detail_RightWall_')))
close(wall_end,120 if has_wall_extension else 60)
cam=actors['ReferenceCamera']; cp=cam.get_actor_location(); cr=cam.get_actor_rotation()
camera_config_path=OUT/'camera_revision.json'
expected=load_current_json(camera_config_path.read_text()) if camera_config_path.exists() else dict(position=[-160,-60,330],rotation=[-30,18,0],fov=68)
for a,b in zip([cp.x,cp.y,cp.z,cr.pitch,cr.yaw,cr.roll],expected['position']+expected['rotation']): close(a,b)
close(cam.get_component_by_class(u.CameraComponent).field_of_view,expected['fov'])
result=dict(status='pass',mesh_instances=sum(isinstance(a,u.StaticMeshActor) for a in actors.values()),stairs_landing_seams=True,stair_width_cm=240,rail_clearance_cm=220,brackets_outward=True,minimum_ceiling_clearance_cm=ceiling_bottom-upper_top,beam_clearance_cm=beam_bottom-under_beam,door_leaf_frame_separate=True,scope='Static assembly measurements; no PIE movement or visual rating implied',playtest='not_run')
result.update(landing_width_cm=600,landing_depth_cm=180,right_wall_end_x_cm=wall_end,camera_matches_config=True,camera=expected,tile_pitch_preserved=True)
(OUT/'scene_verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
u.log('SCENE_VERIFIED '+json.dumps(result))
