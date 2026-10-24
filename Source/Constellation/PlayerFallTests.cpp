#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "PlayerFallComponent.h"
#include "MyCharacter.h"
#include "CarryInputLibrary.h"
#include "CarryComponent.h"
#include "SteepSlopeMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"

namespace
{
struct FFallFixture
{
 UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);
 AMyCharacter* Character=World->SpawnActor<AMyCharacter>();
 APlayerController* Controller=World->SpawnActor<APlayerController>();
 UPlayerFallComponent* Fall=NewObject<UPlayerFallComponent>(Character);
 UObject* Stats=nullptr;
 FFallFixture()
 {
  Controller->Possess(Character);
  UClass* StatsClass=LoadClass<UActorComponent>(nullptr,TEXT("/Game/Constellation/Gameplay/Combat/Components/Ac_Stats.Ac_Stats_C"));
  auto* S=NewObject<UActorComponent>(Character,StatsClass);Stats=S;Character->AddInstanceComponent(S);S->RegisterComponent();
  Set(TEXT("MaxHP"),300);Set(TEXT("CurrentHP"),300);Set(TEXT("DefensePoint"),999);
  Character->AddInstanceComponent(Fall);Fall->RegisterComponent();Fall->Activate();
  static_cast<UActorComponent*>(Fall)->BeginPlay();
 }
 ~FFallFixture(){World->DestroyWorld(false);}
 void Set(FName Name,double Value){FindFProperty<FDoubleProperty>(Stats->GetClass(),Name)->SetPropertyValue_InContainer(Stats,Value);}
 double HP()const{return FindFProperty<FDoubleProperty>(Stats->GetClass(),TEXT("CurrentHP"))->GetPropertyValue_InContainer(Stats);}
 void Start(double Z)
 {
  Character->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
  Character->SetActorLocation(FVector(0,0,Z));
  Character->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
 }
 void Land(double Z)
 {
  Character->SetActorLocation(FVector(0,0,Z));FHitResult Hit;Character->LandedDelegate.Broadcast(Hit);
  Character->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
 }
};
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerFallLifecycle,"Constellation.Fall.Lifecycle",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FPlayerFallLifecycle::RunTest(const FString&)
{
 FFallFixture F;
 F.Start(2020);TestEqual(TEXT("Airborne tracked"),F.Fall->State,EPlayerFallState::Falling);
 F.Land(100);
 TestEqual(TEXT("Twelve heights strong"),F.Fall->LastLanding.Tier,EPlayerLandingTier::Strong);
 TestEqual(TEXT("Defense does not reduce fall damage"),F.HP(),270.0);
 TestTrue(TEXT("Recovery blocks movement"),F.Controller->IsMoveInputIgnored());
 TestFalse(TEXT("Camera remains available"),F.Controller->IsLookInputIgnored());
 for(FName Action:{FName("IA_Move"),FName("IA_Jump"),FName("IA_Dodge"),FName("IA_Attack"),FName("IA_Dash"),FName("BlockAction")})
  TestTrue(*Action.ToString(),UCarryInputLibrary::RouteCarryInput(F.Character,Action,TEXT("Started")));
 TestFalse(TEXT("Release not swallowed"),UCarryInputLibrary::RouteCarryInput(F.Character,TEXT("IA_Dash"),TEXT("Completed")));
 auto* Move=F.Character->GetCharacterMovement();
 TestEqual(TEXT("Movement speed locked"),Move->GetMaxSpeed(),0.f);
 TestFalse(TEXT("Direct jump blocked"),Move->CanAttemptJump());
 const int32 Id=F.Fall->LastLanding.LandingId;
 F.Character->LandedDelegate.Broadcast(FHitResult());TestEqual(TEXT("Duplicate landing no damage"),F.HP(),270.0);
 F.Fall->FinishLanding(Id-1);TestTrue(TEXT("Stale callback ignored"),F.Fall->IsLandingLocked());
 F.Controller->SetIgnoreMoveInput(true);
 F.Fall->FinishLanding(Id);TestTrue(TEXT("Another owner's lock survives"),F.Controller->IsMoveInputIgnored());
 F.Controller->SetIgnoreMoveInput(false);TestFalse(TEXT("Our lock released exactly once"),F.Controller->IsMoveInputIgnored());
 TestTrue(TEXT("Speed restored"),Move->GetMaxSpeed()>0);
 F.Start(3940);F.Land(100);TestEqual(TEXT("Maximum damage leaves 1 HP"),F.HP(),1.0);
 F.Fall->SetLandingRecoveryDuration(F.Fall->LastLanding.LandingId,.01f);
 F.World->GetTimerManager().Tick(.02f);++GFrameCounter;F.World->GetTimerManager().Tick(.02f);
 TestFalse(TEXT("No-animation watchdog restores control"),F.Fall->IsLandingLocked());
 F.Start(250);F.Land(100);TestEqual(TEXT("Small drop no recovery"),F.Fall->LastLanding.Tier,EPlayerLandingTier::None);
 TestFalse(TEXT("Small drop never locks"),F.Controller->IsMoveInputIgnored());
 F.Set(TEXT("CurrentHP"),0);F.Start(3940);F.Land(100);TestEqual(TEXT("Dead actor never healed"),F.HP(),0.0);
 F.Fall->ResetFall();return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerFallCancellation,"Constellation.Fall.Cancellation",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FPlayerFallCancellation::RunTest(const FString&)
{
 FFallFixture F;F.Start(1000);F.Character->SetActorLocation(FVector(0,0,2980));
 F.Fall->TickComponent(.01f,LEVELTICK_All,nullptr);F.Land(100);
 TestEqual(TEXT("Peak height includes jump ascent"),F.Fall->LastLanding.HeightCm,2880.f);
 TestEqual(TEXT("Eighteen heights damage"),F.HP(),135.0);
 F.Fall->ResetFall();F.Set(TEXT("CurrentHP"),300);
 F.Start(2500);F.Character->GetCharacterMovement()->OnTeleported();F.Land(100);
 TestEqual(TEXT("Teleport discards previous fall"),F.HP(),300.0);
 F.Start(2500);F.Fall->SetFallSuspended(true);F.Land(100);TestEqual(TEXT("Cinematic suspended"),F.HP(),300.0);
 F.Fall->SetFallSuspended(false);F.Start(2500);F.Character->GetCharacterMovement()->SetMovementMode(MOVE_Flying);F.Land(100);
 TestEqual(TEXT("Nonfall locomotion cancels"),F.HP(),300.0);
 F.Start(2020);F.Land(100);F.Fall->Deactivate();TestFalse(TEXT("Deactivation releases lock"),F.Controller->IsMoveInputIgnored());
 F.Fall->Activate();F.Start(2020);F.Land(100);F.Controller->UnPossess();F.Fall->TickComponent(.01f,LEVELTICK_All,nullptr);
 TestFalse(TEXT("Unpossess releases old controller"),F.Controller->IsMoveInputIgnored());
 F.Controller->Possess(F.Character);F.Fall->TickComponent(.01f,LEVELTICK_All,nullptr);
 F.Start(2020);F.Land(100);
 F.Controller->SetCinematicMode(true,false,false,false,false);
 F.Fall->TickComponent(.01f,LEVELTICK_All,nullptr);
 TestFalse(TEXT("Cinematic entry cancels existing recovery"),F.Fall->IsLandingLocked());
 F.Set(TEXT("CurrentHP"),300);F.Start(2500);F.Land(100);
 TestEqual(TEXT("Cinematic without movement suppression has no fall damage"),F.HP(),300.0);
 F.Controller->SetCinematicMode(false,false,false,false,false);
 F.Start(740);F.Land(100);
 auto* Carry=NewObject<UCarryComponent>(F.Character);F.Character->AddInstanceComponent(Carry);Carry->RegisterComponent();
 Carry->State=ECarryState::Aiming;
 TestTrue(TEXT("Attack release is consumed during recovery"),UCarryInputLibrary::RouteCarryInput(F.Character,TEXT("IA_Attack"),TEXT("Completed")));
 TestEqual(TEXT("Attack release cancels aim without throwing"),Carry->State,ECarryState::Carrying);
 F.Fall->ResetFall();
 return true;
}
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPlayerFallPhysicalLanding,"Constellation.Fall.PhysicalLanding",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FPlayerFallPhysicalLanding::RunTest(const FString&)
{
 FFallFixture F;
 auto* Player=NewObject<ULocalPlayer>(GEngine);Player->PlayerController=F.Controller;F.Controller->Player=Player;
 auto* Floor=F.World->SpawnActor<AActor>();auto* Box=NewObject<UBoxComponent>(Floor);
 Floor->SetRootComponent(Box);Box->SetBoxExtent(FVector(2000,2000,10));Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
 Box->SetCollisionResponseToAllChannels(ECR_Block);Box->RegisterComponent();Floor->SetActorLocation(FVector(0,0,-10));
 auto* M=F.Character->GetCharacterMovement();M->bRunPhysicsWithNoController=true;
 const float Half=F.Character->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
 F.Start(Half+3000);
 for(int I=0;I<240&&F.Fall->LastLanding.LandingId==0;++I)
 {
  M->TickComponent(1.f/60,LEVELTICK_All,nullptr);
  F.Fall->TickComponent(1.f/60,LEVELTICK_All,nullptr);
 }
 TestTrue(TEXT("Real floor collision produces landing event"),F.Fall->LastLanding.LandingId>0);
 AddInfo(FString::Printf(TEXT("Physical landing: Z=%f velocity=%s mode=%d height=%f HP=%f"),F.Character->GetActorLocation().Z,*M->Velocity.ToString(),int(M->MovementMode),F.Fall->LastLanding.HeightCm,F.HP()));
 TestEqual(TEXT("Real fall classified strong"),F.Fall->LastLanding.Tier,EPlayerLandingTier::Strong);
 TestTrue(TEXT("Height measured from capsule feet"),FMath::Abs(F.Fall->LastLanding.HeightCm-3000)<5);
 TestTrue(TEXT("Real landing applied damage and lock"),F.HP()<135&&F.HP()>110&&F.Fall->IsLandingLocked());
 F.Fall->ResetFall();return true;
}
#endif
