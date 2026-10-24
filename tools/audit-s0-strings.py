import unreal as u
from pathlib import Path
R=Path(u.Paths.project_dir())/'Saved/S0StringTable';R.mkdir(exist_ok=True)
d=u.load_asset('/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData');assert u.DataTableFunctionLibrary.export_data_table_to_json_file(d,str(R/'sequence-data.json'))
(R/'api.txt').write_text('\n'.join(x for x in dir(u.DataTableFunctionLibrary) if 'row' in x or 'json' in x),encoding='utf8')
