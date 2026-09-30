"""Plan a reversible asset relocation. This module never edits Unreal packages."""
import collections,csv,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Saved/ResourceOrganization/20260930'
PREFIX='/Game/Constellation/'
VENDORS=['/Game/LuosCaves/','/Game/ModulAbandJPSchool/','/Game/Landscape/StylizedGrassByMayu/','/Game/Landscape/Stylized_PBR_Nature/','/Game/Resources/VFX/FXVarietyPack/','/Game/Resources/VFX/LightShaftGenie/','/Game/Resources/VFX/SwordTrailVFX_Resources/']

def destination(p,classes):
    if p.startswith(tuple(VENDORS)):return p,'vendor','External pack preserved'
    if p.startswith(('/Game/__','/Game/Levels/_GENERATED/')):return p,'managed','Engine-owned package'
    if 'ObjectRedirector' in classes:return p,'redirector','Resolve via engine Fixup after moves'
    if p.startswith(PREFIX):return p,'organized','Already organized'
    name=p.rsplit('/',1)[1]
    if p=='/Game/Levels/AbandonedSchool_BuiltData':return PREFIX+'Worlds/AbandonedSchool/Maps/'+name,'maps','Map build data moves with its owner'
    if 'World' in classes:
        worlds={'L_Title':'Title','L_StartIsland':'StartIsland','AbandonedSchool':'AbandonedSchool','L_Stairwell_PlayScale2':'Stairwell','L_OvergrownHall_TripoFull':'OvergrownHall'}
        if name in worlds:return PREFIX+'Worlds/'+worlds[name]+'/Maps/'+name,'maps','Playable map'
        review='Heroine' if 'heroine' in p.lower() else 'Stairwell' if 'Stairwell' in p else 'General'
        return PREFIX+'Review/'+review+'/Maps/'+name,'maps','Maintained review map'
    def put(old,new,batch='environment'):
        return (PREFIX+new+p[len(old):],batch,'Project-owned content') if p.startswith(old) else None
    rules=[('/Game/Environment/StairwellModular/','Environments/Stairwell/'),('/Game/Environment/OvergrownHall/','Environments/OvergrownHall/'),('/Game/Environment/SubwayEntrance/','Environments/SubwayEntrance/'),('/Game/Environment/OldKoreanBuildingA/','Environments/KoreanBuildings/BuildingA/'),('/Game/Environment/OldKoreanBuildingB/','Environments/KoreanBuildings/BuildingB/'),('/Game/Resources/Environments/Props/AbandonedSchool/','Environments/School/Props/'),('/Game/Resources/Environments/Props/StartIsland/','Environments/StartIsland/Props/'),('/Game/Resources/Environments/Props/Common/','Environments/Shared/Props/'),('/Game/Resources/Environments/','Environments/Shared/'),('/Game/Landscape/Foilage/','Environments/Shared/Foliage/'),('/Game/Landscape/','Environments/Shared/Landscape/')]
    for a,b in rules:
        result=put(a,b)
        if result:return result
    if p.startswith('/Game/Art/'):
        sub=p[len('/Game/Art/'):];zone=sub.split('/')[0]
        cave=any(x in zone for x in ['Cave','Slime','Hollow','Mushroom','Dump','Dustchute'])
        return PREFIX+'Environments/'+('Cave' if cave else 'School')+'/Sets/'+sub,'environment','Original authored regional set'
    rules=[('/Game/Resources/Characters/PC/player_heroine_new/','Characters/Heroine/Refined/'),('/Game/Resources/Characters/PC/Player_Heroine/','Characters/Heroine/Base/'),('/Game/Resources/Characters/CommonAnimation/','Characters/Shared/Animations/'),('/Game/Resources/Characters/Monster/','Characters/Enemies/'),('/Game/Resources/Characters/NPC/','Characters/NPC/'),('/Game/Resources/Weapons/','Characters/Shared/Equipment/'),('/Game/Blueprints/Character/PC/','Characters/Heroine/Blueprints/'),('/Game/Blueprints/Character/Monster/','Characters/Enemies/Blueprints/'),('/Game/Blueprints/Character/NPC/','Characters/NPC/Blueprints/'),('/Game/Blueprints/Widget/','UI/Widgets/'),('/Game/Resources/UI/','UI/Art/'),('/Game/Resources/Fonts/','UI/Fonts/'),('/Game/Resources/VFX/Custom/','VFX/'),('/Game/Resources/Common/','MaterialLibrary/'),('/Game/Inputs/','Input/')]
    for a,b in rules:
        result=put(a,b,'character_ui')
        if result:return result
    rules=[('/Game/Data/Quests/','Gameplay/Quests/Data/'),('/Game/Resources/LevelSequence/','Gameplay/Sequences/LevelSequences/'),('/Game/Data/','Gameplay/Sequences/Data/'),('/Game/Blueprints/System/Data/','Gameplay/Sequences/Data/'),('/Game/PCG/','Procedural/')]
    for a,b in rules:
        result=put(a,b,'gameplay')
        if result:return result
    if p.startswith('/Game/Blueprints/Actor/'):
        if '/AbandonedSchool/' in p:return PREFIX+'Environments/School/Blueprints/'+name,'environment','School-specific actors'
        if '/StartIsland/' in p:return PREFIX+'Environments/StartIsland/Blueprints/'+name,'environment','Island-specific actors'
        return PREFIX+'Gameplay/Interaction/Actors/'+name,'gameplay','Shared interactive actors'
    if p.startswith('/Game/Blueprints/'):
        lower=name.lower()
        domain='Combat' if any(x in lower for x in ['battle','attack','damage','combo','dodge','stats','monster']) else 'Quests' if 'quest' in lower else 'Sequences' if any(x in lower for x in ['sequence','choice','dialogue']) else 'Interaction' if any(x in lower for x in ['interact','breakable','push','switch','ability']) else None
        sub='Interfaces/' if '/Interface/' in p else 'Components/' if '/ActorComponent/' in p else 'Types/' if '/Enum/' in p else ''
        if name=='FBXPipelineCharacter':return PREFIX+'Editor/Import/'+name,'gameplay','Character import pipeline'
        if name=='BP_HUD':return PREFIX+'UI/Blueprints/'+name,'character_ui','HUD coordinator'
        return PREFIX+('Gameplay/'+domain+'/' if domain else 'Core/')+sub+name,'gameplay','Gameplay ownership'
    return p,'retained','Unclassified: retain until provenance is established'

