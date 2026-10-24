"""Non-colliding rock relief embedded into the existing cave masses."""
for old in list(A.get_all_level_actors()):
 if old.get_actor_label().startswith(('S0_Art_Relief_','S0_Art_Vine_')):A.destroy_actor(old)
# World centers and full bounding dimensions; pieces overlap existing rock, not the main aisle.
parts=[(2700,-1480,125,240,180,220,12),(2930,-1530,235,230,190,210,-28),
 (2530,-1680,240,200,200,190,35),(3070,-1700,300,190,160,180,55),
 (650,-2070,540,210,190,200,20),(820,-2190,675,210,200,210,-15),
 (570,-2430,790,190,180,190,45),(2900,-1750,25,250,230,65,-25)]
for i,(x,y,z,w,l,h,yaw) in enumerate(parts):
 mesh=E.load_asset('/Game/LuosCaves/Meshes/Props_Rocks/SM_LCave_P_Free_Rock_%02d'%(1+i%3));assert mesh
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,z),u.Rotator(yaw=yaw))
 a.set_actor_label('S0_Art_Relief_%02d'%i);a.set_folder_path('classroom_start/ArtPass')
 c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,rock)
 a.set_actor_enable_collision(False)
 box=mesh.get_bounding_box();sz=box.max-box.min
 a.set_actor_scale3d(u.Vector(w/max(sz.x,1),l/max(sz.y,1),h/max(sz.z,1)))
 center,extent=a.get_actor_bounds(False);loc=a.get_actor_location()
 a.set_actor_location(u.Vector(loc.x+x-center.x,loc.y+y-center.y,loc.z+z-center.z),False,True)

# Sparse hanging clusters anchored at slab rims. Existing textured vine, no new clutter.
vine=E.load_asset('/Game/Constellation/Environments/Shared/Props/SM_Vine/SM_Vine');assert vine
for i,(x,y,z,yaw,scale) in enumerate([(415,-1900,725,90,.85),(415,1250,730,90,.8),(415,1650,745,90,.65),(1150,-1990,330,0,.8),(2250,-1990,345,0,.65)]):
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,z),u.Rotator(yaw=yaw))
 a.set_actor_label('S0_Art_Vine_%02d'%i);a.set_folder_path('classroom_start/ArtPass')
 a.static_mesh_component.set_static_mesh(vine);a.set_actor_scale3d(u.Vector(scale,scale,scale));a.set_actor_enable_collision(False)
