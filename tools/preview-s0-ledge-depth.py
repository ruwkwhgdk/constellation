"""Unsaved ledge-depth candidate for the approved classroom refinement.

Run only in an exclusively held, freshly loaded editor. Reuses seven existing
non-colliding fascia actors; preserves XY extents and world-space top heights.
Does not save assets or the map. Output is review data, not validation evidence.
"""
import json
from pathlib import Path
import unreal as u

out = Path(u.Paths.project_dir()) / 'Saved/S0WetFloor/LedgeDepth_20261018'
out.mkdir(parents=True, exist_ok=True)
assert not (out / 'candidate.json').exists(), 'Review the existing candidate before rerunning.'
actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
factors = {
    'S0_Edge_Upper_00': 1.9, 'S0_Edge_Upper_01': 1.6,
    'S0_Edge_Upper_02': 1.8, 'S0_Edge_Upper_03': 1.7,
    'S0_Edge_Lower_00': 1.2, 'S0_Edge_Lower_01': 1.35,
    'S0_Edge_Lower_02': 1.15,
}
targets = {}
for actor in actors:
    label = actor.get_actor_label()
    if label in factors:
        assert label not in targets, 'Duplicate fascia label: ' + label
        targets[label] = actor
assert set(targets) == set(factors), 'Latest map has different fascia actors; inspect first.'
for actor in targets.values():
    assert not actor.get_actor_enable_collision(), 'Do not alter colliding geometry.'
    rotation = actor.get_actor_rotation()
    assert abs(rotation.pitch) < .001 and abs(rotation.roll) < .001

def xyz(v):
    return [v.x, v.y, v.z]

records = []
for label, actor in targets.items():
    center, extent = actor.get_actor_bounds(False)
    location, scale = actor.get_actor_location(), actor.get_actor_scale3d()
    records.append(dict(label=label, location=xyz(location), scale=xyz(scale),
                        center=xyz(center), extent=xyz(extent)))
(out / 'before.json').write_text(json.dumps(records, indent=2))
try:
    for row in records:
        actor = targets[row['label']]
        sx, sy, sz = row['scale']
        actor.set_actor_scale3d(u.Vector(sx, sy, sz * factors[row['label']]))
        center, extent = actor.get_actor_bounds(False)
        original_top = row['center'][2] + row['extent'][2]
        position = actor.get_actor_location()
        actor.set_actor_location(u.Vector(position.x, position.y,
                                 position.z + original_top - center.z - extent.z), False, True)
        center, extent = actor.get_actor_bounds(False)
        assert abs(center.z + extent.z - original_top) < .01
        assert all(abs(x-y) < .01 for x,y in zip(xyz(center)[:2],row['center'][:2]))
        assert all(abs(x-y) < .01 for x,y in zip(xyz(extent)[:2],row['extent'][:2]))
        row['candidate_center'] = xyz(center)
        row['candidate_extent'] = xyz(extent)
    (out / 'candidate.json').write_text(json.dumps(records, indent=2))
except Exception:
    for row in records:
        actor = targets[row['label']]
        actor.set_actor_scale3d(u.Vector(*row['scale']))
        actor.set_actor_location(u.Vector(*row['location']), False, True)
    raise
