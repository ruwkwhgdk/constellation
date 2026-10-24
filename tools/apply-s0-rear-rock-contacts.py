"""Apply reviewed rear-wall foot details only to the already-open maintained map.
Run within its owning editor; never load/switch the user's current map.
"""
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir())
O=R/'ArtSource/SchoolOpening/WetFloor/RearRockContacts'
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_path_name()=='/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool.AbandonedSchool','Open maintained AbandonedSchool before applying'
A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert not any(a.get_actor_label().startswith('S0_Art_RearRockContact_') for a in A.get_all_level_actors()),'Already applied; do not duplicate'
protected=json.loads((R/'ArtSource/SchoolOpening/WetFloor/PROTECTED_LAYOUT.json').read_text())
actors={a.get_name():a for a in A.get_all_level_actors()}
for row in protected['actors']:
 p=actors[row['name']].get_actor_location()
 assert all(abs(v-e)<.1 for v,e in zip([p.x,p.y,p.z],row['position_cm'])), 'Protected layout changed: re-audit first'
# Small foot contacts along the rear wall, outside both protected ramp volumes.
contact=[]
mat=u.EditorAssetLibrary.load_asset('/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor/M_S0_ShallowRock_V18')
for i,(x,y,width,height,yaw) in enumerate([(720,1950,130,46,25),(900,1930,80,28,-18),(1720,1940,145,52,60),(1870,1950,85,30,-35),(2070,1950,110,38,12),(3060,1950,130,42,38)]):
 mesh=u.EditorAssetLibrary.load_asset('/Game/LuosCaves/Meshes/Props_Rocks/SM_LCave_P_Rock_%02d'%(1+i%3))
 box=mesh.get_bounding_box();size=box.max-box.min
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,0),u.Rotator(yaw=yaw))
 a.set_actor_label('S0_Art_RearRockContact_%02d'%i);c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,mat)
 a.set_actor_scale3d(u.Vector(width/size.x,55/size.y,height/size.z));a.set_actor_enable_collision(False)
 center,ext=a.get_actor_bounds(False);p=a.get_actor_location();p.x+=x-center.x;p.y+=y-center.y;p.z+=-5-(center.z-ext.z);a.set_actor_location(p,False,True)
 center,ext=a.get_actor_bounds(False)
 assert center.y-ext.y>1780 and center.z-ext.z<0
 contact.append(a)
(O/'contacts.json').write_text(json.dumps([{'name':a.get_name(),'label':a.get_actor_label(),'transform':str(a.get_actor_transform()),'bounds':str(a.get_actor_bounds(False))} for a in contact],indent=2))

# Deliberately leave save to the owning editor after inspecting the result.

