#include "SchoolOpeningSceneAction.h"
#include "SchoolOpeningSceneActor.h"
#include "SceneDirectorPlayer.h"
#include "EngineUtils.h"
bool USchoolOpeningSceneAction::Execute_Implementation(ASceneDirectorPlayer* Player,AActor*,const FDirectorActionParameters& Params,FString& Error)
{
 if(Player)for(TActorIterator<ASchoolOpeningSceneActor> It(Player->GetWorld());It;++It){if(It->RunCue(Player,Params.Identifier,Params.Value))return true;break;}
 Error=TEXT("S0 cue failed (stage/door missing or unknown cue): ")+Params.Identifier.ToString();return false;
}
