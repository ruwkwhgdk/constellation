#include "ConstellationSceneFXAction.h"
#include "ConstellationFXLibrary.h"
#include "ConstellationFXActor.h"
#include "ConstellationGlass.h"
#include "ConstellationCaveFX.h"
#include "SceneDirectorPlayer.h"
bool UConstellationSceneFXAction::Execute_Implementation(ASceneDirectorPlayer* Player,AActor* Target,const FDirectorActionParameters& P,FString& Error){
 if(!IsValid(Player)){Error=TEXT("Effects need a valid scene player");return false;}
 if(P.Identifier==TEXT("StopEffects")){UConstellationFXLibrary::StopEffectsForOwner(Player);return true;}
 if(!IsValid(Target)){Error=TEXT("Effects need a bound target actor");return false;}
 if(P.Identifier==TEXT("GlassBreak")||P.Identifier==TEXT("GlassReset")){
  auto* G=Cast<AConstellationGlass>(Target);if(!G){Error=TEXT("Glass operation requires ConstellationGlass");return false;}
  if(!G->SetBrokenForScene(Player,P.Identifier==TEXT("GlassBreak"))){Error=TEXT("Glass is controlled by another scene");return false;}return true;
 }
 if(P.Identifier==TEXT("CaveEnable")){auto* C=Cast<AConstellationCaveFX>(Target);if(!C){Error=TEXT("CaveEnable requires ConstellationCaveFX");return false;}if(!C->ApplySceneEnabled(Player,P.Flag)){Error=TEXT("Cave already controlled by another scene");return false;}return true;}
 int64 K=StaticEnum<EConstellationFXKind>()->GetValueByNameString(P.Identifier.ToString());if(K==INDEX_NONE||K>int64(EConstellationFXKind::PlayerHit)){Error=TEXT("Unknown effect identifier: ")+P.Identifier.ToString();return false;}
 EConstellationFXKind Kind=EConstellationFXKind(K);
 FLinearColor Color=Kind==EConstellationFXKind::SlimeHit||Kind==EConstellationFXKind::SlimeAttack?FLinearColor(.12,.8,.32,1):Kind==EConstellationFXKind::RunDust?FLinearColor(.3,.23,.15,.65):FLinearColor(.65,.86,1,1);
 auto* FX=UConstellationFXLibrary::SpawnEffect(Player,Kind,Target->GetActorLocation(),Target->GetActorForwardVector(),Color,P.Value>0?P.Value:1);
 if(!FX){Error=TEXT("Effect could not spawn (world/limit)");return false;}FX->SetOwner(Player);Player->OnDirectorStopped.AddUniqueDynamic(FX,&AConstellationFXActor::OnSceneStopped);return true;
}
