#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "CombatAbilitySystem.h"
#include "CombatActionDefinition.h"
#include "CombatLabCharacter.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/RootMotionSource.h"
#include "Components/BoxComponent.h"
#include "Engine/World.h"
namespace CombatTest {
UCombatActionDefinition* Action(UObject*);
ACombatLabCharacter* Actor(UWorld*,FVector,int32);
int32 Instance(ACombatLabCharacter*,UCombatActionDefinition*);
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatRadialTest,"Constellation.CombatCore.RadialOcclusion",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatRadialTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);
 auto* A=CombatTest::Actor(W,FVector(0,0,100),0);
 auto* Front=CombatTest::Actor(W,FVector(200,0,100),1);
 auto* Back=CombatTest::Actor(W,FVector(-200,0,100),1);
 auto* Behind=CombatTest::Actor(W,FVector(-280,0,100),1);
 auto* Friend=CombatTest::Actor(W,FVector(0,200,100),0);
 auto* Far=CombatTest::Actor(W,FVector(0,-800,100),1);
 auto* Wall=W->SpawnActor<AActor>();auto* Box=NewObject<UBoxComponent>(Wall);Wall->SetRootComponent(Box);
 Box->SetBoxExtent(FVector(10,100,100));Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
 Box->SetCollisionResponseToAllChannels(ECR_Block);Box->RegisterComponent();Wall->SetActorLocation(FVector(100,0,100));
 auto* Action=CombatTest::Action(A);Action->bRadialHit=true;Action->Radius=300;
 TestTrue(TEXT("Radial starts"),A->Combat->TryStartAction(Action));
 int32 Id=CombatTest::Instance(A,Action);A->Combat->OpenHitWindow(TEXT("Area"),Id);
 TestEqual(TEXT("Occluder protects front"),Front->Combat->GetHealth(),100.f);
 TestEqual(TEXT("Radial reaches behind caster"),Back->Combat->GetHealth(),80.f);
 TestEqual(TEXT("Other monsters do not shield radial damage"),Behind->Combat->GetHealth(),80.f);
 TestEqual(TEXT("Friendly protected"),Friend->Combat->GetHealth(),100.f);
 TestEqual(TEXT("Outside radius protected"),Far->Combat->GetHealth(),100.f);
 A->Combat->TickHitWindow(TEXT("Area"),Id);
 TestEqual(TEXT("Repeated ticks hit once"),Back->Combat->GetHealth(),80.f);
 A->Combat->CancelAction();Wall->Destroy();
 TestTrue(TEXT("Next cast starts"),A->Combat->TryStartAction(Action));
 Id=CombatTest::Instance(A,Action);A->Combat->OpenHitWindow(TEXT("Area"),Id);
 TestEqual(TEXT("Unblocked front hit"),Front->Combat->GetHealth(),80.f);
 A->Combat->CancelAction();W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDashTest,"Constellation.CombatCore.ActionDashLifecycle",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDashTest::RunTest(const FString&)
{
 auto* W=UWorld::CreateWorld(EWorldType::Game,false);auto* A=CombatTest::Actor(W,FVector(0,0,100),0);
 auto* Action=CombatTest::Action(A);Action->DashDistance=300;Action->DashDuration=.25f;
 auto* Move=A->GetCharacterMovement();Move->SetMovementMode(MOVE_Walking);
 TestTrue(TEXT("Dash action starts"),A->Combat->TryStartAction(Action));
 auto Motion=Move->GetRootMotionSource(TEXT("CombatActionDash"));
 TestTrue(TEXT("Dash uses swept character movement"),Motion.IsValid());
 if(Motion.IsValid()) TestEqual(TEXT("Configured dash duration"),Motion->Duration,.25f);
 A->Combat->CancelAction();
 Motion=Move->GetRootMotionSource(TEXT("CombatActionDash"));
 TestTrue(TEXT("Cancel retires motion"),!Motion.IsValid() || Motion->Status.HasFlag(ERootMotionSourceStatusFlags::MarkedForRemoval));
 Move->SetMovementMode(MOVE_Falling);
 TestFalse(TEXT("Airborne dash rejected"),A->Combat->TryStartAction(Action));
 Move->SetMovementMode(MOVE_Walking);Action->DashDuration=0;
 FString Reason;TestFalse(TEXT("Zero dash duration invalid"),Action->Validate(Reason));
 Action->DashDuration=100;TestFalse(TEXT("Movement cannot outlast action"),Action->Validate(Reason));
 W->DestroyWorld(false);return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FCombatDashCollisionTest,"Constellation.CombatCore.ActionDashCollision",
 EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FCombatDashCollisionTest::RunTest(const FString&)
{
 auto Run=[this](float Step,bool Block)
 {
  auto* W=UWorld::CreateWorld(EWorldType::Game,false);
  auto MakeBox=[W](FVector Position,FVector Extent)
  {
   auto* Actor=W->SpawnActor<AActor>();auto* Box=NewObject<UBoxComponent>(Actor);Actor->SetRootComponent(Box);
   Box->SetBoxExtent(Extent);Box->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
   Box->SetCollisionResponseToAllChannels(ECR_Block);Box->RegisterComponent();Actor->SetActorLocation(Position);
  };
  MakeBox(FVector(0,0,-10),FVector(2000,2000,10));
  if(Block) MakeBox(FVector(180,0,100),FVector(10,200,200));
  auto* A=CombatTest::Actor(W,FVector(0,0,96),0);
  auto* Move=A->GetCharacterMovement();Move->bRunPhysicsWithNoController=true;Move->SetMovementMode(MOVE_Walking);
  auto* Action=CombatTest::Action(A);Action->DashDistance=300;Action->DashDuration=.3f;
  TestTrue(TEXT("Physical dash starts"),A->Combat->TryStartAction(Action));
  for(int32 I=0;I<FMath::RoundToInt(.3f/Step);++I) Move->TickComponent(Step,LEVELTICK_All,nullptr);
  const float Distance=A->GetActorLocation().X;
  if(Block) TestTrue(TEXT("Capsule stops before wall"),Distance>20 && Distance<170);
  else TestTrue(TEXT("Unblocked dash covers configured distance"),FMath::IsNearlyEqual(Distance,300.f,15.f));
  A->Combat->ReceiveCombatDamage(1000,nullptr);
  auto Motion=Move->GetRootMotionSource(TEXT("CombatActionDash"));
  TestTrue(TEXT("Death retires dash"),!Motion.IsValid() || Motion->Status.HasFlag(ERootMotionSourceStatusFlags::MarkedForRemoval));
  W->DestroyWorld(false);return Distance;
 };
 const float A=Run(.01f,false),B=Run(.05f,false);
 TestTrue(TEXT("Dash distance stable across frame rates"),FMath::Abs(A-B)<15);
 Run(.01f,true);Run(.05f,true);return true;
}
#endif
