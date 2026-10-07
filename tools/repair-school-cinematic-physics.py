"""Repair migrated spawn scale and hidden-wall zero scales; preserve original assets and visible interpolation."""
import unreal as u
from pathlib import Path
import shutil,json,hashlib
root=Path(u.Paths.project_dir()).resolve();out=root/'Saved/SceneReleaseValidation';out.mkdir(parents=True,exist_ok=True)
p='/Game/SceneDirector/School/Visual/LS_Appear_Slime_Event_Visual'
f=root/'Content'/(p.removeprefix('/Game/')+'.uasset');backup=out/'Backup'/f.name;backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(f,backup)
a=u.load_asset(p);fixed=[]
for b in a.get_spawnables():
 if not str(b.get_name()).startswith('npc_slime'):continue
 t=b.get_object_template();assert isinstance(t,u.Character)
 component=t.get_editor_property('root_component');assert component
 before=str(component.get_editor_property('relative_scale3d'))
 scales={}
 for track in b.get_tracks():
  if isinstance(track,u.MovieScene3DTransformTrack):
   for section in track.get_sections():
    for channel in section.get_all_channels():
     name=str(channel.get_name())
     if name.startswith('Scale.'):
      keys=channel.get_keys();scales[name.split('.')[1][0]]=keys[0].get_value() if keys else channel.get_default()
 assert len(scales)==3 and all(v>0 for v in scales.values()),scales
 # Spawn happens before Sequencer evaluates the first transform keys. Its template must have a valid scale.
 t.modify();component.modify()
 value=u.Vector(scales['X'],scales['Y'],scales['Z'])
 component.set_editor_property('relative_scale3d',value)
 fixed.append({'name':str(b.get_name()),'before':before,'after':str(value)})
assert len(fixed)==4,fixed
walls=[]
for binding in a.get_bindings():
 if not str(binding.get_name()).startswith('GC_Break_Wall'):continue
 visibility_keys=[]
 for track in binding.get_tracks():
  if isinstance(track,u.MovieSceneVisibilityTrack):
   for section in track.get_sections():
    for channel in section.get_all_channels():
     for key in channel.get_keys():
      visibility_keys.append((key.get_time().frame_number.value,key.get_value()))
 assert visibility_keys,(binding.get_name(),'no explicit visibility keys')
 for track in binding.get_tracks():
  if isinstance(track,u.MovieScene3DTransformTrack):
   for section in track.get_sections():
    for channel in section.get_all_channels():
     if not str(channel.get_name()).startswith('Scale.'):continue
     keys=channel.get_keys()
     for i,key in enumerate(keys):
      if key.get_value() not in (0.0,0.001):continue
      frame=key.get_time().frame_number.value
      prior_visibility=sorted((time,value) for time,value in visibility_keys if time<=frame)
      assert prior_visibility and prior_visibility[-1][1] is False,(binding.get_name(),'zero scale is visible',frame)
      assert i>0 and keys[i-1].get_interpolation_mode()==u.RichCurveInterpMode.RCIM_CONSTANT,'Do not alter visible interpolation'
      section.modify();key.set_value(0.001)
      walls.append({'name':str(binding.get_name()),'channel':str(channel.get_name()),'frame':frame,'scale_floor':0.001})
assert len(walls)==6,walls
fixed.extend(walls)
a.modify();assert u.EditorAssetLibrary.save_loaded_asset(a,False)
director_path='/Game/SceneDirector/School/DA_Appear_Slime_Event'
director_file=root/'Content'/(director_path.removeprefix('/Game/')+'.uasset');director_backup=backup.parent/director_file.name
if not director_backup.exists():shutil.copy2(director_file,director_backup)
director=u.load_asset(director_path)
result=u.SceneDirectorLibrary.compile_director(director);assert result is not None,result
assert u.EditorAssetLibrary.save_loaded_asset(director,False)
# Compiled subsequences are snapshots. Verify the runtime snapshot, not only the source clip.
checked=0
for track in director.get_editor_property('generated_sequence').get_tracks():
 if isinstance(track,u.MovieSceneSubTrack):
  for section in track.get_sections():
   for binding in section.get_sequence().get_spawnables():
    if str(binding.get_name()).startswith('npc_slime'):
     scale=binding.get_object_template().get_editor_property('root_component').get_editor_property('relative_scale3d')
     assert min(scale.x,scale.y,scale.z)>0,scale
     checked+=1
assert checked==4,checked
for r in json.loads((root/'Saved/SceneEventIntegration/sequences.json').read_text(encoding='utf-8')):
 assert hashlib.sha256((root/'Content'/(r['path'].removeprefix('/Game/')+'.uasset')).read_bytes()).hexdigest()==r['sha256']
(out/'physics-repair.json').write_text(json.dumps(fixed,ensure_ascii=False,indent=2),encoding='utf-8');u.log('SCENE_PHYSICS_REPAIRED 4 spawn templates + 6 hidden wall scale channels')
