"""Local-only combat authoring server; runs approved fixed scripts without a shell."""
import json
import secrets
import subprocess
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from combat_author_model import ROOT,save_version,read_version,versions,command
from combat_tuning_bridge import load_bridge
from combat_recipe import validate_recipe,V2_ACTION_RANGES,ACTION_BOOLEANS,STAT_RANGES,PATTERN_DEFAULTS,ENCOUNTER_DEFAULTS,VFX_KINDS,VFX_DEFAULT_CUE

TOKEN=secrets.token_urlsafe(32)
LOCK=threading.Lock()
JOB={"running":False}
STATIC=ROOT/"tools/combat-author"
def start_job(mode,name):
    args=command(mode,name)
    with LOCK:
        if JOB.get("running"):raise ValueError("현재 검증·제작 작업이 끝난 뒤 실행하세요.")
        JOB.clear();JOB.update(running=True,mode=mode,id=name,started=time.time(),message="실행 중")
    def worker():
        log=ROOT/"Saved/CombatAuthor"/(mode+"-"+name+"-"+str(time.time_ns())+".log")
        log.parent.mkdir(parents=True,exist_ok=True)
        with LOCK:JOB["log"]=str(log)
        try:
            with log.open("w",encoding="utf-8") as stream:
                p=subprocess.Popen(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                # Keep the job locked until its own child exits; never orphan a live creator on timeout.
                code=p.wait()
            with LOCK:JOB.update(running=False,passed=code==0,code=code,message="완료" if code==0 else "실패 — 진단 로그 확인",log=str(log))
        except Exception as e:
            with LOCK:JOB.update(running=False,passed=False,message=str(e),log=str(log))
    threading.Thread(target=worker,daemon=True).start()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,status,data,kind="application/json; charset=utf-8"):
        body=json.dumps(data,ensure_ascii=False).encode() if not isinstance(data,bytes) else data
        self.send_response(status);self.send_header("Content-Type",kind);self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers();self.wfile.write(body)
    def local(self):
        return self.headers.get("Host")==f"127.0.0.1:{self.server.server_port}"
    def do_GET(self):
        if not self.local():return self.send(403,{"error":"Invalid host"})
        route=urlsplit(self.path)
        if route.path in ("/","/app.js","/style.css"):
            filename={"/":"index.html","/app.js":"app.js","/style.css":"style.css"}[route.path]
            kind={"index.html":"text/html; charset=utf-8","app.js":"text/javascript; charset=utf-8","style.css":"text/css; charset=utf-8"}[filename]
            body=(STATIC/filename).read_bytes()
            if filename=="index.html":body=body.replace(b"__TOKEN__",TOKEN.encode())
            return self.send(200,body,kind)
        if self.headers.get("X-Combat-Token")!=TOKEN:return self.send(403,{"error":"Session token required"})
        try:
            query=parse_qs(route.query)
            if route.path=="/api/state":
                with LOCK:job=dict(JOB)
                reports=sorted(p.stem for p in (ROOT/"Saved/CombatTuningReports").glob("*.json"))
                return self.send(200,{"versions":versions(),"job":job,"reports":reports})
            if route.path=="/api/recipe":return self.send(200,read_version(query.get("id",[""])[0]))
            if route.path=="/api/catalog":
                actions=set()
                for row in versions():
                    try:data=read_version(row["file"])
                    except (ValueError,OSError):continue
                    for action in data["actions"]+data.get("player",{}).get("actions",[]):actions.add(action["source"])
                content=ROOT/"Content"
                montages=sorted("/Game/"+str(p.relative_to(content).with_suffix("")).replace("\\","/") for p in content.rglob("AM_*.uasset"))
                niagara=sorted("/Game/"+str(p.relative_to(content).with_suffix("")).replace("\\","/") for p in content.rglob("NS_*.uasset"))
                return self.send(200,{"actions":sorted(actions),"montages":montages,"niagara":niagara})
            if route.path=="/api/schema":return self.send(200,{"actions":V2_ACTION_RANGES,"booleans":ACTION_BOOLEANS,"stats":STAT_RANGES,"patterns":PATTERN_DEFAULTS,"encounter":ENCOUNTER_DEFAULTS,"vfxKinds":VFX_KINDS,"vfxCue":VFX_DEFAULT_CUE})
            if route.path=="/api/log":
                with LOCK:path=JOB.get("log")
                return self.send(200,{"text":Path(path).read_text(encoding="utf-8",errors="replace")[-24000:] if path else "아직 로그 없음"})
            self.send(404,{"error":"Not found"})
        except (ValueError,OSError) as e:self.send(400,{"error":str(e)})
    def do_POST(self):
        if not self.local() or self.headers.get("X-Combat-Token")!=TOKEN:return self.send(403,{"error":"Invalid session"})
        origin=self.headers.get("Origin")
        if origin and origin!=f"http://127.0.0.1:{self.server.server_port}":return self.send(403,{"error":"Invalid origin"})
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=2_000_000:raise ValueError("Invalid document size")
            data=json.loads(self.rfile.read(length))
            if self.path=="/api/validate":
                checked=validate_recipe(data);warnings=checked.pop("warnings");return self.send(200,{"draft":checked,"message":"JSON 검사 통과 — 엔진 검증은 저장 후 실행하세요.","warnings":warnings})
            if self.path=="/api/import-report":
                draft,changes=load_bridge(ROOT,data["base_id"],data["report"],data["new_id"])
                return self.send(200,{"draft":draft,"changes":changes})
            if self.path=="/api/save":
                with LOCK:
                    if JOB.get("running"):raise ValueError("작업 중에는 파일 저장을 기다려 주세요.")
                    path=save_version(data)
                return self.send(200,{"message":"새 버전 파일 저장 완료","path":str(path)})
            if self.path=="/api/job":
                start_job(data["mode"],data["id"]);return self.send(200,{"message":"작업 시작"})
            self.send(404,{"error":"Not found"})
        except (ValueError,OSError,KeyError,TypeError) as e:self.send(400,{"error":str(e)})

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    url=f"http://127.0.0.1:{server.server_port}/"
    folder=ROOT/"Saved/CombatAuthor";folder.mkdir(parents=True,exist_ok=True)
    (folder/"server.json").write_text(json.dumps({"url":url,"token":TOKEN,"pid":__import__("os").getpid()}),encoding="utf-8")
    if "--no-browser" not in __import__("sys").argv:webbrowser.open(url)
    server.serve_forever()
if __name__=="__main__":main()
