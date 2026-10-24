"""Bounded wall-contact preview: reuse rock detail; no source or walking geometry edit."""
actors={a.get_name():a for a in A.get_all_level_actors()}
source=actors['StaticMeshActor_833'].static_mesh_component
created=[]
# World X/Z patches on the vertical infill y=2000, outside both protected ramp volumes.
for i,(p,scale,yaw) in enumerate([
 ((1920,2045,390),(.48,.70,.20),-22),
 ((1750,2050,770),(.45,.30,.16),18),
 ((2100,2040,70),(.38,.22,.18),-12),
]):
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*p),u.Rotator(pitch=0,yaw=yaw,roll=90))
 a.set_actor_label('S0_WallContact_Review_'+str(i))
 a.set_folder_path('sector0/StartingClassroom/WetFloor/WallContact')
 c=a.static_mesh_component;c.set_static_mesh(source.static_mesh)
 for slot,m in enumerate(source.get_materials()):c.set_material(slot,m)
 a.set_actor_scale3d(u.Vector(*scale));a.set_actor_enable_collision(False)
 c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
 created.append(dict(name=a.get_name(),label=a.get_actor_label(),transform=str(a.get_actor_transform()),bounds=str(a.get_actor_bounds(False))))
(O/'additions.json').write_text(json.dumps(created,indent=2))
tag='candidate';shots=[('backwall',(1700,400,300),(5,90)),('concept',(2900,900,700),(-20,-138))];S.update(i=0,sent=False,t=time.monotonic())