def check_destinations(rows):
    seen={}
    for r in rows:
        key=r['new'].casefold()
        if key in seen and seen[key]!=r['old']:raise ValueError('Destination collision: '+str((seen[key],r)))
        seen[key]=r['old']

def replace_paths(text,mapping):
    # Match the longest complete directory/package prefix; preserve .Object_C suffixes.
    mapping=dict(mapping)
    for old,new in list(mapping.items()):
        oldname,newname=old.rsplit('/',1)[-1],new.rsplit('/',1)[-1]
        if oldname!=newname and '.' not in old:
            for suffix in ('','_C'):
                mapping[old+'.'+oldname+suffix]=new+'.'+newname+suffix
    keys=sorted(mapping,key=len,reverse=True)
    if not keys:return text
    regex=re.compile('(?:'+'|'.join(re.escape(k.rstrip('/')) for k in keys)+r')(?=$|[/\.\s\x00\x22\x27\),;:\]\}])')
    lookup={k.rstrip('/'):v.rstrip('/') for k,v in mapping.items()}
    return regex.sub(lambda m:lookup[m.group(0)],text)

def resolved_mapping(rows,baseline):
    mapping={r['old']:r['new'] for r in rows if r['old']!=r['new']}
    for old,data in baseline.items():
        if 'ObjectRedirector' not in data['classes']:continue
        targets=[p for p in data['dependencies'] if p.startswith('/Game/')]
        if len(targets)==1:mapping[old]=targets[0]
    for old in list(mapping):
        seen={old};target=mapping[old]
        while target in mapping:
            if target in seen:raise ValueError('Redirect cycle: '+old)
            seen.add(target);target=mapping[target]
        mapping[old]=target
    return mapping

