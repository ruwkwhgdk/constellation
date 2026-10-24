import unreal as u,json,time,traceback
from pathlib import Path
R=Path(u.Paths.project_dir());O=R/'Saved/S0WetFloor/WallPass_20261017'
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;A=u.get_editor_subsystem(u.EditorActorSubsystem);AT=u.AssetToolsHelpers.get_asset_tools()
assert u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
actors={a.get_actor_label():a for a in A.get_all_level_actors()}
D='/Game/Constellation/Environments/School/Sets/StartingClassroom/WetFloor'
source=(R/'tools/art-s0-classroom.py').read_text()
start=source.index("src=(R/'tools/apply-s0-wet-floor.py')")
end=source.index('# Plaster:')
exec(source[start:end])
plaster=material('M_S0_PeelingPlaster_V6');plaster.set_editor_property('tangent_space_normal',False)
g=G(plaster);p=g.n(u.MaterialExpressionWorldPosition)
clean=tri(g,p,False,'/Game/ModulAbandJPSchool/Textures/T_InPlaster_Clean_A',180)
worn=tri(g,p,False,'/Game/ModulAbandJPSchool/Textures/T_ExPlaster_Worn_A',180)
color=g.custom(NOISE+"""float2 q=float2(P.x+P.y,P.z);
float coarse=n.fbm(q/float2(140,230));
float fine=n.noise(q/9.);
float h=coarse+.15*(fine-.5);
float paint=smoothstep(.39,.41,h);
float rim=smoothstep(.378,.39,h)*(1-smoothstep(.41,.425,h));
float drips=smoothstep(.53,.7,n.fbm(q/float2(28,500)));
float damp=(1-smoothstep(10,220,P.z))*.35+drips*.13;
float3 base=lerp(W*float3(.34,.35,.31),C*float3(.62,.57,.46),paint);
return base*lerp(1,.55,rim)*lerp(1,.55,saturate(damp));""",{'P':p,'C':clean,'W':worn},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(color,u.MaterialProperty.MP_BASE_COLOR)
g.prop(tri(g,p,True,'/Game/ModulAbandJPSchool/Textures/T_ExPlaster_Worn_N',180),u.MaterialProperty.MP_NORMAL)
g.prop(g.c(.84),u.MaterialProperty.MP_ROUGHNESS);finish(plaster)
# Separate instance of the frosted panes; render both sides of the existing single-sided mesh.
glass=material('M_S0_WindowGlass_V6');glass.set_editor_property('two_sided',True)
g=G(glass);p=g.n(u.MaterialExpressionWorldPosition)
c=g.custom(NOISE+"""float cloud=n.fbm(P.yz/65.);float frost=n.noise(P.yz/8.);
return lerp(float3(.004,.014,.023),float3(.017,.045,.07),cloud)*lerp(.75,1.1,frost);""",{'P':p},u.CustomMaterialOutputType.CMOT_FLOAT3)
g.prop(c,u.MaterialProperty.MP_BASE_COLOR);g.prop(c,u.MaterialProperty.MP_EMISSIVE_COLOR);g.prop(g.c(.48),u.MaterialProperty.MP_ROUGHNESS);finish(glass)
transforms=[]
for label,a in actors.items():
 if label.startswith('ART3_WindowFrame'):
  before=str(a.get_actor_transform());pos=a.get_actor_location()
  a.set_actor_location(u.Vector(pos.x+25,pos.y,pos.z),False,True)
  transforms.append({'name':a.get_name(),'label':label,'before':before,'after':str(a.get_actor_transform())})
(O/'allowed-transforms.json').write_text(json.dumps(transforms,indent=2))
changes=[]
for label,a in actors.items():
 for c in a.get_components_by_class(u.StaticMeshComponent):
  for i,m in enumerate(c.get_materials()):
   if not m:continue
   new=plaster if m.get_path_name()==D+'/M_S0_ArtPlaster.M_S0_ArtPlaster' else glass if label.startswith('ART3_WindowInfill') else None
   if new:
    changes.append([a.get_name(),label,c.get_name(),i,m.get_path_name(),new.get_path_name()]);c.set_material(i,new)
(O/'allowed-material-changes.json').write_text(json.dumps(changes,indent=2))
rows=[];lights=[]
capture=(R/'tools/review-s0-wall.py').read_text();exec(capture[capture.index('cmd=u.SystemLibrary'):])
