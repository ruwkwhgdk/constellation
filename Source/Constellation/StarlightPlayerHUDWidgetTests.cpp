#if WITH_DEV_AUTOMATION_TESTS
#include "StarlightPlayerHUDWidget.h"
#include "TutorialPromptTestTypes.h"
#include "CombatAbilitySystem.h"
#include "Components/ActorComponent.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Misc/AutomationTest.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStarlightHUDResourceTest,"Constellation.StarlightHUD.ResourcesAndFeedback",EAutomationTestFlags::EditorContext|EAutomationTestFlags::EngineFilter)
bool FStarlightHUDResourceTest::RunTest(const FString&)
{
 UWorld* World=UWorld::CreateWorld(EWorldType::Game,false);if(!TestNotNull(TEXT("HUD world"),World))return false;
 auto* PC=World->SpawnActor<ATutorialPromptTestController>();
 auto* Player=NewObject<ULocalPlayer>(GEngine);Player->PlayerController=PC;PC->Player=Player;World->AddController(PC);
 PC->bShowMouseCursor=true;
 UClass* StatsClass=LoadClass<UActorComponent>(nullptr,TEXT("/Game/Constellation/Gameplay/Combat/Components/Ac_Stats.Ac_Stats_C"));
 if(!TestNotNull(TEXT("Authored legacy resource component"),StatsClass)){World->DestroyWorld(false);return false;}
 auto Set=[this](UObject* Object,FName Name,double Value)
 {
  FDoubleProperty* Property=FindFProperty<FDoubleProperty>(Object->GetClass(),Name);
  if(TestNotNull(*FString::Printf(TEXT("Resource %s"),*Name.ToString()),Property))Property->SetPropertyValue_InContainer(Object,Value);
 };
 auto MakePawn=[World,StatsClass]()
 {
  auto* Pawn=World->SpawnActor<APawn>();auto* Stats=NewObject<UActorComponent>(Pawn,StatsClass);
  Pawn->AddInstanceComponent(Stats);Stats->RegisterComponent();return Pawn;
 };
 auto* Pawn=MakePawn();UObject* Stats=UStarlightPlayerHUDWidget::FindLegacyStats(Pawn);
 Set(Stats,TEXT("MaxHP"),100);Set(Stats,TEXT("CurrentHP"),20);Set(Stats,TEXT("MaxStamina"),100);Set(Stats,TEXT("CurrentStamina"),75);PC->Possess(Pawn);
 auto* HUD=NewObject<UStarlightPlayerHUDWidget>(World);HUD->SetOwningPlayer(PC);HUD->NativeConstruct();
 TestEqual(TEXT("Reads legacy health"),HUD->GetHealthRatio(),.2f);TestEqual(TEXT("Reads legacy stamina"),HUD->GetStaminaRatio(),.75f);
 TestEqual(TEXT("Startup low health has no invented damage trail"),HUD->GetDamageTrailRatio(),.2f);
 Set(Stats,TEXT("CurrentHP"),10);UStarlightPlayerHUDWidget::NotifyDamage(Pawn);HUD->AdvanceVisuals(0);
 TestEqual(TEXT("Accepted damage updates live ratio"),HUD->GetHealthRatio(),.1f);
 TestEqual(TEXT("Accepted damage retains preceding ratio in trail"),HUD->GetDamageTrailRatio(),.2f);
 HUD->AdvanceVisuals(.8f);TestEqual(TEXT("Damage trail converges to actual health"),HUD->GetDamageTrailRatio(),.1f);
 Set(Stats,TEXT("MaxHP"),20);HUD->AdvanceVisuals(0);
 TestEqual(TEXT("Maximum edit cannot create damage trail"),HUD->GetDamageTrailRatio(),.5f);
 Set(Stats,TEXT("CurrentStamina"),0);HUD->AdvanceVisuals(0);
 TestEqual(TEXT("Zero stamina is represented exactly"),HUD->GetStaminaRatio(),0.f);
 TestFalse(TEXT("Zero stamina alone is not a rejection"),HUD->IsFailureFeedbackActive());
 UStarlightPlayerHUDWidget::NotifyStaminaRejected(Pawn);HUD->AdvanceVisuals(.04375f);
 TestTrue(TEXT("Rejected action activates feedback"),HUD->IsFailureFeedbackActive());
 TestTrue(TEXT("Star moves within the 2.5 unit bound"),HUD->GetStarOffset().X>2.4&&HUD->GetStarOffset().X<=2.5);
 UStarlightPlayerHUDWidget::NotifyStaminaRejected(Pawn);HUD->AdvanceVisuals(.31f);
 TestFalse(TEXT("Repeated rejection cannot restart active feedback"),HUD->IsFailureFeedbackActive());
 TestTrue(TEXT("Star returns exactly to rest"),HUD->GetStarOffset().IsNearlyZero());
 UStarlightPlayerHUDWidget::NotifyStaminaRejected(Pawn);TestFalse(TEXT("Cooldown suppresses immediate reactivation"),HUD->IsFailureFeedbackActive());
 HUD->AdvanceVisuals(.16f);UStarlightPlayerHUDWidget::NotifyStaminaRejected(Pawn);TestTrue(TEXT("New rejection works after cooldown"),HUD->IsFailureFeedbackActive());
 auto* Slime=MakePawn();UObject* SlimeStats=UStarlightPlayerHUDWidget::FindLegacyStats(Slime);
 Set(SlimeStats,TEXT("MaxHP"),200);Set(SlimeStats,TEXT("CurrentHP"),150);Set(SlimeStats,TEXT("MaxStamina"),80);Set(SlimeStats,TEXT("CurrentStamina"),20);
 PC->Possess(Slime);HUD->AdvanceVisuals(0);
 TestEqual(TEXT("Possession uses active form health"),HUD->GetHealthRatio(),.75f);TestEqual(TEXT("Possession uses active form stamina"),HUD->GetStaminaRatio(),.25f);
 TestFalse(TEXT("Possession clears prior form feedback"),HUD->IsFailureFeedbackActive());
 UStarlightPlayerHUDWidget::NotifyStaminaRejected(Pawn);TestFalse(TEXT("Old pawn events ignored"),HUD->IsFailureFeedbackActive());

 auto* NativePawn=World->SpawnActor<APawn>();auto* Combat=NewObject<UCombatAbilitySystem>(NativePawn);NativePawn->AddInstanceComponent(Combat);Combat->RegisterComponent();Combat->InitializeCombat(NativePawn);
 PC->Possess(NativePawn);HUD->AdvanceVisuals(0);TestEqual(TEXT("Native resources used without legacy stats"),HUD->GetHealthRatio(),1.f);
 TestTrue(TEXT("Native damage observer bound"),Combat->OnDamageAccepted.IsBoundToObject(HUD));
 TestTrue(TEXT("Actual native damage accepted"),Combat->ReceiveCombatDamage(20,nullptr));HUD->AdvanceVisuals(0);
 TestEqual(TEXT("Native damage health ratio"),HUD->GetHealthRatio(),.8f);TestEqual(TEXT("Native accepted damage starts trail"),HUD->GetDamageTrailRatio(),1.f);
 Combat->OnStaminaActionRejected.Broadcast();TestTrue(TEXT("Native rejection observer activates feedback"),HUD->IsFailureFeedbackActive());
 HUD->NativeDestruct();TestFalse(TEXT("Removal releases damage delegate"),Combat->OnDamageAccepted.IsBoundToObject(HUD));TestFalse(TEXT("Removal releases rejection delegate"),Combat->OnStaminaActionRejected.IsBoundToObject(HUD));
 TestFalse(TEXT("Removal clears timer"),World->GetTimerManager().IsTimerActive(HUD->VisualTimer));
 HUD->NativeConstruct();TestEqual(TEXT("Recreation starts without stale damage trail"),HUD->GetDamageTrailRatio(),HUD->GetHealthRatio());HUD->NativeDestruct();
 TestEqual(TEXT("HUD never sets input mode"),PC->InputModeCalls,0);TestTrue(TEXT("HUD preserves cursor"),PC->bShowMouseCursor!=0);TestFalse(TEXT("HUD is not focusable"),HUD->IsFocusable());
 World->DestroyWorld(false);return true;
}
#endif
