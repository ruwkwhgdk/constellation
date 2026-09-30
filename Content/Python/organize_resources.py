"""Execute a reviewed manifest batch with Unreal rename APIs and import-source preservation."""
import datetime,json,os,traceback
from pathlib import Path
import unreal as u

root=Path(u.Paths.project_dir()).resolve();out=root/'Saved/ResourceOrganization/20260930'
assert (out/'recovery.json').exists(),'Missing recovery snapshot'
manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
baseline=json.loads((out/'registry.json').read_text(encoding='utf-8'))['packages']
job=json.loads((out/'job.json').read_text(encoding='utf-8'))
rows=[x for x in manifest if x['old']!=x['new'] and (x['old'] in job['packages'] if 'packages' in job else x['batch']==job['batch'])]
r=u.AssetRegistryHelpers.get_asset_registry();r.search_all_assets(True)
tool=u.AssetToolsHelpers.get_asset_tools();E=u.EditorAssetLibrary
C=u.get_editor_subsystem(u.CollectionManagerSubsystem)
container=u.CollectionContainerSource()
collection_name='ResourceOrganization_20260930'
if not C.collection_exists(container,collection_name,u.CollectionShareType.LOCAL):
    collection=C.create_collection(container,collection_name,u.CollectionShareType.LOCAL)
    if isinstance(collection,tuple):collection=collection[-1]
    assert collection,'Cannot create migration reference collection'
else:collection=u.Collection(container='Game',name=collection_name,share_type=u.CollectionShareType.LOCAL)
# AssetRenameManager preserves redirectors for collection members, even when dependency gathering is deferred.
members=C.get_assets_in_collection(collection)
assert members is not None,'Cannot inspect migration collection'
existing={str(a.package_name) for a in members}
additions=[u.SoftObjectPath(row['old']+'.'+row['old'].rsplit('/',1)[-1]) for row in rows if row['old'] not in existing]
if additions:assert C.add_assets_to_collection(collection,additions)
report_path=out/('move_'+job['id']+'.json')
report={'job':job,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'moved':[],'failed':[]}
def write():report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
def get_data(path):
    assets=r.get_assets_by_package_name(path)
    return assets[0] if assets else u.AssetData()
def already_moved(row):
    a=get_data(row['new'])
    return a.is_valid() and str(a.asset_class_path.asset_name)!='ObjectRedirector'

def baseline_sources(row):
    raw=baseline[row['old']]['tags'].get('AssetImportData')
    if not raw:return []
    entries=json.loads(raw)
    result=[]
    for entry in entries:
        path=entry['RelativeFilename']
        candidate=((root/'Content'/row['old'][6:]).parent/path).resolve()
        result.append(str(candidate) if candidate.is_file() else str(u.Paths.convert_relative_path_to_full(path)))
    return result
try:
    for start in range(0,len(rows),10):
        r.scan_paths_synchronous(['/Game'],force_rescan=True)
        chunk=rows[start:start+10];objects=[];renames=[];active=[];sources={}
        for row in chunk:
            if already_moved(row):
                old=get_data(row['old'])
                assert not old.is_valid() or str(old.asset_class_path.asset_name)=='ObjectRedirector','Both paths contain assets'
                obj=get_data(row['new']).get_asset();paths=baseline_sources(row)
                if paths and str(get_data(row['new']).asset_class_path.asset_name) in ['StaticMesh','SkeletalMesh','Texture2D','AnimSequence','SoundWave']:
                    imp=obj.get_editor_property('asset_import_data')
                    for i,path in enumerate(paths):imp.scripted_add_filename(path,i,'')
                    assert E.save_loaded_asset(obj,only_if_is_dirty=False)
                else:paths=[]
                report['moved'].append({'old':row['old'],'new':row['new'],'resumed':True,'source_files':paths});continue
            a=get_data(row['old']);assert a.is_valid(),row
            obj=a.get_asset();assert obj and obj.get_outermost().get_name()==row['old'],row
            if str(a.asset_class_path.asset_name) in ['StaticMesh','SkeletalMesh','Texture2D','AnimSequence','SoundWave']:
                try:
                    imp=obj.get_editor_property('asset_import_data')
                    if imp:sources[row['old']]=[str(p) for p in imp.extract_filenames()]
                except Exception:pass
            folder,name=row['new'].rsplit('/',1)
            renames.append(u.AssetRenameData(obj,folder,name));objects.append(obj);active.append(row)
        if renames:
            report['pending']=[dict(row,source_files=sources.get(row['old'],[])) for row in active];write()
            ok=tool.rename_assets(renames)
            assert ok,'Rename failed; inspect redirectors before resuming'
            for row,obj in zip(active,objects):
                assert obj.get_outermost().get_name()==row['new'],row
                if row['old'] in sources:
                    imp=obj.get_editor_property('asset_import_data')
                    for i,path in enumerate(sources[row['old']]):imp.scripted_add_filename(path,i,'')
                    assert [os.path.normcase(os.path.abspath(str(p))) for p in imp.extract_filenames()]==[os.path.normcase(os.path.abspath(p)) for p in sources[row['old']]],row
                assert E.save_loaded_asset(obj,only_if_is_dirty=False),'Save failed: '+row['new']
                report['moved'].append({'old':row['old'],'new':row['new'],'source_files':sources.get(row['old'],[])})
            report.pop('pending',None)
        write();u.log('RESOURCE_ORGANIZATION_PROGRESS '+job['id']+' '+str(len(report['moved']))+'/'+str(len(rows)))
        objects.clear();renames.clear();active.clear();u.SystemLibrary.collect_garbage()
    report['success']=True
except Exception:
    report['success']=False;report['failed'].append(traceback.format_exc());write();raise
finally:
    report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write()
u.log('RESOURCE_ORGANIZATION_BATCH_OK '+job['id'])
