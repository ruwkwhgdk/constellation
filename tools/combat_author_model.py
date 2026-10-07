"""Filesystem and subprocess boundary for the local combat authoring application."""
import copy
import json
from pathlib import Path
from combat_recipe import validate_recipe, identifier, load_recipe

ROOT=Path(__file__).resolve().parents[1]
def recipe_path(name,root=ROOT):
    identifier(name,"id")
    return root/"CombatRecipes"/(name+".json")

def save_version(data,root=ROOT):
    checked=validate_recipe(data);checked.pop("warnings",None)
    path=recipe_path(checked["id"],root);path.parent.mkdir(parents=True,exist_ok=True)
    if (root/"Content/Constellation/Review/CombatRecipes"/checked["id"]).exists():
        raise ValueError("이미 제작된 버전입니다. 새 버전 이름을 사용하세요.")
    with path.open("x",encoding="utf-8") as stream:json.dump(checked,stream,ensure_ascii=False,indent=2)
    return path

def read_version(name,root=ROOT):
    path=recipe_path(name,root)
    resolved=path.with_name(name+".resolved.json");manifest=path.with_name(name+".manifest.json")
    if manifest.is_file() and not resolved.is_file():raise ValueError("제작 스냅샷 파일이 없습니다: "+name)
    if resolved.is_file() and manifest.is_file():
        import hashlib
        meta=json.loads(manifest.read_text(encoding="utf-8"))
        if not meta.get("complete") or hashlib.sha256(resolved.read_bytes()).hexdigest()!=meta.get("recipe_sha256"):
            raise ValueError("제작 스냅샷 원본 확인에 실패했습니다: "+name)
        path=resolved
    data=load_recipe(path);data.pop("warnings",None);return data

def playable(name,root=ROOT):
    if not (root/"Content/Constellation/Review/CombatRecipes"/name/"L_Preview.umap").is_file():return False
    try:
        data=read_version(name,root)
        if data["schema_version"]==2:
            manifest=root/"CombatRecipes"/(name+".manifest.json")
            return manifest.is_file() and bool(json.loads(manifest.read_text(encoding="utf-8")).get("complete"))
        return True
    except (ValueError,OSError):return False

def versions(root=ROOT):
    result=[]
    for path in sorted((root/"CombatRecipes").glob("*.json")):
        if "." in path.stem:continue
        try:
            data=load_recipe(path)
            result.append({"id":data["id"],"file":path.stem,"schema":data["schema_version"],
                "playable":playable(data["id"],root)})
        except (ValueError,OSError):continue
    return result

def command(mode,name,root=ROOT):
    identifier(name,"id")
    if mode not in ("preview","build","play"):raise ValueError("Unknown operation")
    if mode=="play":
        if not playable(name,root):
            raise ValueError("먼저 이 버전을 제작하세요.")
        return ["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(root/"tools/play-combat-recipe.ps1"),"-Id",name]
    read_version(name,root)
    args=["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",str(root/"tools/build-combat-recipe.ps1"),"-Recipe",str(recipe_path(name,root))]
    if mode=="build":args.append("-Apply")
    return args
