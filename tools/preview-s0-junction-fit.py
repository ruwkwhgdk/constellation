"""Preview only: fit vertical infill below existing upper floor underside."""
a = next(a for a in A.get_all_level_actors() if a.get_name() == 'StaticMeshActor_797')
assert a.get_actor_label() == 'classroom_start_floor_22'
scale = a.get_actor_scale3d()
assert abs(scale.x-6)<.001 and abs(scale.y-2.5)<.001 and abs(scale.z-1)<.001
before = str(a.get_actor_transform())
a.set_actor_scale3d(u.Vector(6,2.375,1))
center, extent = a.get_actor_bounds(False)
assert abs(center.z+extent.z-950)<.1
assert abs(center.z-extent.z)<.1
(O/'changes.json').write_text(json.dumps([dict(name=a.get_name(),label=a.get_actor_label(),old_transform=before,new_transform=str(a.get_actor_transform()),reason='Vertical infill top1000 overlaps floor19 edge950..1000; fit infill top to underside950. Existing walking floor untouched.')],indent=2))
tag='art1'
shots=[('junction',(2600,900,700),(0,110)),('concept',(2900,900,700),(-20,-138))]
S.update(i=0,sent=False,t=time.monotonic())
