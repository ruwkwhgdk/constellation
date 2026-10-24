a=next(a for a in A.get_all_level_actors() if a.get_name()=='StaticMeshActor_796')
assert a.get_actor_label()=='classroom_start_floor_21'
s=a.get_actor_scale3d();assert abs(s.x-2)<.001 and abs(s.y-2.5)<.001 and abs(s.z-1)<.001
before=str(a.get_actor_transform())
a.set_actor_scale3d(u.Vector(2,2.375,1))
c,e=a.get_actor_bounds(False);assert abs(c.z+e.z-950)<.1 and abs(c.z-e.z)<.1
(O/'transform-changes.json').write_text(json.dumps([dict(name=a.get_name(),label=a.get_actor_label(),old_transform=before,new_transform=str(a.get_actor_transform()))],indent=2))
tag='art2';shots=[('upper',(1450,1500,1500),(-30,105)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
