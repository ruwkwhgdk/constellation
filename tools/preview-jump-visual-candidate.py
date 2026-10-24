"""Apply visual candidate in memory. Call after loading the real map; never save map/graph here."""
import unreal as u,math,json
from pathlib import Path

def apply_jump_visual_candidate():
 def prop(o,**kw):
  for k,v in kw.items():o.set_editor_property(k,v)
  return o
 actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
 stage=next(a for a in actors if isinstance(a,u.JumpAcquisitionStage));star=stage.get_editor_property('star');origin=star.get_actor_location()
 mesh=star.get_component_by_class(u.StaticMeshComponent);mesh.set_relative_scale3d(u.Vector(.28,.28,.28))
 prop(stage,contact_light_intensity=90.,absorption_light_intensity=120.,face_fill_intensity=35.)
 folder='/Game/Constellation/VFX/JumpAcquisition';path=folder+'/M_StarSurface_Review'
 mat=u.load_asset(path)
 if not mat:
  mat=u.AssetToolsHelpers.get_asset_tools().create_asset('M_StarSurface_Review',folder,u.Material,u.MaterialFactoryNew())
  prop(mat,shading_model=u.MaterialShadingModel.MSM_UNLIT)
  def expr(c,x,y):return u.MaterialEditingLibrary.create_material_expression(mat,c,x,y)
  color=expr(u.MaterialExpressionConstant3Vector,-700,0);prop(color,constant=u.LinearColor(1.7,.9,.22,1))
  noise=expr(u.MaterialExpressionNoise,-900,220);prop(noise,scale=.08,quality=1,levels=2)
  amount=expr(u.MaterialExpressionMultiply,-650,200);prop(amount,const_b=.35)
  bias=expr(u.MaterialExpressionAdd,-450,200);prop(bias,const_b=.65)
  final=expr(u.MaterialExpressionMultiply,-200,0)
  for a,ap,b,bp in [(noise,'',amount,'A'),(amount,'',bias,'A'),(color,'',final,'A'),(bias,'',final,'B')]:u.MaterialEditingLibrary.connect_material_expressions(a,ap,b,bp)
  u.MaterialEditingLibrary.connect_material_property(final,'',u.MaterialProperty.MP_EMISSIVE_COLOR)
  u.MaterialEditingLibrary.recompile_material(mat);assert u.EditorAssetLibrary.save_loaded_asset(mat,False)
 mesh.set_material(0,mat)
 def pose(p,t):
  p=origin+u.Vector(*p);t=origin+u.Vector(*t)
  return u.Transform(location=p,rotation=u.MathLibrary.find_look_at_rotation(p,t),scale=u.Vector(1,1,1))
 views={'A':pose((180,280,215),(-45,0,130)),'Inspect':pose((130,245,195),(-50,0,138)),
        'Hand':pose((-15,115,168),(-43,0,148)),'Face':pose((25,140,183),(-92,0,151)),
        'Absorb':pose((108.4,215.6,188.16),(-58,0,130)),'After':pose((110,220,195),(-95,0,128))}
 a=u.load_asset('/Game/SceneDirector/School/DA_JumpAcquisition');cameras=list(a.get_editor_property('cameras'));prop(cameras[0],transform=views['A']);prop(a,cameras=cameras)
 steps=list(a.get_editor_property('steps'));N=u.DirectorNodeType
 moves=[s for s in steps if s.get_editor_property('type')==N.CAMERA_MOVE]
 for s,name in zip(moves,['Inspect','Inspect','Inspect','Absorb','After']):
  x=views[name];r=x.rotation.rotator();prop(s,destination=prop(u.DirectorVectorInput(),value=x.translation),rotation=prop(u.DirectorVectorInput(),value=u.Vector(r.roll,r.pitch,r.yaw)))
  if s in moves[1:3]:
   i=steps.index(s);old=s.get_editor_property('duration');prop(s,duration=1/30)
   prop(steps[i+1],duration=steps[i+1].get_editor_property('duration')+old-1/30)
 # Reach is the animation handoff marker at the start of the slow inspection push-in.
 def cue_name(s):return str(s.get_editor_property('action_parameters').get_editor_property('identifier')) if s.get_editor_property('type')==N.GAME_ACTION else ''
 reach=next(s for s in steps if cue_name(s)=='Reach');steps.remove(reach)
 prop(reach,action_parameters=prop(u.DirectorActionParameters(),identifier='Reach',value=4.5))
 steps.insert(steps.index(moves[0]),reach)
 for s,n in zip(steps,steps[1:]):prop(s,next_nodes=[n.id])
 shot=next(s for s in steps if s.get_editor_property('type')==N.CAMERA_SWITCH)
 frames=sum(max(1,math.floor(s.get_editor_property('duration')*30+.50001)) for s in steps if s.get_editor_property('type') in {N.WAIT,N.CAMERA_MOVE,N.DIALOGUE})
 prop(shot,duration=frames/30,blend_seconds=0.);prop(a,steps=steps);result=u.SceneDirectorLibrary.compile_director(a);assert '생성 완료' in str(result),str(result)
 out=globals().get('JUMP_REVIEW_DIR',Path(u.Paths.project_dir())/'Saved/JumpAcquisition/VisualCandidate01');out.mkdir(exist_ok=True)
 (out/'candidate.json').write_text(json.dumps({'revision':'v03 user timing feedback','initial_transition':'cut','reach':'starts with Inspect push-in','contact_surprise':'hold Inspect','absorb':'small chest push from Inspect','saved_map':False,'saved_graph':False,'star_scale':.28,'star_center':str(mesh.get_world_location()),'local_bounds':str(mesh.get_local_bounds()),'compile':str(result),'camera_side':'positive Y; heroine left, star right'},ensure_ascii=False,indent=2),encoding='utf8')
 return a,stage,star
