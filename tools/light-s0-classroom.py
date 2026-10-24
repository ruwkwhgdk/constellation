"""S0 reference lighting, window reflection and large rock silhouette pass. Unsaved trial."""
import unreal as u,json,time
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/LightingPass_20261017'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);AT=u.AssetToolsHelpers.get_asset_tools()
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
src=(R/'tools/apply-s0-wet-floor.py').read_text();exec(src[src.index('class G:'):src.index('# World coordinates')])
src=(R/'tools/polish-s0-wet-floor.py').read_text();exec(src[src.index('NOISE='):src.index('floor=material')])
name='M_S0_CoolWindow'
glass=E.load_asset(D+'/'+name) if E.does_asset_exist(D+'/'+name) else AT.create_asset(name,D,u.Material,u.MaterialFactoryNew())
for n in list(M.get_material_expressions(glass)):M.delete_material_expression(glass,n)
g=G(glass);p=g.n(u.MaterialExpressionWorldPosition)
c=g.custom(NOISE+'''float cloud=n.fbm(P.yz/65.);
float frost=n.noise(P.yz/8.);
return lerp(float3(.012,.045,.072),float3(.055,.16,.24),cloud)*lerp(.8,1.1,frost);''',{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(c,u.MaterialProperty.MP_BASE_COLOR);g.prop(c,u.MaterialProperty.MP_EMISSIVE_COLOR)
g.prop(g.c(.38),u.MaterialProperty.MP_ROUGHNESS)
M.recompile_material(glass);assert E.save_loaded_asset(glass,False)
changes=[]
for i in range(5):
 a=actors['ART3_WindowInfill'+str(i)];c=a.static_mesh_component
 changes.append([a.get_name(),a.get_actor_label(),c.get_name(),0,c.get_material(0).get_path_name(),glass.get_path_name()]);c.set_material(0,glass)

key=actors['ART_SchoolCave_CeilingKey'].get_component_by_class(u.LightComponent)
key.set_intensity(1.15);key.set_light_color(u.LinearColor(1,.88,.70))
actors['S0_WetPolish_CoolCeilingBounce'].get_component_by_class(u.LightComponent).set_intensity(35.)

def rect(label,pos,rot,intensity,width,height,color):
 a=actors.get(label) or A.spawn_actor_from_class(u.RectLight,u.Vector(*pos),u.Rotator(pitch=rot[0],yaw=rot[1]))
 a.set_actor_label(label);a.set_folder_path('classroom_start/ReferenceLighting')
 c=a.rect_light_component;c.set_mobility(u.ComponentMobility.MOVABLE)
 c.set_editor_property('intensity_units',u.LightUnits.CANDELAS);c.set_intensity(intensity)
 c.set_editor_property('specular_scale',.08);c.set_intensity(intensity*.35)
 c.set_attenuation_radius(2200);c.set_light_color(u.LinearColor(*color));c.set_cast_shadows(True)
 c.set_editor_property('source_width',width);c.set_editor_property('source_height',height)
 return a
rect('S0_Ref_WindowBlue_0',(435,1490,260),(-12,0),45,270,300,(.20,.55,1.0))
rect('S0_Ref_WindowBlue_1',(435,740,260),(-12,0),30,270,300,(.20,.55,1.0))
rect('S0_Ref_WindowBlue_2',(435,-1510,260),(-12,0),35,270,300,(.20,.55,1.0))
rect('S0_Ref_CaveBlue',(2250,-1940,470),(-25,90),65,420,260,(.18,.72,1.0))

# Angular layered faces sit inside the bounds of the existing collision masses.
rock=E.load_asset(D+'/M_S0_ArtRock')
parts=[(2700,-1640,180,430,320,500,23),(2960,-1750,150,380,390,460,-32),(2480,-1870,130,330,340,370,60),
 (640,-2260,550,430,370,490,15),(780,-2440,690,400,360,390,-25)]
for i,(x,y,z,w,l,h,yaw) in enumerate(parts):
 label='S0_Ref_RockFace_%02d'%i
 a=actors.get(label) or A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,z),u.Rotator(yaw=yaw))
 a.set_actor_label(label);a.set_folder_path('classroom_start/ReferenceLighting')
 mesh=E.load_asset('/Game/LuosCaves/Meshes/Props_Rocks/SM_LCave_P_Rock_%02d'%(40+i*3));assert mesh
 c=a.static_mesh_component;c.set_static_mesh(mesh);c.set_material(0,rock);a.set_actor_enable_collision(False)
 box=mesh.get_bounding_box();sz=box.max-box.min
 a.set_actor_scale3d(u.Vector(w/max(sz.x,1),l/max(sz.y,1),h/max(sz.z,1)))
 center,extent=a.get_actor_bounds(False);loc=a.get_actor_location();a.set_actor_location(u.Vector(loc.x+x-center.x,loc.y+y-center.y,loc.z+z-center.z),False,True)
(O/'allowed-material-changes.json').write_text(json.dumps(changes,indent=2))
rows=[];lights=[]
capture=(R/'tools/review-s0-light.py').read_text();exec(capture[capture.index('cmd=u.SystemLibrary'):])

