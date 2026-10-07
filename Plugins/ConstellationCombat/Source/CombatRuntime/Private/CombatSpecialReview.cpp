#include "CombatLabCharacter.h"
#if !UE_BUILD_SHIPPING
#include "CombatAbilitySystem.h"
#include "CombatAttributes.h"
#include "CombatWorkbenchSubsystem.h"
#include "CombatActionDefinition.h"
#include "CombatEnemyAgent.h"
#include "AIController.h"
#include "BrainComponent.h"
#include "EngineUtils.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "InputKeyEventArgs.h"
#include "GenericPlatform/GenericPlatformInputDeviceMapper.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "TimerManager.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "UnrealClient.h"
#include "Kismet/KismetSystemLibrary.h"
void ACombatLabCharacter::ConfigureSpecialReview()
{
 if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatSpecialReview")))return;
 struct FState {TWeakObjectPtr<ACombatLabCharacter> Enemy;FVector Start;bool Passed=true;float HP=0;float Recovery=0;};
 auto State=MakeShared<FState>();
 auto Check=[State](bool OK,const TCHAR* Name){State->Passed&=OK;UE_LOG(LogTemp,Display,TEXT("CombatSpecial%sReview: %s"),Name,OK?TEXT("PASS"):TEXT("FAIL"));};
 auto Key=[this](FKey K,EInputEvent E){auto* V=GetGameInstance()->GetGameViewportClient();V->InputKey(FInputKeyEventArgs(V->Viewport,IPlatformInputDeviceMapper::Get().GetDefaultInputDevice(),K,E,FPlatformTime::Cycles64()));};
 auto At=[this](float Time,TFunction<void()> Fn){FTimerHandle Timer;GetWorldTimerManager().SetTimer(Timer,FTimerDelegate::CreateWeakLambda(this,MoveTemp(Fn)),Time,false);};
 At(2,[this,State,Check,Key]{
  for(TActorIterator<ACombatLabCharacter> It(GetWorld());It;++It)if(It->bTrainingEnemy){
   if(auto* AI=Cast<AAIController>(It->GetController())){if(AI->BrainComponent)AI->BrainComponent->StopLogic(TEXT("Special input review"));AI->StopMovement();}
   It->EnemyAgent->SetComponentTickEnabled(false);It->Combat->CancelAction();if(!State->Enemy.IsValid())State->Enemy=*It;
  }
  Check(SkillAction && UltimateAction && State->Enemy.IsValid(),TEXT("Loadout"));
  if(!State->Passed)return;
  Combat->CancelAction();State->Recovery=Combat->StaminaRecoveryPerSecond;Combat->StaminaRecoveryPerSecond=0;
  SetActorLocation(State->Enemy->GetActorLocation()-FVector(450,0,0));SetActorRotation(FRotator::ZeroRotator);
  GetCharacterMovement()->SetMovementMode(MOVE_Walking);State->Start=GetActorLocation();Key(EKeys::Q,IE_Pressed);
 });
 At(2.1f,[this,Check,Key]{Key(EKeys::Q,IE_Released);Check(Combat->GetActiveAction()==SkillAction && FMath::IsNearlyEqual(Combat->GetStamina(),80.f),TEXT("QInput"));});
 At(2.4f,[this,State,Check,Key]{
  Check(GetActorLocation().X>State->Start.X+30,TEXT("DashMovement"));Combat->CancelAction();
  Combat->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),0);Key(EKeys::E,IE_Pressed);
 });
 At(2.55f,[this,State,Check,Key]{
  Key(EKeys::E,IE_Released);Check(!Combat->IsActing() && Combat->GetUltimateCharge()==0,TEXT("EmptyUltimate"));
  if(!State->Enemy.IsValid())return;
  SetActorLocation(State->Enemy->GetActorLocation()-FVector(150,0,0));State->HP=State->Enemy->Combat->GetHealth();
  Combat->SetNumericAttributeBase(UCombatAttributes::GetUltimateChargeAttribute(),100);Key(EKeys::E,IE_Pressed);
 });
 At(2.7f,[this,Check,Key]{Key(EKeys::E,IE_Released);Check(Combat->GetActiveAction()==UltimateAction && Combat->GetUltimateCharge()==0,TEXT("EInput"));});
 At(3.4f,[this,State,Check]{
  if(State->Enemy.IsValid()){
   FHitResult Hit;FCollisionQueryParams Query(SCENE_QUERY_STAT(CombatSpecialDiagnostic),false,this);
   GetWorld()->LineTraceSingleByChannel(Hit,GetActorLocation(),State->Enemy->GetActorLocation(),ECC_Visibility,Query);
   UE_LOG(LogTemp,Display,TEXT("Special area diagnostic: source=%s target=%s hp=%.0f->%.0f distance=%.1f blocker=%s radial=%d radius=%.0f"),
    *GetActorLocation().ToString(),*State->Enemy->GetActorLocation().ToString(),State->HP,State->Enemy->Combat->GetHealth(),
    FVector::Dist(GetActorLocation(),State->Enemy->GetActorLocation()),*GetNameSafe(Hit.GetActor()),UltimateAction?UltimateAction->bRadialHit:0,UltimateAction?UltimateAction->Radius:0);
  }
  Check(State->Enemy.IsValid() && State->Enemy->Combat->GetHealth()<State->HP,TEXT("AreaDamage"));
 });
 At(4,[this,State]{
  Combat->StaminaRecoveryPerSecond=State->Recovery;
  const FString Dir=FPaths::ProjectSavedDir()/TEXT("CombatAudit/Special");IFileManager::Get().MakeDirectory(*Dir,true);
  FScreenshotRequest::RequestScreenshot(Dir/TEXT("loadout.png"),true,false);
  auto* Model=GetGameInstance()->GetSubsystem<UCombatWorkbenchSubsystem>();FString Result;
  const FString Name=TEXT("Special_")+FGuid::NewGuid().ToString(EGuidFormats::Digits);
  const bool Saved=Model->ExportTuningReport(Model->ReadValues(),Name,Result);
  UE_LOG(LogTemp,Display,TEXT("CombatSpecialTuningReportReview: %s %s"),Saved?TEXT("PASS"):TEXT("FAIL"),*Name);
 });
 At(5,[this,State]{UE_LOG(LogTemp,Display,TEXT("COMBAT_SPECIAL_REVIEW %s"),State->Passed?TEXT("PASS"):TEXT("FAIL"));UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);});
}

