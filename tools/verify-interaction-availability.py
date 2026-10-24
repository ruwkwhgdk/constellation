"""Reload saved actors and verify the availability component/input graph."""
import json
from pathlib import Path
import unreal as u
root=Path(u.Paths.project_dir()).resolve()
out=root/'Saved/InteractionAvailabilityReview'
installed=json.loads((out/'installed.json').read_text(encoding='utf-8'))
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
results=[]
for path in installed['actors']:
    cls=u.EditorAssetLibrary.load_blueprint_class(path)
    actor=actors.spawn_actor_from_class(cls,u.Vector(0,0,-100000))
    try:
        states=actor.get_components_by_class(u.InteractionAvailabilityComponent)
        assert len(states)==1,(path,len(states))
        state=states[0]
        assert not state.get_editor_property('bInteractionUnavailable'),path
        state.set_editor_property('bInteractionUnavailable',True)
        assert not u.InteractionAvailabilityComponent.can_actor_interact(actor),path
        state.set_editor_property('bInteractionUnavailable',False)
        results.append({'path':path,'component_count':len(states),'passed':True})
    finally:
        actors.destroy_actor(actor)
bp=u.load_asset(installed['input'])
graph=u.ResourceRecoveryLibrary.export_blueprint_graphs(bp)
assert graph.count('CanActorInteract')>=1
(out/'input-gate.txt').write_text(graph,encoding='utf-8')
(out/'reload.json').write_text(json.dumps({'actors':results,'input_gate':True},indent=2),encoding='utf-8')
u.log('AVAILABILITY_RELOAD_PASS '+str(len(results)))
