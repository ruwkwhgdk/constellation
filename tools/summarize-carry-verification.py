"""Collect evidence for the gameplay implementation handoff."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]; out=root/'Saved/CarryReview'
def read(name): return json.loads((out/name).read_text(encoding='utf-8-sig'))
tests=read('final-tests/index.json'); play=read('play-verification.json'); reload=read('reload-verification.json')
assert tests['failed']==0 and tests['notRun']==0
assert 'error' not in play and all(x['passed'] for x in play['checks'])
assert all('errors=0' in reload[x] and 'warnings=0' in reload[x] for x in ('input','overlay'))
build=(out/'build-release-step.log').read_text(encoding='utf-8-sig')
assert 'Result: Succeeded' in build
review30=read('play-contact-30fps.json')
summary={
    'status':'gameplay implementation and first animation review handoff',
    'build':'build-release-step.log: Succeeded',
    'standalone_math':'tools/test-carry.cmd: 0 failures',
    'project_automation':{x:tests[x] for x in ('succeeded','succeededWithWarnings','failed','notRun')},
    'blueprint_reload':reload,
    'pie_60fps':{'passed':sum(x['passed'] for x in play['checks']),'failed':0,'first_contact_error_cm':play['first_contact']['error_cm'],'hand_contact_error_cm':play['hand_contact_error_cm']},
    'trajectory_30fps':{'first_contact_error_cm':review30['first_contact']['error_cm'],'note':'trajectory passed; this earlier run stopped later at a corrected Python UI-library name'},
    'animation_source_foot_drift':read('source-motion-metrics.json'),
    'retired_draft_cleanup':read('draft-cleanup.json'),
    'review_map':'/Game/Constellation/Review/Carry/Maps/L_Carry_Review',
    'review_media':['carry-play-review.gif','play-holding.png','play-aiming.png','play-too-heavy.png'],
    'remaining_visual_qa':['multi-angle transition hand contact','garment/object interference for varied object sizes','walking foot slip and final motion polish'],
    'limits':['single rigid static-mesh root with simple collision','bounding-box prediction of first contact, not final resting position','changing physics step during flight can change prediction error','broader death/cinematic/focus-loss and irregular-object scenarios are not all exercised in PIE'],
}
(out/'verification.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'native_tests':tests['succeeded']+tests['succeededWithWarnings'],'pie_checks':len(play['checks']),'first_contact_error_cm':play['first_contact']['error_cm']},ensure_ascii=False))
