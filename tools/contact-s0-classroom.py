"""S0 V8: sparse wall-foot stone clusters, hanging growth, warm focal lighting.
Only additive local decoration; original gameplay geometry remains unchanged.
"""
import unreal as u,json,time,random,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/ContactPass_20261017'
E=u.EditorAssetLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
assert not any(a.get_actor_label().startswith('S0_Contact_') for a in A.get_all_level_actors())
review=(R/'tools/review-s0-contact.py').read_text()
exec(review[review.index('rows=[];lights=[]'):review.index('cmd=u.SystemLibrary')])
(O/'baseline-actors.json').write_text(json.dumps(rows,indent=2))
(O/'baseline-lights.json').write_text(json.dumps(lights,indent=2))
rock=E.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_ArtRock');assert rock
created=[];bounds=[]
def mesh_piece(label,path,center,size,yaw,material=None):
    mesh=E.load_asset(path);assert mesh
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*center),u.Rotator(yaw=yaw))
    a.set_actor_label('S0_Contact_'+label);a.set_folder_path('classroom_start/ContactPass')
    a.static_mesh_component.set_static_mesh(mesh)
    if material:a.static_mesh_component.set_material(0,material)
    a.set_actor_enable_collision(False)
    # Fit rotated world bounds to the desired envelope, preserving the authored mesh.
    c,e=a.get_actor_bounds(False)
    a.set_actor_scale3d(u.Vector(size[0]/max(e.x*2,1),size[1]/max(e.y*2,1),size[2]/max(e.z*2,1)))
    c,e=a.get_actor_bounds(False);p=a.get_actor_location()
    a.set_actor_location(u.Vector(p.x+center[0]-c.x,p.y+center[1]-c.y,p.z+center[2]-c.z),False,True)
    c,e=a.get_actor_bounds(False)
    created.append(a);bounds.append(dict(label=a.get_actor_label(),center=[c.x,c.y,c.z],extent=[e.x,e.y,e.z]))
    return a
rng=random.Random(17028)
# Three-stone clusters embedded in the wall-foot, with broad clear gaps between.
# The main entry at y=0 and the classroom centre remain free of decoration.
for i,(x,y) in enumerate([(445,-1770),(445,-1120),(445,1120),(445,1870),(445,2430),(2450,-1600),(2870,-1490)]):
    for j in range(3):
        w=rng.uniform(55,110);length=rng.uniform(75,145);h=rng.uniform(18,42)
        mesh_piece('Toe_%02d_%d'%(i,j),'/Game/LuosCaves/Meshes/Props_Rocks/SM_LCave_P_Rock_%02d'%(40+(i+j)%4*3),
                   (x+j*22,y+(j-1)*65,h*.35),(w,length,h),rng.uniform(-50,50),rock)
# Relief at the two cave/wall seams; keep below the playable ledges.
for i,(center,size,yaw) in enumerate([((2480,-1900,90),(270,130,170),0)]):
    mesh_piece('Seam_%02d'%i,'/Game/LuosCaves/Meshes/Rock_Walls/Walls_08/SM_LCave_P_Wall02_08',center,size,yaw,rock)
vine=E.load_asset('/Game/Constellation/Environments/Shared/Props/SM_Vine/SM_Vine');assert vine
for i,(x,y,z,yaw,scale) in enumerate([(450,-1550,750,90,1.35),(450,-1440,730,90,.85),(450,2050,745,90,1.25),(450,2130,720,90,.75),(1960,-1960,360,0,1.05),(2070,-1960,345,0,.7)]):
    a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,z),u.Rotator(yaw=yaw))
    a.set_actor_label('S0_Contact_Vine_%02d'%i);a.set_folder_path('classroom_start/ContactPass')
    a.static_mesh_component.set_static_mesh(vine);a.set_actor_scale3d(u.Vector(scale,scale,scale));a.set_actor_enable_collision(False);created.append(a)
# Local pools of warm light link the plaster, desks and wet floor.
for i,(pos,rot,power,radius,cone) in enumerate([((850,-1050,680),(-70,175),1.05,1700,60),((1050,1450,680),(-72,-165),.70,1750,60)]):
    a=A.spawn_actor_from_class(u.SpotLight,u.Vector(*pos),u.Rotator(pitch=rot[0],yaw=rot[1]))
    a.set_actor_label('S0_Contact_Warm_%02d'%i);a.set_folder_path('classroom_start/ContactPass')
    c=a.spot_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
    c.set_editor_property('intensity_units',u.LightUnits.UNITLESS);c.set_editor_property('use_inverse_squared_falloff',False)
    c.set_intensity(power);c.set_attenuation_radius(radius);c.set_light_color(u.LinearColor(1,.67,.34));c.set_cast_shadows(True)
    c.set_editor_property('inner_cone_angle',8.);c.set_editor_property('outer_cone_angle',float(cone));c.set_editor_property('source_radius',140.)
    created.append(a)
(O/'new-labels.json').write_text(json.dumps([a.get_actor_label() for a in created],indent=2))
(O/'new-bounds.json').write_text(json.dumps(bounds,indent=2))
rows=[];lights=[]
exec(review[review.index('cmd=u.SystemLibrary'):])
