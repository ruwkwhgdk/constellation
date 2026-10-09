import unreal as u
from pathlib import Path
import shutil,json
root=Path(u.Paths.project_dir());source=root/'ArtSource/UI/AbilityAcquisition/Unreal';out=root/'Saved/AbilityAcquisition';out.mkdir(exist_ok=True)
folder='/Game/Constellation/UI/AbilityAcquisition';lib=u.EditorAssetLibrary;lib.make_directory(folder)
assets={}
for file in sorted(source.iterdir()):
 if file.suffix not in ['.png','.wav']:continue
 task=u.AssetImportTask();task.filename=str(file);task.destination_path=folder;task.destination_name='T_'+file.stem if file.suffix=='.png' else 'S_'+file.stem;task.automated=True;task.replace_existing=True;task.save=False
 u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);asset=u.load_asset(folder+'/'+task.destination_name);assert asset,file
 if file.suffix=='.png':
  asset.set_editor_property('lod_group',u.TextureGroup.TEXTUREGROUP_UI);asset.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_EDITOR_ICON);asset.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_NO_MIPMAPS);asset.set_editor_property('srgb',True);asset.set_editor_property('never_stream',True)
 assert lib.save_loaded_asset(asset,False);assets[file.stem]=asset
art=u.load_asset(folder+'/DA_AbilityAcquisition')
if not art:
 factory=u.DataAssetFactory();factory.set_editor_property('data_asset_class',u.AbilityAcquisitionArt.static_class());art=u.AssetToolsHelpers.get_asset_tools().create_asset('DA_AbilityAcquisition',folder,u.AbilityAcquisitionArt.static_class(),factory)
art.set_editor_property('background',assets['Background']);art.set_editor_property('emblem',assets['Emblem'])
for prop,prefix,n in [('dormant','Dormant',7),('stars','Star',7),('new_stars','New',7),('lines','Line',6),('lit_lines','LitLine',6)]:art.set_editor_property(prop,[assets[prefix+str(i)] for i in range(n)])
art.set_editor_property('descriptions',u.load_asset('/Game/Constellation/Gameplay/Sequences/Data/DT_SequenceStringData'))
# Engine composite font correctly maps Greek and provides Korean fallback.
art.set_editor_property('title_font',None)
art.set_editor_property('sounds',[assets[n] for n in ['Resonance','EmblemChime','StarChime','Dismiss']]);assert lib.save_loaded_asset(art,False)
pkg='Constellation/Gameplay/Interaction/Components/Ac_Ability';file=root/'Content'/(pkg+'.uasset');backup=out/'Ac_Ability.before-acquisition.uasset'
if not backup.exists():shutil.copy2(file,backup)
# UE Python maps bool + one output to str on success and None on failure.
bp=u.load_asset('/Game/'+pkg);result=u.AbilityAcquisitionEditorLibrary.install_acquisition_hooks(bp);u.log(str(result));assert result is not None
export=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp);assert export.count('NodeComment="AbilityAcquisition.BeforeUnlock.')==3
assert lib.save_loaded_asset(bp,False)
(out/'Ac_Ability.installed.txt').write_text(export,encoding='utf8')
assert u.AbilityAcquisitionEditorLibrary.install_acquisition_hooks(bp) is not None;assert u.ResourceRecoveryLibrary.export_blueprint_graphs(bp).count('NodeComment="AbilityAcquisition.BeforeUnlock.')==3
(out/'installed.json').write_text(json.dumps({'art':art.get_path_name(),'assets':len(assets),'hooks':3,'idempotent':True},indent=2),encoding='utf8')
u.log('ABILITY_ACQUISITION_INSTALLED')
