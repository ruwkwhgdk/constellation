import unreal as u
from pathlib import Path
out=Path(u.Paths.project_saved_dir())/'StatueDirector'; out.mkdir(exist_ok=True)
paths=['/Game/Constellation/Environments/School/Blueprints/BP_School_Girl_Statue','/Game/Constellation/Gameplay/Sequences/BP_SequenceManager','/Game/Constellation/Gameplay/Sequences/Components/Ac_SequencePlayer']
for p in paths:
 a=u.load_asset(p)
 if a: (out/(a.get_name()+'.txt')).write_text(u.ResourceRecoveryLibrary.export_blueprint_graphs(a),encoding='utf-8')
for p in u.EditorAssetLibrary.list_assets('/Game/Constellation/Gameplay/Sequences/LevelSequences',recursive=True):
 a=u.load_asset(p)
 if isinstance(a,u.LevelSequence):
  lines=[str(a),str(a.get_playback_start()),str(a.get_playback_end()),str(a.get_display_rate())]
  for b in a.get_bindings():
   lines.append('BIND '+str(b.get_name())+' '+str(b.get_id()))
   for t in b.get_tracks():
    lines.append(' TRACK '+t.get_class().get_name())
    for s in t.get_sections():
     lines.append('  '+s.get_class().get_name()+' '+str(s.get_start_frame() if s.has_start_frame() else 'open')+' '+str(s.get_end_frame() if s.has_end_frame() else 'open'))
  for t in a.get_tracks(): lines.append('MASTER '+t.get_class().get_name())
  (out/(a.get_name()+'.txt')).write_text('\n'.join(lines),encoding='utf-8')
u.log('STATUE_AUDIT_DONE')
