#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "Animation/AnimMontage.h"
#include "CombatHitReactionComponent.h"
#include "CombatLabCharacter.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatReactionLifecycleTest,"Constellation.CombatCore.Reaction.AcceptanceAndRestoration",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatReactionLifecycleTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);
 auto* Target=W->SpawnActor<ACombatLabCharacter>(); auto* Source=W->SpawnActor<ACombatLabCharacter>();
 Target->GetMesh()->SetSkeletalMesh(LoadObject<USkeletalMesh>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/SK_player_heroine_new_RunPreview")));
 Target->GetMesh()->InitAnim(true);
 Target->IdleAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_PreviewRelaxed"));
 Target->GetMesh()->PlayAnimation(Target->IdleAnimation,true);
 auto* Single=Target->GetMesh()->GetSingleNodeInstance();
 if(!TestNotNull(TEXT("Single node playback available"),Single)){W->DestroyWorld(false);return false;}
 Single->SetPosition(.01f,false);Single->SetPlaying(false);
 Target->Combat->InitializeCombat(Target); Target->HitReaction->Initialize(Target->Combat);
 TestNotNull(TEXT("Front clip retained after preload"),Target->HitReaction->FrontAnimation.Get());
 TestNotNull(TEXT("Back clip retained after preload"),Target->HitReaction->BackAnimation.Get());
 TestNotNull(TEXT("Left clip retained after preload"),Target->HitReaction->LeftAnimation.Get());
 TestNotNull(TEXT("Right clip retained after preload"),Target->HitReaction->RightAnimation.Get());
 const FTransform MeshBefore=Target->GetMesh()->GetRelativeTransform(), ActorBefore=Target->GetActorTransform();
 int32 Accepted=0; FVector Direction;
 Target->Combat->OnDamageAccepted.AddLambda([&](const FCombatAcceptedDamage& Hit){++Accepted;Direction=Hit.LocalSourceDirection;});
 TestFalse(TEXT("Zero damage rejected"),Target->Combat->ReceiveCombatDamage(0,Source));
 TestFalse(TEXT("Negative damage rejected"),Target->Combat->ReceiveCombatDamage(-5,Source));
 TestEqual(TEXT("Rejected hit has no reaction"),Accepted,0);
 const FVector Directions[]={FVector::ForwardVector,-FVector::ForwardVector,-FVector::RightVector,FVector::RightVector};
 const TCHAR* Names[]={TEXT("Front"),TEXT("Back"),TEXT("Left"),TEXT("Right")};
 for(int32 Index=0;Index<4;++Index)
 {
  Target->SetActorRotation(FRotator(0,70,0));
  Source->SetActorLocation(Target->GetActorLocation()+Target->GetActorQuat().RotateVector(Directions[Index])*100);
  TestTrue(TEXT("Accepted hit"),Target->Combat->ReceiveCombatDamage(5,Source));
  TestTrue(TEXT("Source direction captured in actor space"),Direction.Equals(Directions[Index],.001));
  TestTrue(TEXT("Reaction active"),Target->HitReaction->IsPresenting());
  TestTrue(TEXT("Correct directional clip selected"),Single->GetCurrentAsset() && Single->GetCurrentAsset()->GetName().EndsWith(Names[Index]));
  Target->Tick(.016f);
  TestTrue(TEXT("Locomotion cannot overwrite reaction"),Single->GetCurrentAsset() && Single->GetCurrentAsset()->GetName().EndsWith(Names[Index]));
  Target->HitReaction->TickComponent(.36f,LEVELTICK_All,nullptr);
  TestFalse(TEXT("Reaction finishes"),Target->HitReaction->IsPresenting());
  TestTrue(TEXT("Original asset restored"),Single->GetCurrentAsset()==Target->IdleAnimation);
  TestTrue(TEXT("Original pose time restored"),FMath::IsNearlyEqual(Single->GetCurrentTime(),.01f));
  TestFalse(TEXT("Original paused state restored"),Single->IsPlaying());
 }
 Target->SetActorRotation(ActorBefore.Rotator());
 TestTrue(TEXT("No capsule translation or scale"),Target->GetActorTransform().Equals(ActorBefore));
 TestTrue(TEXT("No mesh transform workaround"),Target->GetMesh()->GetRelativeTransform().Equals(MeshBefore));
 Target->Combat->ReceiveCombatDamage(5,Source);Target->HitReaction->TickComponent(.05f,LEVELTICK_All,nullptr);
 Target->Combat->ReceiveCombatDamage(5,Source);Target->Combat->CancelAction();
 TestFalse(TEXT("Repeated hit then cancel clears presentation"),Target->HitReaction->IsPresenting());
 TestTrue(TEXT("Repeated hit returns original asset"),Single->GetCurrentAsset()==Target->IdleAnimation);
 Target->Combat->ReceiveCombatDamage(5,Source);Target->Combat->ResetAfterReturn();
 TestFalse(TEXT("Reset clears reaction"),Target->HitReaction->IsPresenting());
 TestEqual(TEXT("Reset is not accepted damage"),Accepted,7);
 Target->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
 TestTrue(TEXT("Dodge starts after reset"),Target->Combat->TryDodge(FVector::ForwardVector));
 Target->Combat->TickComponent(.15f,LEVELTICK_All,nullptr);
 TestFalse(TEXT("Invulnerable hit rejected"),Target->Combat->ReceiveCombatDamage(5,Source));
 TestEqual(TEXT("Dodge rejection has no reaction event"),Accepted,7);
 Target->Combat->CancelDodge();
 Target->Combat->ReceiveCombatDamage(5,Source);
 Target->Combat->ReceiveCombatDamage(1000,Source);
 TestFalse(TEXT("Death clears visual reaction"),Target->HitReaction->IsPresenting());
 TestTrue(TEXT("Death restores exact transform"),Target->GetMesh()->GetRelativeTransform().Equals(MeshBefore));
 TestTrue(TEXT("Death restores original asset"),Single->GetCurrentAsset()==Target->IdleAnimation);
 W->DestroyWorld(false); return true;
}
namespace CombatTest
{
 UCombatActionDefinition* Action(UObject* Outer);
 ACombatLabCharacter* Actor(UWorld* World,FVector Location,int32 Team);
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatInterruptedReactionTest,"Constellation.CombatCore.Reaction.InterruptedAttackReturnsToIdle",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatInterruptedReactionTest::RunTest(const FString&)
{
 auto* World=UWorld::CreateWorld(EWorldType::Game,false);
 auto* Target=CombatTest::Actor(World,FVector(0,0,100),0);
 auto* Source=CombatTest::Actor(World,FVector(250,0,100),1);
 Target->IdleAnimation=LoadObject<UAnimSequence>(nullptr,TEXT("/Game/Constellation/Characters/Heroine/Refined/Animations/AS_player_heroine_new_PreviewRelaxed"));
 Target->GetMesh()->PlayAnimation(Target->IdleAnimation,true);
 Target->HitReaction->Initialize(Target->Combat);
 auto* Action=CombatTest::Action(Target);
 if(!TestTrue(TEXT("GAS attack starts"),Target->Combat->TryStartAction(Action)))
 {World->DestroyWorld(false);return false;}
 auto* Single=Target->GetMesh()->GetSingleNodeInstance();
 TestTrue(TEXT("SingleNode owns attack montage"),Single && Single->GetCurrentAsset()==Action->Montage);
 TestTrue(TEXT("Damage interrupts attack"),Target->Combat->ReceiveCombatDamage(5,Source));
 TestFalse(TEXT("Attack no longer active"),Target->Combat->IsActing());
 TestTrue(TEXT("Hit reaction replaces interrupted attack"),Target->HitReaction->IsPresenting());
 Target->HitReaction->TickComponent(.36f,LEVELTICK_All,nullptr);
 // Deliberately do not tick the character: locomotion must not be needed to hide resurrection.
 TestTrue(TEXT("Completion restores idle immediately before locomotion tick"),Single && Single->GetCurrentAsset()==Target->IdleAnimation);
 TestFalse(TEXT("Completion cannot restore canceled montage"),Single && Single->GetCurrentAsset()==Action->Montage);
 TestTrue(TEXT("Idle resumes playing"),Single && Single->IsPlaying());
 World->DestroyWorld(false);return true;
}
#endif
