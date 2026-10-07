import unreal as u
from pathlib import Path
out=Path(u.Paths.project_saved_dir())/'StatueDirector'
for p in u.EditorAssetLibrary.list_assets('/Game/Constellation/Gameplay/Sequences/LevelSequences',recursive=True):
 if 'Checkpoint' not in p: continue
 a=u.load_asset(p); lines=[]
 try:
  bp=u.SceneDirectorLibrary.get_sequence_director_blueprint(a); (out/(a.get_name()+'-events.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(bp),encoding='utf-8')
 except Exception as e: lines.append('BP '+str(e))
 for b in a.get_bindings():
  lines.append('BIND '+b.get_name())
  try: lines.append('TEMPLATE '+str(b.get_object_template()))
  except: pass
  for t in b.get_tracks():
   lines.append('TRACK '+str(t))
   if isinstance(t,u.MovieScenePropertyTrack): lines.append('PROPERTY '+str(t.get_property_path()))
   for s in t.get_sections():
    lines.append('SECTION '+str(s))
    if isinstance(s,u.MovieSceneSkeletalAnimationSection): lines.append('ANIMATION '+str(s.get_editor_property('params')))
    try:
     for c in s.get_all_channels():
      lines.append('CHANNEL '+str(c.channel_name))
      try: lines.append('DEFAULT '+str(c.get_default()))
      except: pass
      for k in c.get_keys():
       v=k.get_value(); lines.append('KEY '+str(k.get_time())+' VALUE '+str(v))
       if isinstance(v,u.MovieSceneEvent):
        for name in ['payload_variables','weak_endpoint']:
         try:
          data=v.get_editor_property(name); lines.append(name+' '+str({str(kk): vv.get_editor_property('value') for kk,vv in data.items()} if name=='payload_variables' else data))
         except Exception as e: lines.append(str(e))
    except Exception as e: lines.append('CHANNELERR '+str(e))
 (out/(a.get_name()+'-detail.txt')).write_text('\n'.join(lines),encoding='utf-8')

for p in ['/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData']:
 a=u.load_asset(p)
 if a: (out/'dialogue.json').write_text(u.DataTableFunctionLibrary.export_data_table_to_json_string(a),encoding='utf-8')
