"""Apply S0 framing after importing replacement meshes; invoked by importer with -LockerApply."""
import unreal as u,json
from pathlib import Path
R=Path(u.Paths.project_dir()).resolve();A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
aa=A.get_all_level_actors();by={a.get_actor_label():a for a in aa};updated=0
for a in aa:
 for c in a.get_components_by_class(u.StaticMeshComponent):
  if c.static_mesh and c.static_mesh.get_path_name().startswith('/Game/Constellation/Environments/School/Props/SM_Locker/SM_Locker'):
   c.set_editor_property('override_materials',[]);updated+=1
for label,pos,scale in [('S0_MemoryPhoto',(3154,-48,229),(.14,.18,1)),('S0_StarCard',(3154,48,225),(.12,.18,1)),('S0_Note',(3154,48,203),(.095,.095,1))]:
 a=by[label];a.set_actor_location(u.Vector(*pos),False,True);a.set_actor_scale3d(u.Vector(*scale))
charm={'S0_Charm_Body':((3156,-49,178),(.042,.042,.057)),'S0_Charm_Head':((3156,-49,186),(.054,.051,.048)),'S0_Charm_String':((3156,-49,200),(.0024,.0024,.072))}
for a in aa:
 label=a.get_actor_label()
 if label in charm:p,s=charm[label];a.set_actor_location(u.Vector(*p),False,True);a.set_actor_scale3d(u.Vector(*s))
 if label.startswith('S0_Charm_Ear'):
  ears=sorted(x.get_actor_label() for x in aa if x.get_actor_label().startswith('S0_Charm_Ear'));y=-50.8 if label==ears[0] else -47.2
  a.set_actor_location(u.Vector(3156,y,192),False,True);a.set_actor_scale3d(u.Vector(.015,.015,.039))
# Rebuild only our S0 prop surface shaders without emissive output.
for name,tex,col in [('M_MemoryPhoto_Draft','Photo_Memory_Draft',None),('M_ConstellationCard','Card_Constellation',None),('M_StarNote','Note_Stars',None),('M_CharmCream',None,(.7,.57,.42)),('M_CharmPink',None,(.35,.12,.2)),('M_CharmGold',None,(.55,.33,.08))]:
 m=u.load_asset('/Game/SceneDirector/School/S0/'+name);M.delete_all_material_expressions(m)
 if tex:
  n=M.create_material_expression(m,u.MaterialExpressionTextureSample);n.set_editor_property('texture',u.load_asset('/Game/SceneDirector/School/S0/'+tex));pin='RGB'
 else:
  n=M.create_material_expression(m,u.MaterialExpressionConstant3Vector);n.set_editor_property('constant',u.LinearColor(*col));pin=''
 M.connect_material_property(n,pin,u.MaterialProperty.MP_BASE_COLOR)
 r=M.create_material_expression(m,u.MaterialExpressionConstant);r.set_editor_property('r',.8);M.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
 M.recompile_material(m);E.save_loaded_asset(m,False)
by['S0_InteriorFill'].point_light_component.set_intensity(.025)
spot=by.get('S0_VentWarmLight') or A.spawn_actor_from_class(u.SpotLight,u.Vector(3142,0,219),u.Rotator(pitch=-20,yaw=0));spot.set_actor_label('S0_VentWarmLight');spot.set_folder_path('S0 Opening/Props')
c=spot.spot_light_component;c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(.4);c.set_attenuation_radius(180);c.set_inner_cone_angle(25);c.set_outer_cone_angle(45);c.set_light_color(u.LinearColor(1,.69,.36))
a=u.load_asset('/Game/SceneDirector/School/DA_S0_Opening');cams=list(a.get_editor_property('cameras'))
for cam in cams:
 if str(cam.get_editor_property('key'))=='Eyes':
  cam.set_editor_property('field_of_view',115.0)
  t=cam.get_editor_property('transform');t.set_editor_property('translation',u.Vector(3203,0,214.6));cam.set_editor_property('transform',t)
a.set_editor_property('cameras',cams);steps=list(a.get_editor_property('steps'));peeks=0
for s in steps:
 if s.get_editor_property('type')!=u.DirectorNodeType.CAMERA_MOVE:continue
 d=s.get_editor_property('destination');p=d.get_editor_property('value');r=s.get_editor_property('rotation');rv=r.get_editor_property('value')
 if p.distance(u.Vector(3158,0,245))<1 or p.distance(u.Vector(3165,0,214.6))<1:
  peeks+=1;pts=list(s.get_editor_property('motion_points'));assert len(pts)==3
  for pt,t,pos in zip(pts,[0,.7,1.3],[(3203,0,214.6),(3180,0,214.6),(3165,0,214.6)]):pt.set_editor_property('position',u.Vector(*pos));pt.set_editor_property('time',t)
  s.set_editor_property('motion_points',pts);p=u.Vector(3165,0,214.6)
 elif p.distance(u.Vector(3192,0,165))<1:
  p=u.Vector(3203,0,214.6)
  if abs(rv.y+13)<.1:rv.y=-27
 elif p.distance(u.Vector(3187,-5,170))<1:p=u.Vector(3181,-18,220);rv=u.Vector(0,12,228)
 d.set_editor_property('value',p);r.set_editor_property('value',rv);s.set_editor_property('destination',d);s.set_editor_property('rotation',r)
assert peeks==3,peeks
a.set_editor_property('steps',steps);result=u.SceneDirectorLibrary.compile_director(a);assert result is not None;assert E.save_loaded_asset(a,False)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
(R/'ArtSource/SchoolLocker/Review/applied-stage.json').write_text(json.dumps({'locker_components':updated,'peeks':peeks,'compile':str(result),'camera':[3203,0,214.6],'fov':115,'master':'/Game/Constellation/MaterialLibrary/Materials/M_Base_PBR'},ensure_ascii=False,indent=2),encoding='utf8');u.log('LOCKER_STAGE_APPLIED')
