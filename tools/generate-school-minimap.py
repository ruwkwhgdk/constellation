"""Run through Unreal Editor Python after compiling MinimapEditorLibrary.

Regeneration preserves author corrections in the existing data asset and adds just
one region actor to the maintained school. A failed generation never saves the map.
"""
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
OUT = ROOT / 'Saved/Minimap'
OUT.mkdir(parents=True, exist_ok=True)
MAP = '/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool'
ASSET = '/Game/Constellation/UI/Minimap/DA_AbandonedSchool'
map_file = ROOT / 'Content/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.umap'
data_file = ROOT / 'Content/Constellation/UI/Minimap/DA_AbandonedSchool.uasset'
backup = OUT / 'BeforeGeneration' / datetime.now().strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True, exist_ok=False)
shutil.copy2(map_file, backup / map_file.name)
if data_file.exists():
    shutil.copy2(data_file, backup / data_file.name)

world = u.EditorLoadingAndSavingUtils.load_map(MAP)
assert world, 'Maintained map did not load'
sub = u.get_editor_subsystem(u.EditorActorSubsystem)
before = {a.get_path_name(): str(a.get_actor_transform()) for a in sub.get_all_level_actors()}
data = u.load_asset(ASSET)
if not data:
    u.EditorAssetLibrary.make_directory(ASSET.rsplit('/', 1)[0])
    factory = u.DataAssetFactory()
    factory.set_editor_property('data_asset_class', u.MinimapRegionData)
    data = u.AssetToolsHelpers.get_asset_tools().create_asset(
        ASSET.rsplit('/', 1)[1], ASSET.rsplit('/', 1)[0], u.MinimapRegionData, factory)
assert data, 'Could not create minimap data asset'
preserved = {key: str(data.get_editor_property(key)) for key in ('marker_overrides', 'manual_markers')}
report = u.MinimapEditorLibrary.build_school_map(world, data)
assert report.startswith("OK "), report
floors = data.get_editor_property('floors')
assert floors and len({str(f.floor_id) for f in floors}) == len(floors), 'Empty or duplicate floor IDs'
assert all(f.cell_size == 50 and f.width > 0 and f.height > 0 for f in floors)
assert preserved == {key: str(data.get_editor_property(key)) for key in preserved}, 'Designer corrections changed'
markers = data.get_editor_property('generated_markers')
assert len({m.source_id for m in markers}) == len(markers), 'Duplicate generated marker IDs'
actors = [a for a in sub.get_all_level_actors() if isinstance(a, u.MinimapRegionActor)
          and (a.get_editor_property('data') == data or a.get_actor_label() == 'Minimap_AbandonedSchool')]
assert len(actors) <= 1, 'Multiple school minimap region actors; resolve explicitly before regeneration'
actor = actors[0] if actors else sub.spawn_actor_from_class(u.MinimapRegionActor, u.Vector(0, 0, 0))
actor.set_actor_label('Minimap_AbandonedSchool')
actor.set_editor_property('data', data)
after = {a.get_path_name(): str(a.get_actor_transform()) for a in sub.get_all_level_actors()}
assert all(after.get(path) == transform for path, transform in before.items()), 'Existing actor transform changed'
assert u.EditorAssetLibrary.save_loaded_asset(data, only_if_is_dirty=False)
assert u.EditorLoadingAndSavingUtils.save_map(world, MAP)
summary = dict(map=MAP, asset=ASSET, backup=str(backup), report=report,
               previous_map_sha256=hashlib.sha256((backup / map_file.name).read_bytes()).hexdigest(),
               map_sha256=hashlib.sha256(map_file.read_bytes()).hexdigest(),
               existing_actor_transforms_preserved=True,
               floors=[dict(id=str(f.floor_id), label=str(f.label), width=f.width, height=f.height,
                            origin=[f.origin.x, f.origin.y], reference_z=f.reference_z,
                            min_z=f.min_z, max_z=f.max_z) for f in floors],
               markers=[dict(id=m.source_id, position=[m.position.x, m.position.y, m.position.z],
                             floor=str(m.floor_id), connected_floor=str(m.connected_floor_id),
                             hidden=m.hidden, verified=m.connection_verified) for m in markers])
summary['objectives'] = [dict(quest=str(b.quest_id), progress=b.progress, inner_progress=b.inner_progress,
                               floor=str(b.floor_id), generated=b.generated)
                         for b in data.get_editor_property('objectives')]
probes = [('PlayerStartFloor', 2600., 0., 0.)]
for a in sub.get_all_level_actors():
    if a.get_class().get_name() in ('BP_School_Door_C', 'BP_Suzume_Door_C', 'BP_Ladder_C'):
        p = a.get_actor_location()
        probes.append((a.get_name(), p.x, p.y, p.z))
summary['surface_probes'] = [dict(actor=n, position=[x, y, z], layers=[]) for n, x, y, z in probes]
for f, row in zip(floors, summary['floors']):
    cells = list(f.get_editor_property('cells'))
    surfaces = list(f.get_editor_property('surface_z'))
    row['floor_cells'] = cells.count(1)
    row['wall_cells'] = cells.count(2)
    for probe in summary['surface_probes']:
        x, y, z = probe['position']
        ix, iy = int((x-f.origin.x)//50), int((y-f.origin.y)//50)
        if not (0 <= ix < f.width and 0 <= iy < f.height):
            continue
        idx = iy*f.width+ix
        if cells[idx] and abs(surfaces[idx]-z) < 600:
            probe['layers'].append(dict(id=str(f.floor_id), cell=cells[idx], surface_z=surfaces[idx]))
(OUT / 'generation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
u.log('MINIMAP_GENERATION_COMPLETE ' + report)
