"""Bounded, local editor job queue for this asset integration only."""
import unreal as u,time,json,traceback
from pathlib import Path
P=Path(__file__).resolve().parent
u.EditorPythonScripting.set_keep_python_script_alive(True)
started=time.monotonic()
seen=None
def tick(dt):
 global seen
 if time.monotonic()-started>7200:
  u.unregister_slate_post_tick_callback(handle);u.SystemLibrary.quit_editor();return
 q=P/'request.json'
 if not q.exists():return
 request=json.loads(q.read_text(encoding='utf8'))
 if request['id']==seen:return
 seen=request['id']
 try:
  script=(P/request['script']).resolve()
  assert script.is_relative_to(P)
  scope={'__file__':str(script),'__name__':'__main__'}
  exec(compile(script.read_text(encoding='utf8'),str(script),'exec'),scope)
  result={'id':seen,'success':True}
 except Exception:result={'id':seen,'success':False,'error':traceback.format_exc()}
 (P/'response.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 u.log('SLIME_JOB '+json.dumps(result))
handle=u.register_slate_post_tick_callback(tick)
(P/'session-ready.json').write_text(json.dumps({'ready':True}))
