#include "SceneGameSubsystem.h"
#include "SceneEventSubsystem.h"
#include "ConstellationSaveGame.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/GameInstance.h"
#include "Engine/LevelStreaming.h"
#include "GameFramework/PlayerController.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
void USceneGameSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
 Super::Initialize(Collection);Collection.InitializeDependency<USceneEventSubsystem>();FParse::Value(FCommandLine::Get(),TEXT("SceneEventSaveSlot="),Slot);EnsureStorage();
}
bool USceneGameSubsystem::EnsureStorage()
{
 if(bStorageReady)return true;if(!GetWorld()->GetGameInstance())return false;
 UConstellationSaveGame* Save=nullptr;
 if(UGameplayStatics::DoesSaveGameExist(Slot,0)){Save=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot,0));if(!Save){Status=TEXT("저장 파일 읽기 실패 · 기존 파일을 덮어쓰지 않습니다.");return false;}}
 if(Save&&Save->SceneEvents.Version!=1){Status=TEXT("지원하지 않는 연출 저장 버전");return false;}
 auto* Events=GetWorld()->GetSubsystem<USceneEventSubsystem>();Events->RestorePersistence(Save?Save->SceneEvents:FSceneEventSaveData());Events->SaveHandler.BindUObject(this,&USceneGameSubsystem::WriteState);bStorageReady=true;Status=TEXT("UI·플레이어 준비 대기");return true;
}
bool USceneGameSubsystem::MergeSave(const FString& Slot,const FSceneEventSaveData& Delta,FString& Error)
{
 Error.Reset();if(Slot.IsEmpty()||Delta.Version!=1){Error=TEXT("잘못된 저장 슬롯/버전");return false;}
 UConstellationSaveGame* Save=nullptr;
 if(UGameplayStatics::DoesSaveGameExist(Slot,0)){Save=Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(Slot,0));if(!Save){Error=TEXT("기존 저장 파일 읽기 실패");return false;}}
 else Save=NewObject<UConstellationSaveGame>();
 if(Save->SceneEvents.Version!=1){Error=TEXT("지원하지 않는 저장 버전");return false;}
 Save->SceneEvents.Merge(Delta);
 if(!UGameplayStatics::SaveGameToSlot(Save,Slot,0)){Error=TEXT("연출 상태 저장 실패");return false;}return true;
}
bool USceneGameSubsystem::WriteState(const FSceneEventSaveData& Delta,FString& Error){return MergeSave(Slot,Delta,Error);}
void USceneGameSubsystem::UIReady(){bUIReady=true;EnsureStorage();}
void USceneGameSubsystem::Tick(float)
{
 auto* W=GetWorld();if(!W->HasBegunPlay()||!bUIReady||!EnsureStorage())return;
 auto* E=W->GetSubsystem<USceneEventSubsystem>();if(E->bLevelReady)return;
 auto* PC=W->GetFirstPlayerController();if(!PC||!PC->GetPawn()||!PC->PlayerCameraManager)return;
 for(auto* L:W->GetStreamingLevels())if(L&&((L->ShouldBeLoaded()&&!L->IsLevelLoaded())||(L->ShouldBeVisible()&&!L->IsLevelVisible())))return;
 E->NotifyLevelReady();Status=TEXT("레벨 준비 완료");
}
void USceneGameSubsystem::BattleStarted(const FString& Key)
{
 if(Key.IsEmpty()){Status=TEXT("전투 Key 누락");return;}EnsureStorage();if(!Battles.Contains(Key))Battles.Add(Key,FGuid::NewGuid());
}
void USceneGameSubsystem::BattleEnded(const FString& Key)
{
 auto* ID=Battles.Find(Key);if(!ID){Status=TEXT("시작되지 않았거나 이미 종료된 전투: ")+Key;return;}const FGuid Completed=*ID;Battles.Remove(Key);
 GetWorld()->GetSubsystem<USceneEventSubsystem>()->NotifyCombatFinished(FName(*Key),Completed,ESceneCombatResult::Victory);
}
void USceneGameSubsystem::Deinitialize(){if(auto* E=GetWorld()->GetSubsystem<USceneEventSubsystem>())E->SaveHandler.Unbind();Super::Deinitialize();}
static USceneGameSubsystem* SceneBridge(UObject* C){auto* W=C?C->GetWorld():nullptr;return W?W->GetSubsystem<USceneGameSubsystem>():nullptr;}
void USceneGameLibrary::NotifyGameplayUIReady(UObject* C){if(auto* S=SceneBridge(C))S->UIReady();}
void USceneGameLibrary::NotifyBattleStarted(UObject* C,const FString& Key){if(auto* S=SceneBridge(C))S->BattleStarted(Key);}
void USceneGameLibrary::NotifyBattleEnded(UObject* C,const FString& Key){if(auto* S=SceneBridge(C))S->BattleEnded(Key);}

