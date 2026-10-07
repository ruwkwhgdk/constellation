"""Compare resolved recipe tuning; version IDs and clone-source paths are provenance."""
import copy
import struct

def compare_recipes(before,after):
    def canonical(data):
        data=copy.deepcopy(data)
        data.pop("id",None); data.pop("warnings",None)
        for key in ("actions","patterns"):
            rows=data.get(key,[])
            if key=="actions":
                for row in rows: row.pop("source",None)
            data[key]={row["id"]:{k:v for k,v in row.items() if k!="id"} for row in rows}
        return data
    changes=[]
    def walk(a,b,path):
        if isinstance(a,dict) and isinstance(b,dict):
            for key in sorted(set(a)|set(b)):
                child=path+"."+key if path else key
                if key not in a or key not in b:
                    changes.append({"path":child,"before":a.get(key),"after":b.get(key)})
                else: walk(a[key],b[key],child)
        elif type(a) in (int,float) and type(b) in (int,float) and struct.pack("!f",a)==struct.pack("!f",b):
            return
        elif type(a)!=type(b) or a!=b:
            changes.append({"path":path,"before":a,"after":b})
    walk(canonical(before),canonical(after),"")
    return changes