#include "CombatEncounterDirector.h"
void ACombatLabCharacter::ConfigureGroupReview()
{
 if(bTrainingEnemy || !FParse::Param(FCommandLine::Get(),TEXT("CombatGroupReview")))return;
 static int32 Phase=0;static bool Passed=true;
 auto Check=[](bool OK,const TCHAR* Name){Passed&=OK;UE_LOG(LogTemp,Display,TEXT("CombatGroup%sReview: %s"),Name,OK?TEXT("PASS"):TEXT("FAIL"));};
 auto At=[this](float T,TFunction<void()> Fn){FTimerHandle H;GetWorldTimerManager().SetTimer(H,FTimerDelegate::CreateWeakLambda(this,MoveTemp(Fn)),T,false);};
 if(Phase==1){At(1,[this,Check]{
  Check(EncounterDirector && EncounterDirector->Outcome==ECombatEncounterOutcome::Active && EncounterDirector->LivingEnemies()==3 && Combat->GetHealth()==Combat->GetMaxHealth(),TEXT("Restart"));
  UE_LOG(LogTemp,Display,TEXT("COMBAT_GROUP_REVIEW %s"),Passed?TEXT("PASS"):TEXT("FAIL"));
  UKismetSystemLibrary::QuitGame(this,nullptr,EQuitPreference::Quit,false);
 });return;}
 struct FState {TSet<TWeakObjectPtr<ACombatLabCharacter>> Attackers;int32 Samples=0;FTimerHandle Sample;};auto State=MakeShared<FState>();
 At(1,[this,State,Check]{
  Check(EncounterDirector && EncounterDirector->LivingEnemies()==3,TEXT("AuthoredGroup"));if(!EncounterDirector)return;
  Combat->MaxHealth=10000;Combat->SetNumericAttributeBase(UCombatAttributes::GetHealthAttribute(),10000);
  // Place the authored actors in a clear triangle; their real AI and navigation remain enabled.
  const FVector Center=EncounterDirector->Enemies[0]->GetActorLocation()-FVector(300,0,0);SetActorLocation(Center);
  int32 I=0;for(const auto& Enemy:EncounterDirector->Enemies){const float Angle=I++*2*PI/3;Enemy->SetActorLocation(Center+FVector(FMath::Cos(Angle)*150,FMath::Sin(Angle)*150,0));}
  GetWorldTimerManager().SetTimer(State->Sample,FTimerDelegate::CreateWeakLambda(this,[this,State]{
   ++State->Samples;int32 Acting=0;for(const auto& Enemy:EncounterDirector->Enemies)if(Enemy->Combat->IsActing()){++Acting;State->Attackers.Add(Enemy.Get());}
   Passed&=Acting<=EncounterDirector->MaxAttackers;
  }),.02f,true);
 });
 At(13,[this,State,Check]{
  GetWorldTimerManager().ClearTimer(State->Sample);
  Check(State->Samples>100 && State->Attackers.Num()>=2,TEXT("RealAIConcurrency"));
  UE_LOG(LogTemp,Display,TEXT("Group samples=%d unique attackers=%d"),State->Samples,State->Attackers.Num());
  Check(Combat->GetHealth()<10000,TEXT("RealDamage"));
  if(EncounterDirector)for(const auto& Enemy:EncounterDirector->Enemies)Enemy->Combat->ReceiveCombatDamage(100000,this);
 });
 At(14,[this,Check]{Check(EncounterDirector && EncounterDirector->Outcome==ECombatEncounterOutcome::Completed && EncounterDirector->ActiveAttackers()==0,TEXT("Completion"));Phase=1;ResetReview();});
}
#endif
