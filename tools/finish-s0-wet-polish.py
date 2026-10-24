"""Peripheral depth and restrained cave bounce; execute after water look-dev."""
import unreal as u,math
A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.EditorAssetLibrary
by={a.get_actor_label():a for a in A.get_all_level_actors()}
for a in list(by.values()):
 if a.get_actor_label().startswith('S0_WetPolish_Shore'):A.destroy_actor(a)
stone=E.load_asset('/Game/Constellation/Environments/Cave/Sets/SchoolCave/Pass4/M_DetailedStone')
placements=[(520,-1600,270,150,18,15),(510,-950,210,130,12,-15),(530,600,300,150,16,12),(520,1250,240,180,20,-20),(750,2580,300,170,22,30),(1250,2600,330,180,15,-10),(1830,2580,260,190,18,24),(3030,1650,260,160,16,72),(3080,1000,230,160,12,105),(3070,-800,250,150,18,80)]
for i,(x,y,w,l,h,yaw) in enumerate(placements):
 path='/Game/LuosCaves/Meshes/Props_Rocks/SM_LCave_P_Free_Rock_%02d'%(1+i%3)
 mesh=E.load_asset(path);assert mesh,path
 box=mesh.get_bounding_box();size=box.max-box.min
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,0),u.Rotator(yaw=yaw))
 a.set_actor_label('S0_WetPolish_Shore_%02d'%i);a.set_folder_path('classroom_start/WetFloor')
 c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,stone);a.set_actor_enable_collision(False)
 a.set_actor_scale3d(u.Vector(w/max(size.x,1),l/max(size.y,1),h/max(size.z,1)))
 center,extent=a.get_actor_bounds(False);loc=a.get_actor_location()
 # Top half of a low slab emerges; bottom remains inside the existing ground.
 a.set_actor_location(u.Vector(loc.x+x-center.x,loc.y+y-center.y,loc.z+h*.35-center.z),False,True)
label='S0_WetPolish_RockFill'
a=by.get(label) or A.spawn_actor_from_class(u.SpotLight,u.Vector(1800,1000,320),u.Rotator(pitch=35,yaw=30))
a.set_actor_label(label);a.set_folder_path('classroom_start/WetFloor')
c=a.spot_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
c.set_editor_property('intensity_units',u.LightUnits.UNITLESS);c.set_editor_property('use_inverse_squared_falloff',False)
c.set_intensity(.28);c.set_attenuation_radius(2300);c.set_light_color(u.LinearColor(.30,.54,.65));c.set_cast_shadows(True)
c.set_editor_property('inner_cone_angle',25.0);c.set_editor_property('outer_cone_angle',65.0);c.set_editor_property('source_radius',120.0)
label='S0_WetPolish_CoolCeilingBounce'
a=by.get(label) or A.spawn_actor_from_class(u.RectLight,u.Vector(1800,-900,1800),u.Rotator(pitch=-90))
a.set_actor_label(label);a.set_folder_path('classroom_start/WetFloor')
c=a.rect_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
c.set_editor_property('intensity_units',u.LightUnits.CANDELAS);c.set_intensity(70.)
c.set_attenuation_radius(3000);c.set_light_color(u.LinearColor(.28,.57,.8));c.set_cast_shadows(True)
c.set_editor_property('source_width',1200.);c.set_editor_property('source_height',800.)


