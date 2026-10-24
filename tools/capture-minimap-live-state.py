"""Read-only snapshot of the user's current PIE minimap state. No assets/saves changed."""
import unreal as u
import json
import math
import re
from datetime import datetime
from pathlib import Path

world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
assert world, 'Keep the problem PIE session running while capturing.'
pc = u.GameplayStatics.get_player_controller(world, 0)
pawn = pc.get_controlled_pawn()
assert pawn, 'No possessed pawn in the current PIE world.'
pos = pawn.get_actor_location()
feet = pos.z-pawn.capsule_component.get_scaled_capsule_half_height()
sub = next(o for o in u.ObjectIterator(u.MinimapWorldSubsystem) if o.get_outer()==world)
regions = u.GameplayStatics.get_all_actors_of_class(world, u.MinimapRegionActor)
contact = u.MinimapEditorLibrary.describe_pawn_ground(world)
match = re.search(r'at X=([-\d.]+) Y=([-\d.]+) Z=([-\d.]+)', contact)
ground = [float(value) for value in match.groups()] if match else [pos.x, pos.y, feet]
report = dict(captured_at=datetime.now().isoformat(), world=world.get_path_name(), pawn=pawn.get_path_name(),
              position=[pos.x,pos.y,pos.z], feet=feet,
              grounded=pawn.character_movement.is_moving_on_ground(),
              contact=contact, ground=ground,
              floor=str(sub.get_current_floor_id()), discovered=sub.get_discovered_cell_count(), regions=[])
for actor in regions:
    data=actor.get_editor_property('data')
    if not data:
        report['regions'].append(dict(actor=actor.get_path_name(), data=None))
        continue
    # Runtime classification uses the capsule's ground contact, not its center.
    # Record both cells and the neighboring samples to distinguish a raster gap
    # from a selected layer with no exploration revealed.
    layers=[]
    for floor in data.get_editor_property('floors'):
        x=math.floor((ground[0]-floor.origin.x)/floor.cell_size)
        y=math.floor((ground[1]-floor.origin.y)/floor.cell_size)
        neighbors=[]
        for dy in range(-1,2):
            for dx in range(-1,2):
                nx,ny=x+dx,y+dy
                if not (0<=nx<floor.width and 0<=ny<floor.height):
                    continue
                sample=u.Vector(floor.origin.x+(nx+0.5)*floor.cell_size,
                                floor.origin.y+(ny+0.5)*floor.cell_size, ground[2])
                # Cells/SurfaceZ are protected UPROPERTY arrays. Read through
                # the existing public diagnostic function, never reflection.
                summary=u.MinimapEditorLibrary.describe_floor_samples(data,sample)
                parsed=re.search(r'(?:^|\s)'+re.escape(str(floor.floor_id))+r'=(\d+)@(-?[\d.]+)', summary)
                if parsed:
                    z=float(parsed.group(2))
                    neighbors.append(dict(offset=[dx,dy],cell=int(parsed.group(1)),z=z,
                                          height_error=abs(z-ground[2])))
        layers.append(dict(id=str(floor.floor_id), reference_z=floor.reference_z,
                           cell=[x,y], neighbors=neighbors))
    report['regions'].append(dict(actor=actor.get_path_name(), data=data.get_path_name(),
        reveal_mode=str(data.reveal_mode), reveal_radius=data.reveal_radius,
        foot_samples=u.MinimapEditorLibrary.describe_floor_samples(data,u.Vector(pos.x,pos.y,feet)),
        contact_samples=u.MinimapEditorLibrary.describe_floor_samples(data,u.Vector(*ground)),
        layers=layers))
destination=Path(u.Paths.project_dir())/'Saved/Minimap/live-ramp-report.json'
destination.parent.mkdir(parents=True,exist_ok=True)
destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
archive=destination.with_name('live-ramp-report-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
archive.write_text(destination.read_text(encoding='utf8'),encoding='utf8')
u.log('MINIMAP_LIVE_REPORT '+str(destination))
