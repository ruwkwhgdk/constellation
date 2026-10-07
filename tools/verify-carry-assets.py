"""Reload the saved carry integration and compile the player Blueprints."""
import json
from pathlib import Path
import unreal as u
out=Path(u.Paths.project_dir()).resolve()/'Saved/CarryReview'
lib=u.EditorAssetLibrary
hero=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/BP_Player_Heroine')
abp=u.load_asset('/Game/Constellation/Characters/Heroine/Blueprints/ABP_Player_Heroine')
reports={'input':u.CarryEditorLibrary.install_carry_input(hero),'overlay':u.CarryEditorLibrary.install_carry_overlay(abp)}
gm=u.load_asset('/Game/Constellation/Review/Carry/BP_CarryReviewGameMode')
u.get_default_object(gm.generated_class()).set_editor_property('hud_class',u.load_asset('/Game/Constellation/UI/Blueprints/BP_HUD').generated_class())
assert lib.save_loaded_asset(gm,False)
review_path='/Game/Constellation/Review/Carry/Maps/L_Carry_Review'
assert u.EditorLoadingAndSavingUtils.load_map(review_path)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
for actor in actors.get_all_level_actors():
    if isinstance(actor,u.DirectionalLight):
        actor.set_actor_rotation(u.Rotator(-45,135,0),False)
        actor.get_component_by_class(u.DirectionalLightComponent).set_editor_property('intensity',1.)
    if actor.get_actor_label()=='Carry_ReviewFill':
        actor.get_component_by_class(u.PointLightComponent).set_editor_property('intensity',400.)
if not any(actor.get_actor_label()=='Carry_ReviewFill' for actor in actors.get_all_level_actors()):
    fill=actors.spawn_actor_from_class(u.PointLight,u.Vector(200,-200,250))
    fill.set_actor_label('Carry_ReviewFill'); light=fill.get_component_by_class(u.PointLightComponent)
    light.set_editor_property('intensity',400.); light.set_editor_property('attenuation_radius',800.)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert u.EditorLoadingAndSavingUtils.save_map(world,review_path)
for obj in (hero,abp): assert lib.save_loaded_asset(obj,False)
assert all('errors=0' in x and 'warnings=0' in x for x in reports.values()),reports
reports['slots']={}
for name in ('Pickup','Place','Throw','Hold','Aim'):
    am=u.load_asset('/Game/Constellation/Characters/Heroine/Base/Animation/Carry/AM_Carry_'+name)
    slots=[str(track.get_editor_property('slot_name')) for track in am.get_editor_property('slot_anim_tracks')]
    assert slots==['CarryUpperBody' if name in ('Hold','Aim') else 'DefaultSlot'],(name,slots)
    reports['slots'][name]=slots
    seq=u.load_asset('/Game/Constellation/Characters/Heroine/Base/Animation/Carry/AS_Carry_'+name+'_Game')
    assert am.get_editor_property('slot_anim_tracks')[0].get_editor_property('anim_track').get_editor_property('anim_segments')[0].get_editor_property('anim_reference')==seq
    options=u.AnimPoseEvaluationOptions(); options.evaluation_type=u.AnimDataEvalType.COMPRESSED
    pose=u.AnimPoseExtensions.get_anim_pose_at_time(seq,0.,options)
    hip=u.AnimPoseExtensions.get_bone_pose(pose,'Hips',u.AnimPoseSpaces.LOCAL).translation.z
    assert abs(hip-112.154167)<1.,(name,hip)
context=u.load_asset('/Game/Constellation/Input/IAC_Default')
mappings=context.get_editor_property('default_key_mappings').get_editor_property('mappings')
reports['keys']=[{'action':x.get_editor_property('action').get_name(),'key':str(x.get_editor_property('key').get_editor_property('key_name'))} for x in mappings]
exec(compile((Path(u.Paths.project_dir())/'tools/test-carry-unreal.py').read_text(),str(out/'inspect.py'),'exec'))
(out/'reload-verification.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
u.log('CARRY_RELOAD_VERIFIED '+json.dumps(reports))
