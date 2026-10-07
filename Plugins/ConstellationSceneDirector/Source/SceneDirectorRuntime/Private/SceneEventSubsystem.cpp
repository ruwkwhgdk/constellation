#include "SceneEventSubsystem.h"
#include "SceneDirectorAsset.h"
#include "SceneDirectorPlayer.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "LevelSequenceActor.h"
#include "LevelSequencePlayer.h"
void USceneEventSubsystem::Record(ASceneEventBinding* B,const FString& Text)
{
 if(B)B->Status=Text;History.Add(FString::Printf(TEXT("%.2f | %s | %s"),GetWorld()->GetTimeSeconds(),B?*B->GetName():TEXT("상호작용"),*Text));if(History.Num()>100)History.RemoveAt(0);
}
bool USceneEventSubsystem::IsBusy() const
{
 if(ActivePlayer)return true;
 for(TActorIterator<ASceneDirectorPlayer> It(GetWorld());It;++It)if(It->IsDirectorPlaying())return true;
 for(TActorIterator<ALevelSequenceActor> It(GetWorld());It;++It)if(auto* P=It->GetSequencePlayer();P&&(P->IsPlaying()||P->IsPaused()))return true;
 return false;
}
ASceneDirectorPlayer* USceneEventSubsystem::Start(USceneDirectorAsset* D,const FString& Key,const FTransform& Origin,bool UseOrigin,const TMap<FName,TObjectPtr<AActor>>& Objects,FString& Error)
{
 Error.Reset();if(bShuttingDown||IsBusy()){Error=TEXT("다른 연출이 진행 중입니다.");return nullptr;}
 if(!D){Error=TEXT("연출 그래프를 지정하세요.");return nullptr;}
 auto& State=States.FindOrAdd(Key);if(State.Asset!=D){State=FSceneEventState();State.Asset=D;}
 TMap<FName,bool> Bools;TMap<FName,int32> Ints;
 for(const auto& V:D->BoolVariables)Bools.Add(V.Key,State.Bools.Contains(V.Key)?State.Bools[V.Key]:V.Value);
 for(const auto& V:D->IntVariables)Ints.Add(V.Key,State.Ints.Contains(V.Key)?State.Ints[V.Key]:V.Value);
 if(ActiveBinding.IsValid()&&ActiveBinding->bPersistVariables)if(const auto* Saved=SavedState.States.Find(PersistentKey(Key));Saved&&Saved->AssetPath==D->GetPathName()){for(auto& Pair:Bools)if(Saved->Bools.Contains(Pair.Key))Pair.Value=Saved->Bools[Pair.Key];for(auto& Pair:Ints)if(Saved->Ints.Contains(Pair.Key))Pair.Value=Saved->Ints[Pair.Key];}
 auto* Event=D->SelectEvent(Bools,Ints,Error);if(!Event)return nullptr;
 auto* R=GetWorld()->SpawnActorDeferred<ASceneDirectorPlayer>(ASceneDirectorPlayer::StaticClass(),FTransform::Identity,nullptr,nullptr,ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
 if(!R){Error=TEXT("실행기 생성 실패");return nullptr;}
 R->bAutoPlay=false;R->Director=D;R->EventKey=Event->EventKey;R->InitialBoolOverrides=Bools;R->InitialIntOverrides=Ints;R->OriginTransform=Origin;R->bUseOrigin=UseOrigin;R->ObjectBindings=Objects;R->FinishSpawning(FTransform::Identity);
 ActivePlayer=R;ActiveStateKey=Key;R->OnDirectorStopped.AddDynamic(this,&USceneEventSubsystem::Finished);
 if(!R->PlayDirector()){Error=R->LastError;R->OnDirectorStopped.RemoveDynamic(this,&USceneEventSubsystem::Finished);if(ActivePlayer==R)ActivePlayer=nullptr;R->Destroy();return nullptr;}
 return R;
}
void USceneEventSubsystem::Finished(bool Done)
{
 auto* R=ActivePlayer.Get();if(!R)return;
 if(Done){auto& State=States.FindOrAdd(ActiveStateKey);State.Bools=R->BoolValues;State.Ints=R->IntValues;if(auto* B=ActiveBinding.Get())Completed.Add(B->EventId);if(!ActiveSignal.IsEmpty())DeliveredSignals.Add(ActiveSignal);}
 if(Done)if(auto* B=ActiveBinding.Get())
 {
  FSceneEventSaveData Delta;
  if(B->bPersistVariables){FSceneEventSavedState State;State.AssetPath=R->Director->GetPathName();State.Bools=R->BoolValues;State.Ints=R->IntValues;Delta.States.Add(PersistentKey(ActiveStateKey),State);}
  if(B->Repeat==ESceneEventRepeat::OncePerSave)Delta.Completed.Add(PersistentKey(B->EventId.ToString()));
  SavedState.Merge(Delta);PendingSave.Merge(Delta);RetryPendingSave();
 }
 Record(ActiveBinding.Get(),Done?(LastSaveError.IsEmpty()?TEXT("완료"):TEXT("완료 · 저장 실패: ")+LastSaveError):TEXT("취소 / 실패: ")+R->LastError);
 R->OnDirectorStopped.RemoveDynamic(this,&USceneEventSubsystem::Finished);ActivePlayer=nullptr;ActiveBinding.Reset();ActiveSignal.Reset();R->Destroy();
}
void USceneEventSubsystem::Register(ASceneEventBinding* B){Bindings.AddUnique(B);FString Error;if(!B->Validate(Error))Record(B,Error);}
void USceneEventSubsystem::Unregister(ASceneEventBinding* B)
{
 Bindings.Remove(B);Pending.RemoveAll([B](const FSceneEventRequest& R){return R.Binding==B;});if(ActiveBinding==B)CancelActive();
}
bool USceneEventSubsystem::Request(ASceneEventBinding* B,const FString& Signal)
{
 if(!IsValid(B)||!B->bEnabled||bShuttingDown)return false;
 if((B->bPersistVariables||B->Repeat==ESceneEventRepeat::OncePerSave)&&!SaveHandler.IsBound()){Record(B,TEXT("저장 시스템 준비가 필요합니다."));return false;}
 if((B->Repeat!=ESceneEventRepeat::EveryTime&&Completed.Contains(B->EventId))||(B->Repeat==ESceneEventRepeat::OncePerSave&&SavedState.Completed.Contains(PersistentKey(B->EventId.ToString())))){Record(B,TEXT("이번 방문에서 이미 완료"));return false;}
 const FString Id=Signal.IsEmpty()?FString():B->EventId.ToString()+TEXT(":")+Signal;
 if(!Id.IsEmpty()&&DeliveredSignals.Contains(Id)){Record(B,TEXT("이미 처리한 신호"));return false;}
 if((ActiveBinding==B&&(Id.IsEmpty()||ActiveSignal==Id))||Pending.ContainsByPredicate([B,&Id](const FSceneEventRequest& R){return R.Binding==B&&(Id.IsEmpty()||R.Signal==Id);}))return false;
 if((IsBusy()||!Pending.IsEmpty())&&(B->Trigger==ESceneEventTrigger::Interaction||B->Trigger==ESceneEventTrigger::LegacySequence)){Record(B,TEXT("다른 연출 진행 중 · 다시 상호작용하세요."));return false;}
 FSceneEventRequest R;R.Binding=B;R.Origin=B->CaptureOrigin();R.Signal=Id;
 if(IsBusy()||!Pending.IsEmpty())
 {if(Pending.Num()>=64){Record(B,TEXT("대기열 한도 초과 (64)"));return false;}Pending.Add(R);Record(B,TEXT("대기"));return true;}
 return Execute(R);
}
bool USceneEventSubsystem::Execute(const FSceneEventRequest& R)
{
 auto* B=R.Binding.Get();if(!B||!B->bEnabled)return false;
 if((B->Repeat!=ESceneEventRepeat::EveryTime&&Completed.Contains(B->EventId))||(B->Repeat==ESceneEventRepeat::OncePerSave&&SavedState.Completed.Contains(PersistentKey(B->EventId.ToString()))))return false;
 if(B->Trigger==ESceneEventTrigger::Volume&&!B->PlayerInside()){Record(B,TEXT("영역 이탈 · 대기 취소"));return false;}
 // The destroyed source is intentionally no longer required; its transform was captured at signal time.
 FString Error;
 if(!B->Validate(Error,B->Trigger==ESceneEventTrigger::Destroyed)){Record(B,Error);return false;}
 for(const auto& Pair:B->Objects)if(!IsValid(Pair.Value)){Record(B,TEXT("연출 대상이 사라졌습니다."));return false;}
 ActiveBinding=B;ActiveSignal=R.Signal;
 auto* Player=Start(B->Director,B->StateKey(),R.Origin,B->Origin!=ESceneEventOrigin::Authored,B->Objects,Error);
 if(!Player){ActiveBinding.Reset();ActiveSignal.Reset();Record(B,Error);return false;}
 Record(B,TEXT("재생: ")+Player->EventKey.ToString());return true;
}
void USceneEventSubsystem::Tick(float)
{
 if(bShuttingDown||IsBusy()||Pending.IsEmpty())return;auto R=Pending[0];Pending.RemoveAt(0);Execute(R);
}
void USceneEventSubsystem::CancelActive(){if(ActivePlayer)ActivePlayer->StopDirector();}
void USceneEventSubsystem::Deinitialize(){bShuttingDown=true;Pending.Reset();CancelActive();Bindings.Reset();States.Reset();Super::Deinitialize();}
bool USceneEventSubsystem::RouteInteraction(AActor* Source,AActor* Interactor)
{
 auto* PC=GetWorld()->GetFirstPlayerController();if(!PC||PC->GetPawn()!=Interactor)return false;
 for(auto Weak:Bindings)if(auto* B=Weak.Get();B&&B->Trigger==ESceneEventTrigger::Interaction&&B->Source==Source){Request(B);return true;}return false;
}
void USceneEventSubsystem::NotifyLevelReady()
{
 if(bLevelReady)return;bLevelReady=true;
 auto Sorted=Bindings;Sorted.Sort([](const auto& A,const auto& B){if(!A.IsValid())return false;if(!B.IsValid())return true;if(A->StartOrder!=B->StartOrder)return A->StartOrder<B->StartOrder;return A->EventId.ToString()<B->EventId.ToString();});
 for(auto Weak:Sorted)if(auto* B=Weak.Get())if(B->Trigger==ESceneEventTrigger::LevelReady||(B->Trigger==ESceneEventTrigger::Volume&&B->bIncludeInitialOverlap&&B->PlayerInside()))Request(B,TEXT("Ready"));
}
void USceneEventSubsystem::NotifyCombatFinished(FName Key,FGuid Instance,ESceneCombatResult Result)
{
 if(Key.IsNone()||!Instance.IsValid()||Result==ESceneCombatResult::Any)return;
 for(auto Weak:Bindings)if(auto* B=Weak.Get();B&&B->Trigger==ESceneEventTrigger::Combat&&B->CombatKey==Key&&(B->CombatResult==ESceneCombatResult::Any||B->CombatResult==Result))Request(B,Instance.ToString());
}



FString USceneEventSubsystem::PersistentKey(const FString& Local) const{return UWorld::RemovePIEPrefix(GetWorld()->GetOutermost()->GetName())+TEXT(":")+Local;}
void USceneEventSubsystem::RestorePersistence(const FSceneEventSaveData& Data){if(!ActivePlayer&&Pending.IsEmpty())SavedState=Data;}
bool USceneEventSubsystem::RetryPendingSave()
{
 if(PendingSave.States.IsEmpty()&&PendingSave.Completed.IsEmpty())return true;
 LastSaveError.Reset();if(!SaveHandler.IsBound()){LastSaveError=TEXT("저장 연결 없음");return false;}
 if(!SaveHandler.Execute(PendingSave,LastSaveError))return false;
 PendingSave=FSceneEventSaveData();return true;
}
