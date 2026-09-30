"""Resolve package paths in preserved historical reports without rewriting evidence."""
import json
import re
from pathlib import Path

_root=Path(__file__).resolve().parents[2]
_moves=json.loads((_root/'docs/ResourceOrganization/package_paths.json').read_text(encoding='utf-8'))
for _old,_new in list(_moves.items()):
    _oldname,_newname=_old.rsplit('/',1)[-1],_new.rsplit('/',1)[-1]
    if _oldname!=_newname:
        for _suffix in ('','_C'):
            _moves[_old+'.'+_oldname+_suffix]=_new+'.'+_newname+_suffix
_pattern=re.compile('(?:'+'|'.join(re.escape(k) for k in sorted(_moves,key=len,reverse=True))+r')(?=$|[/\.\s\x00\x22\x27\),;:\]\}])')

def resolve(value):
    return _pattern.sub(lambda m:_moves[m.group(0)],value)

def remap_data(value):
    if isinstance(value,str):return resolve(value)
    if isinstance(value,list):return [remap_data(x) for x in value]
    if isinstance(value,dict):return {resolve(k):remap_data(v) for k,v in value.items()}
    return value

def loads(*args,**kwargs):
    return remap_data(json.loads(*args,**kwargs))

def load(*args,**kwargs):
    return remap_data(json.load(*args,**kwargs))
