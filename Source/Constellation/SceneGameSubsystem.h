#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SceneEventSaveData.h"
#include "SceneGameSubsystem.generated.h"
UCLASS()
class CONSTELLATION_API USceneGameSubsystem:public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual bool DoesSupportWorldType(EWorldType::Type T) const override{return T==EWorldType::Game||T==EWorldType::PIE;}
 virtual void Initialize(FSubsystemCollectionBase& Collection) override;
 virtual void Deinitialize() override;
 virtual void Tick(float Delta) override;
 virtual TStatId GetStatId() const override {RETURN_QUICK_DECLARE_CYCLE_STAT(USceneGameSubsystem,STATGROUP_Tickables);}
 bool RouteInteraction(AActor* Source,bool bAfterUI);
 void UIReady();
 void BattleStarted(const FString& Key);
 void BattleEnded(const FString& Key);
 bool EnsureStorage();
 static bool MergeSave(const FString& Slot,const FSceneEventSaveData& Delta,FString& Error);
 UPROPERTY(VisibleAnywhere,Category="연출") FString Status;
private:
 TWeakObjectPtr<AActor> LegacyRequester;
 TSet<TWeakObjectPtr<AActor>> RetryInteractions;
 bool bRequesterWasHidden=false;
 TWeakObjectPtr<class ASceneDirectorPlayer> LegacyRunner;
 UFUNCTION() void LegacyReturned();
 UFUNCTION() void LegacyStopped(bool bCompleted);
 bool bUIReady=false,bStorageReady=false;
 FString Slot=TEXT("ConstellationSaveGame");
 TMap<FString,FGuid> Battles;
 bool WriteState(const FSceneEventSaveData& Delta,FString& Error);
};
UCLASS()
class CONSTELLATION_API USceneGameLibrary:public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="연출 연결") static bool RouteMappedInteraction(AActor* Source,bool bAfterUI);
 UFUNCTION(BlueprintCallable,Category="연출 연결",meta=(WorldContext="WorldContextObject")) static void NotifyGameplayUIReady(UObject* WorldContextObject);
 UFUNCTION(BlueprintCallable,Category="연출 연결",meta=(WorldContext="WorldContextObject")) static void NotifyBattleStarted(UObject* WorldContextObject,const FString& BattleZoneKey);
 UFUNCTION(BlueprintCallable,Category="연출 연결",meta=(WorldContext="WorldContextObject")) static void NotifyBattleEnded(UObject* WorldContextObject,const FString& BattleZoneKey);
};
