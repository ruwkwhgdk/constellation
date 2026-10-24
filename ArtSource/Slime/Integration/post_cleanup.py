import unreal as u,json
from pathlib import Path
P=Path(__file__).resolve().parent
reg=u.AssetRegistryHelpers.get_asset_registry()
reg.scan_paths_synchronous(['/Game/Constellation/Characters/Enemies/Slime_Normal','/Game/Constellation/Characters/Enemies/Slime_Liquid'],True)
exec(compile((P/'verify_saved.py').read_text(),str(P/'verify_saved.py'),'exec'),{'__file__':str(P/'verify_saved.py'),'__name__':'__main__'})
old='/Game/Constellation/Characters/Enemies/Slime_Normal'
removed=['SKM_Slime_Normal','SM_Slime_Normal','SKM_Slime_Normal_CtrlRig','MI_Slime_Normal','MI_Slime_Yellow','T_Slime_Normal','T_Slime_Yellow','Animation/AM_Slime_Idle']
remaining=json.loads((P/'remaining-old-references.json').read_text())
for name in removed:
 assert not u.EditorAssetLibrary.does_asset_exist(old+'/'+name),name
 if old+'/'+name in remaining:assert not remaining[old+'/'+name],(name,remaining[old+'/'+name])
assert u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Liquid/SKM_Slime_Liquid')
assert u.load_asset('/Game/Constellation/Characters/Enemies/Slime_Liquid/SM_Slime_Liquid')
report={'success':True,'removed_packages':[old+'/'+n for n in removed],'references':remaining,'shared_skeleton_retained':old+'/SK_Slime_Normal','physical_material_retained':old+'/PHM_Slime'}
(P/'post-cleanup-verification.json').write_text(json.dumps(report,indent=2))
cleanup=json.loads((P/'cleanup-report.json').read_text());cleanup['deleted']=report['removed_packages'];cleanup['remaining']=remaining;cleanup['success']=True
cleanup['redirector_package_cleanup']='Engine deletion succeeded but retained two orphan files; zero references and ObjectRedirector type confirmed, then exact files removed with native PowerShell.'
(P/'cleanup-report.json').write_text(json.dumps(cleanup,indent=2))
