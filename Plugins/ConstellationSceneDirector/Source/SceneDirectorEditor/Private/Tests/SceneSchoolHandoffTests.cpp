#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorPlayer.h"
#include "SceneDirectorAction.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolActivationOwnership,"Constellation.SceneDirector.SchoolActivationOwnership",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolActivationOwnership::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* Asset=LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/School/DA_Little_Girl_Event_Mushroom_Cave"));
 if(!TestNotNull(TEXT("Girl scene"),Asset)){GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return false;}
 auto* Runner=W->SpawnActor<ASceneDirectorPlayer>();Runner->bAutoPlay=false;Runner->Director=Asset;
 for(const auto& O:Asset->Objects)Runner->ObjectBindings.Add(O.Key,W->SpawnActor<AActor>(O.ActorClass));
 auto* Girl=Cast<ACharacter>(Runner->ObjectBindings.FindRef(TEXT("little_girl")));
 if(!TestNotNull(TEXT("Girl character"),Girl)){GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return false;}
 auto* Move=Girl->GetCharacterMovement();Move->SetMovementMode(MOVE_Walking);Move->Velocity=FVector(0,0,-100);
 Girl->GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);Girl->GetMesh()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
 TestTrue(TEXT("Scene starts"),Runner->PlayDirector());Runner->Tick(.1f);
 TestEqual(TEXT("Cinematic binding disables gameplay locomotion"),uint8(Move->MovementMode),uint8(MOVE_None));
 TestTrue(TEXT("Cinematic binding clears residual velocity"),Move->Velocity.IsNearlyZero());
 TestEqual(TEXT("Cinematic capsule cannot push the player or obstruct its camera"),Girl->GetCapsuleComponent()->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
 TestEqual(TEXT("Cinematic mesh cannot obstruct the gameplay camera"),Girl->GetMesh()->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
 Runner->StopDirector();
 TestEqual(TEXT("Cancellation restores movement"),uint8(Move->MovementMode),uint8(MOVE_Walking));
 TestEqual(TEXT("Cancellation restores capsule collision"),Girl->GetCapsuleComponent()->GetCollisionEnabled(),ECollisionEnabled::QueryAndPhysics);
 TestEqual(TEXT("Cancellation restores mesh collision"),Girl->GetMesh()->GetCollisionEnabled(),ECollisionEnabled::QueryAndPhysics);
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSchoolGirlDeactivation,"Constellation.SceneDirector.SchoolGirlDeactivation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FSchoolGirlDeactivation::RunTest(const FString&)
{
 auto* A=LoadObject<USceneDirectorAsset>(nullptr,TEXT("/Game/SceneDirector/School/DA_Little_Girl_Event_Mushroom_Cave"));if(!TestNotNull(TEXT("Girl scene"),A))return false;
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(W);W->InitializeActorsForPlay(FURL());
 auto* R=W->SpawnActor<ASceneDirectorPlayer>();R->bAutoPlay=false;R->Director=A;
 for(const auto& O:A->Objects)R->ObjectBindings.Add(O.Key,W->SpawnActor<AActor>(O.ActorClass));
 AActor* Girl=R->ObjectBindings.FindRef(TEXT("little_girl"));TestNotNull(TEXT("Bound girl"),Girl);
 TestTrue(TEXT("Scene starts"),R->PlayDirector());bool CheckedReturn=false;bool CheckedOwnership=false;
 for(int I=0;I<600&&R->IsDirectorPlaying();++I)
 {
  if(R->IsWaitingForDialogue())R->AdvanceDialogue();R->Tick(1.f/30);
  if(!CheckedOwnership&&I==2)
  {
   CheckedOwnership=true;
   for(FName Key:{FName(TEXT("Heroine")),FName(TEXT("little_girl"))})if(auto* NPC=Cast<ACharacter>(R->FindNPC(Key)))
   {
    TestEqual(TEXT("Bound scene character movement is exclusively sequencer-controlled"),uint8(NPC->GetCharacterMovement()->MovementMode),uint8(MOVE_None));
    TestEqual(TEXT("Bound scene character cannot collide with return camera"),NPC->GetCapsuleComponent()->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
   }
  }
  if(R->bReturningToGameplay&&!CheckedReturn){CheckedReturn=true;TestTrue(TEXT("Departed girl remains hidden when clip restores its state"),Girl&&Girl->IsHidden());}
 }
 TestTrue(TEXT("Return reached"),CheckedReturn);TestFalse(TEXT("Scene finished"),R->IsDirectorPlaying());
 TestTrue(TEXT("Departed girl remains hidden after root sequence cleanup"),Girl&&Girl->IsHidden());
 if(auto* Character=Cast<ACharacter>(Girl))TestEqual(TEXT("Departed girl cannot obstruct gameplay camera after cleanup"),Character->GetCapsuleComponent()->GetCollisionEnabled(),ECollisionEnabled::NoCollision);
 GEngine->DestroyWorldContext(W);W->DestroyWorld(false);return true;
}
#endif
