#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AbilityAcquisitionSubsystem.generated.h"
class UAbilityAcquisitionWidget;class UAbilityAcquisitionArt;class UActorComponent;class IInputProcessor;class SWidget;
class ASceneDirectorPlayer;
struct FAbilityAcquisitionRequest{int32 Slot=0,Mask=0;};
UCLASS()
class CONSTELLATION_API UAbilityAcquisitionSubsystem : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 virtual void Tick(float DeltaTime) override;
 virtual TStatId GetStatId()const override {RETURN_QUICK_DECLARE_CYCLE_STAT(UAbilityAcquisitionSubsystem,STATGROUP_Tickables);}
 virtual bool IsTickableWhenPaused()const override{return true;}
 virtual void Deinitialize()override;
 void Enqueue(int32 Slot,int32 PreviousMask);
 UFUNCTION(BlueprintCallable,Category="Ability UI") void Dismiss(bool Repeat);
 UFUNCTION(BlueprintPure,Category="Ability UI") bool IsPresenting()const{return Widget!=nullptr;}
 int32 PendingCount()const{return Requests.Num();}
 // Explicit lease: ordinary queued acquisitions still wait until cinematics finish.
 bool PresentForScene(ASceneDirectorPlayer* Scene,int32 Slot,int32 PreviousMask);
 void CancelScene(ASceneDirectorPlayer* Scene);
 bool GrantPresentedAbility(UActorComponent* Component,int32 Slot);
 UFUNCTION(BlueprintCallable,Category="Ability UI") void Preview(int32 Slot,int32 PreviousMask);
protected:
 virtual bool DoesSupportWorldType(EWorldType::Type Type)const override{return Type==EWorldType::Game||Type==EWorldType::PIE;}
private:
 UPROPERTY() TObjectPtr<UAbilityAcquisitionWidget> Widget;
 UPROPERTY() TObjectPtr<UAbilityAcquisitionArt> Art;
 UPROPERTY() TObjectPtr<APlayerController> Player;
 TArray<FAbilityAcquisitionRequest> Requests;
 TSharedPtr<IInputProcessor> Input;
 TWeakPtr<SWidget> PreviousFocus;
 double Started=0,ExitStarted=-1,NotBefore=0;
 bool PausedByUs=false,OldCursor=false;
 int32 SoundStage=0;
 TWeakObjectPtr<ASceneDirectorPlayer> SceneOwner;
 bool bSuppressEnqueue=false;
 void Finish();void PlayCue(int32 Index);
};
UCLASS()
class CONSTELLATION_API UAbilityAcquisitionLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 // Called BEFORE existing boolean assignment; it never changes gameplay progression.
 UFUNCTION(BlueprintCallable,Category="Ability UI") static void BeforeUnlock(UActorComponent* AbilityComponent,int32 Slot,bool Unlock);
 UFUNCTION(BlueprintCallable,Category="Ability UI",meta=(WorldContext="WorldContextObject")) static void PreviewAbilityAcquisition(UObject* WorldContextObject,int32 Slot,int32 PreviousMask);
};
