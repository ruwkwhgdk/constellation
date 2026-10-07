import bpy, json
from pathlib import Path
out = Path(__file__).resolve().parent
rig = bpy.data.objects.get('Heroine_AnimationRig')
assert rig
rows = {b.name: {'head': list(b.head_local), 'tail': list(b.tail_local), 'parent': b.parent.name if b.parent else None}
        for b in rig.data.bones if any(x in b.name for x in ('arm','hand','thigh','shin','foot','torso','hips','spine'))}
(out/'source_inspection.json').write_text(json.dumps({'rig_scale':list(rig.scale), 'fps':bpy.context.scene.render.fps,
    'action':str(rig.animation_data.action.name) if rig.animation_data and rig.animation_data.action else None,
    'bones':rows, 'objects':[o.name for o in bpy.data.objects]}, indent=2), encoding='utf-8')
print('CARRY_SOURCE_INSPECTION_COMPLETE')
