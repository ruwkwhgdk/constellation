#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SceneEventBinding.h"
#include "SceneEventSaveData.h"
#include "SceneEventSubsystem.generated.h"
class ASceneDirectorPlayer;
USTRUCT() struct FSceneEventState
{
 GENERATED_BODY()
 UPROPERTY() TObjectPtr<USceneDirectorAsset> Asset;
 UPROPERTY() TMap<FName,bool> Bools;
 UPROPERTY() TMap<FName,int32> Ints;
};
struct FSceneEventRequest
{
 TWeakObjectPtr<ASceneEventBinding> Binding;
 FTransform Origin;
 FString Signal;
};
UCLASS()
class SCENEDIRECTORRUNTIME_API USceneEventSubsystem:public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual bool DoesSupportWorldType(EWorldType::Type Type) const override { return Type==EWorldType::Game||Type==EWorldType::PIE; }
 virtual TStatId GetStatId() const override { RETURN_QUICK_DECLARE_CYCLE_STAT(USceneEventSubsystem,STATGROUP_Tickables); }
 virtual void Tick(float DeltaTime) override;
 virtual void Deinitialize() override;
 void Register(ASceneEventBinding* Binding);
 void Unregister(ASceneEventBinding* Binding);
 bool Request(ASceneEventBinding* Binding,const FString& Signal=FString());
 bool RouteInteraction(AActor* Source,AActor* Interactor);
 UFUNCTION(BlueprintCallable,Category="연출 이벤트",meta=(DisplayName="레벨 준비 완료 알림")) void NotifyLevelReady();
 UFUNCTION(BlueprintCallable,Category="연출 이벤트",meta=(DisplayName="전투 종료 알림")) void NotifyCombatFinished(FName CombatKey,FGuid BattleInstance,ESceneCombatResult Result);
 UFUNCTION(BlueprintCallable,Category="연출 이벤트") void CancelActive();
 UPROPERTY(VisibleAnywhere,Transient,Category="연출 이벤트") TObjectPtr<ASceneDirectorPlayer> ActivePlayer;
 UPROPERTY(VisibleAnywhere,Transient,Category="연출 이벤트") TArray<FString> History;
 UPROPERTY(VisibleAnywhere,Transient,Category="연출 이벤트") bool bLevelReady=false;
 ASceneDirectorPlayer* Start(USceneDirectorAsset* Director,const FString& StateKey,const FTransform& Origin,bool bUseOrigin,const TMap<FName,TObjectPtr<AActor>>& Objects,FString& Error);
 void RestorePersistence(const FSceneEventSaveData& Data);
 FSceneEventSaveHandler SaveHandler;
 UFUNCTION(BlueprintCallable,Category="연출 이벤트") bool RetryPendingSave();
 UPROPERTY(VisibleAnywhere,Transient,Category="연출 이벤트") FString LastSaveError;
 FString PersistentKey(const FString& Local) const;
 bool IsBusy() const;
 int32 PendingCount() const {return Pending.Num();}
 bool IsConsumed(FGuid Id) const {return Completed.Contains(Id);}
private:
 UPROPERTY() TMap<FString,FSceneEventState> States;
 TArray<TWeakObjectPtr<ASceneEventBinding>> Bindings;
 TArray<FSceneEventRequest> Pending;
 TSet<FGuid> Completed;
 TSet<FString> DeliveredSignals;
 FString ActiveStateKey,ActiveSignal;
 TWeakObjectPtr<ASceneEventBinding> ActiveBinding;
 bool bShuttingDown=false;
 FSceneEventSaveData SavedState,PendingSave;
 void Record(ASceneEventBinding* Binding,const FString& Text);
 bool Execute(const FSceneEventRequest& Request);
 UFUNCTION() void Finished(bool bCompleted);
};
