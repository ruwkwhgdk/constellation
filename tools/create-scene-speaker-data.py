"""Create the shared speaker master without overwriting designer edits."""
import unreal as u
import json, traceback
from pathlib import Path
report = {'success': False}
out = Path(u.Paths.project_dir()).resolve() / 'Saved/SceneSpeakerData'
out.mkdir(parents=True, exist_ok=True)
try:
    package = '/Game/Constellation/Gameplay/Sequences/Data/DT_SpeakerData'
    table = u.load_asset(package)
    created = table is None
    if created:
        factory = u.DataTableFactory()
        factory.set_editor_property('struct', u.load_object(None, '/Script/SceneDirectorRuntime.DirectorSpeakerRow'))
        table = u.AssetToolsHelpers.get_asset_tools().create_asset('DT_SpeakerData', package.rsplit('/', 1)[0], u.DataTable, factory)
        assert table, 'Speaker DataTable creation failed'
        rows = [{'Name': key, 'DisplayName': name} for key, name in [
            ('Heroine', '주인공'), ('Companion', '동료'), ('Girl_Unknown', '???'), ('Girl', '소녀')]]
        assert u.DataTableFunctionLibrary.fill_data_table_from_json_string(table, json.dumps(rows, ensure_ascii=False))
        assert u.EditorAssetLibrary.save_loaded_asset(table, False)
    names = [str(n) for n in u.DataTableFunctionLibrary.get_data_table_row_names(table)]
    assert names, 'Speaker table has no rows'
    report.update(success=True, asset=package, created=created, rows=names)
except Exception:
    report['error'] = traceback.format_exc()
(out / 'asset-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
u.log('SCENE_SPEAKER_DATA ' + json.dumps(report, ensure_ascii=False))
u.SystemLibrary.quit_editor()