#include "SceneDirectorPlayer.h"
#include "EngineUtils.h"
#include "LevelSequencePlayer.h"
#include "LevelSequence.h"
#include "LevelSequenceActor.h"
#include "UObject/UnrealType.h"
static void CallInteractionEvent(AActor* Source,FName Event){if(IsValid(Source))if(auto* F=Source->FindFunction(Event);F&&F->NumParms==0)Source->ProcessEvent(F,nullptr);}
void USceneGameSubsystem::LegacyReturned(){if(LegacyRequester.IsValid())CallInteractionEvent(LegacyRequester.Get(),TEXT("Event Blend Camera Start"));}
void USceneGameSubsystem::LegacyStopped(bool Completed)
{
 auto* Requester=LegacyRequester.Get();if(auto* R=LegacyRunner.Get()){R->OnGameplayReturned.RemoveDynamic(this,&USceneGameSubsystem::LegacyReturned);R->OnDirectorStopped.RemoveDynamic(this,&USceneGameSubsystem::LegacyStopped);}
 LegacyRunner.Reset();LegacyRequester.Reset();
 if(Requester){if(Completed){RetryInteractions.Remove(Requester);CallInteractionEvent(Requester,TEXT("Event Sequence Finished"));}else{Requester->SetActorHiddenInGame(bRequesterWasHidden);RetryInteractions.Add(Requester);}}

}



bool USceneGameSubsystem::RouteInteraction(AActor* Source,bool AfterUI)
{
 if(!IsValid(Source))return false;auto* Property=FindFProperty<FObjectPropertyBase>(Source->GetClass(),TEXT("TargetLevelSequence"));auto* Sequence=Property?Cast<ULevelSequence>(Property->GetObjectPropertyValue_InContainer(Source)):nullptr;if(!Sequence)return false;
 for(TActorIterator<ASceneEventBinding> It(GetWorld());It;++It)if(It->Trigger==ESceneEventTrigger::LegacySequence&&It->OriginalSequence==Sequence)
 {
  auto* Events=GetWorld()->GetSubsystem<USceneEventSubsystem>();
  if(!AfterUI&&!RetryInteractions.Contains(Source))return Events->IsBusy()||Events->PendingCount()>0||!It->bEnabled;
  RetryInteractions.Add(Source);
  if(Events->Request(*It)&&Events->ActivePlayer)
  {
   LegacyRequester=Source;LegacyRunner=Events->ActivePlayer;bRequesterWasHidden=Source->IsHidden();
   if(auto* Hidden=FindFProperty<FBoolProperty>(Source->GetClass(),TEXT("IsHiddenAtSequenceStart"));Hidden&&Hidden->GetPropertyValue_InContainer(Source))Source->SetActorHiddenInGame(true);
   LegacyRunner->OnGameplayReturned.AddDynamic(this,&USceneGameSubsystem::LegacyReturned);LegacyRunner->OnDirectorStopped.AddDynamic(this,&USceneGameSubsystem::LegacyStopped);
  }
  return true;
 }
 return false;
}
bool USceneGameLibrary::RouteMappedInteraction(AActor* Source,bool AfterUI){if(auto* S=SceneBridge(Source))return S->RouteInteraction(Source,AfterUI);return false;}
