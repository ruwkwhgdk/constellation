import unreal as u,json
from pathlib import Path
O=Path(u.Paths.project_dir())/'Saved/S0WetFloor/20261017'
u.EditorLoadingAndSavingUtils.load_map('/Game/Constellation/Worlds/AbandonedSchool/Maps/AbandonedSchool')
rows=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 if isinstance(a,u.PlanarReflection):
  c=a.get_component_by_class(u.PlanarReflectionComponent)
  rows.append(dict(label=a.get_actor_label(),location=str(c.get_world_location()),up=str(c.get_up_vector()),bounds=str(a.get_actor_bounds(False)),settings={k:str(c.get_editor_property(k)) for k in ['visible','hidden_in_game','capture_every_frame','capture_on_movement','primitive_render_mode','hidden_actors','show_only_actors','max_view_distance_override','angle_from_plane_fade_start','angle_from_plane_fade_end','show_flag_settings']}))
(O/'reflection-diagnostic.json').write_text(json.dumps(rows,indent=2))
