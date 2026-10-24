"""Approved S0 concept: irregular rock fascia below existing playable ledges.
No original actor transform, mesh, material or collision changes. Unsaved preview.
"""
import unreal as u,json,time,random
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/EdgePass_20261017'
E=u.EditorAssetLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
assert not any(a.get_actor_label().startswith('S0_Edge_') for a in A.get_all_level_actors()),'Pass already applied; inspect instead of duplicating.'
rock=E.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_ArtRock');assert rock
rng=random.Random(17025);records=[]
def piece(label,center,size,yaw,index):
 mesh=E.load_asset('/Game/LuosCaves/Meshes/Rock_Walls/Walls_08/SM_LCave_P_Wall%02d_08'%index);assert mesh
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*center),u.Rotator(yaw=yaw))
 a.set_actor_label(label);a.set_folder_path('classroom_start/EdgePass')
 a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_material(0,rock)
 a.set_actor_enable_collision(False)
 # Fit world bounds after rotation so the top stays below the playable slab.
 box=mesh.get_bounding_box();sz=box.max-box.min
 local=(size[1],size[0],size[2]) if abs(yaw)==90 else size
 a.set_actor_scale3d(u.Vector(*(local[i]/max((sz.x,sz.y,sz.z)[i],1) for i in range(3))))
 c,e=a.get_actor_bounds(False);p=a.get_actor_location()
 a.set_actor_location(u.Vector(p.x+center[0]-c.x,p.y+center[1]-c.y,p.z+center[2]-c.z),False,True)
 c,e=a.get_actor_bounds(False)
 records.append(dict(label=label,center=[c.x,c.y,c.z],extent=[e.x,e.y,e.z]))
 return a
# Continuous rock-wall relief is embedded into the slab fascia, not separate stones.
for i,y in enumerate([-1450,-350,750,1850]):
 piece('S0_Edge_Upper_%02d'%i,(415,y,765),(80,1200,80),-90,1+i%2)
for i,x in enumerate([1150,1750,2350]):
 piece('S0_Edge_Lower_%02d'%i,(x,-2000,320),(720,80,150),0,1+i%2)
vine=E.load_asset('/Game/Constellation/Environments/Shared/Props/SM_Vine/SM_Vine');assert vine
for i,(x,y,z,yaw,scale) in enumerate([(465,-1650,655,90,1.0),(465,2100,665,90,.85),(1820,-1950,275,0,.65)]):
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,z),u.Rotator(yaw=yaw))
 a.set_actor_label('S0_Edge_Vine_%02d'%i);a.set_folder_path('classroom_start/EdgePass')
 a.static_mesh_component.set_static_mesh(vine);a.set_actor_scale3d(u.Vector(scale,scale,scale));a.set_actor_enable_collision(False)
(O/'edge-bounds.json').write_text(json.dumps(records,indent=2))
rows=[];lights=[]
capture=(R/'tools/review-s0-edge.py').read_text();exec(capture[capture.index('cmd=u.SystemLibrary'):])