def digest(f):
    h=hashlib.sha256()
    with f.open('rb') as s:
        for chunk in iter(lambda:s.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def create_plan():
    data=json.loads((OUT/'registry.json').read_text(encoding='utf-8'))['packages']
    rows=[]
    for p,v in sorted(data.items()):
        new,batch,why=destination(p,v['classes'])
        if not v['indexed_asset']:new,batch,why=p,'managed','Registry has no browsable asset'
        rows.append({'old':p,'new':new,'batch':batch,'reason':why,'classes':';'.join(v['classes']),'referencers':';'.join(v['referencers']),'source_metadata':json.dumps(v['tags'],ensure_ascii=False)})
    check_destinations(rows)
    for row in rows:
        if row['old']!=row['new']:assert row['new'] not in data,row
    (OUT/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    dest=ROOT/'docs/ResourceOrganization';dest.mkdir(parents=True,exist_ok=True)
    with (dest/'move_manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(collections.Counter(r['batch'] for r in rows))
    print('MOVE',sum(r['old']!=r['new'] for r in rows),'RETAIN',sum(r['old']==r['new'] for r in rows))

def snapshot():
    assert not (OUT/'recovery.json').exists(),'Snapshot exists; never replace baseline'
    git=['git','-c','safe.directory='+ROOT.as_posix()]
    head=subprocess.check_output(git+['rev-parse','HEAD'],cwd=ROOT).decode().strip()
    raw=subprocess.check_output(git+['ls-tree','-r','-z','HEAD'],cwd=ROOT)
    blobs={}
    for entry in raw.split(b'\0'):
        if entry:
            meta,path=entry.split(b'\t',1);mode,kind,oid=meta.split()
            if kind==b'blob':blobs[path.decode()]=oid.decode()
    files=[p for base in ['Content','Config','Source','tools','Tests','ArtSource'] for p in (ROOT/base).rglob('*') if p.is_file() and (base!='ArtSource' or p.suffix.lower() in {'.py','.ps1','.md','.json'})]
    paths=[p.relative_to(ROOT).as_posix() for p in files]
    ids=list(dict.fromkeys(blobs[p] for p in paths if p in blobs))
    raw=subprocess.run(git+['cat-file','--batch'],cwd=ROOT,input=('\n'.join(ids)+'\n').encode(),stdout=subprocess.PIPE,check=True).stdout
    cursor=0;pointers={}
    for oid in ids:
        end=raw.index(b'\n',cursor);header=raw[cursor:end].split();size=int(header[2]);cursor=end+1;body=raw[cursor:cursor+size];cursor+=size+1
        if body.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            pointers[oid]=body.decode().split('oid sha256:')[1].splitlines()[0]
    records=[];copied=0
    for f,path in zip(files,paths):
        sha=digest(f);oid=pointers.get(blobs.get(path));lfs=ROOT/'.git/lfs/objects'/sha[:2]/sha[2:4]/sha
        if oid==sha and lfs.exists() and digest(lfs)==sha:source=lfs.relative_to(ROOT).as_posix()
        else:
            b=OUT/'recovery_files'/path;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,b)
            assert digest(b)==sha
            source=b.relative_to(ROOT).as_posix();copied+=f.stat().st_size
        records.append({'path':path,'sha256':sha,'bytes':f.stat().st_size,'mtime_ns':f.stat().st_mtime_ns,'recovery':source})
    (OUT/'recovery.json').write_text(json.dumps({'head':head,'files':records,'copied_bytes':copied},indent=2),encoding='utf-8')
    print('SNAPSHOT',len(records),'files; actual backup MiB',copied/1024**2)

if __name__=='__main__':
    {'plan':create_plan,'snapshot':snapshot}[sys.argv[1]]()
