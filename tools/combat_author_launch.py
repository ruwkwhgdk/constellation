"""Reuse an owned authoring server or start a hidden one, then open the browser."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
import webbrowser
ROOT=Path(__file__).resolve().parents[1]
def existing():
    try:
        config=json.loads((ROOT/"Saved/CombatAuthor/server.json").read_text(encoding="utf-8"))
        parsed=urlsplit(config["url"])
        if parsed.scheme!="http" or parsed.hostname!="127.0.0.1" or parsed.path!="/":return None
        request=Request(config["url"]+"api/state",headers={"X-Combat-Token":config["token"]})
        with urlopen(request,timeout=1) as response:
            if response.status==200:return config["url"]
    except (OSError,ValueError,KeyError):return None
url=existing()
if not url:
    subprocess.Popen([sys.executable,str(ROOT/"tools/combat_author_server.py"),"--no-browser"],cwd=ROOT,
        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    for _ in range(50):
        time.sleep(.2);url=existing()
        if url:break
if not url:raise RuntimeError("Combat authoring server failed to start")
webbrowser.open(url)
