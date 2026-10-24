#pragma once
#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "ItemAcquisitionTypes.h"
#include "ItemAcquisitionSubsystem.generated.h"
class UItemAcquisitionWidget;class IInputProcessor;class SWidget;class UGameViewportClient;class APlayerController;
class ASceneDirectorPlayer;

// Explicit delta clock makes app deactivation and fresh-input boundaries deterministic.
struct FItemAcquisitionTiming
{
 float Elapsed=0,ExitElapsed=0;bool bDown=false,bExiting=false;
 void Reset(bool Held){Elapsed=ExitElapsed=0;bDown=Held;bExiting=false;}
 void Advance(float Delta,bool Active){if(Active){Elapsed+=FMath::Max(0.f,Delta);if(bExiting)ExitElapsed+=FMath::Max(0.f,Delta);}}
 bool Press(bool Repeat){const bool Fresh=!bDown;bDown=true;if(!Repeat&&Fresh&&Elapsed>=.5f&&!bExiting){bExiting=true;return true;}return false;}
 void Release(){bDown=false;}
 bool Finished()const{return bExiting&&ExitElapsed>=.25f;}
};
USTRUCT()
struct FItemAcquisitionRequest
{
 GENERATED_BODY()
 UPROPERTY() FItemAcquisitionPresentation Presentation;
 FGuid Id;FKey Key;TWeakObjectPtr<UObject> Owner;bool bHasOwner=false;
 TFunction<void(bool)> Resolved;
};

/** Explicit FIFO presentation only: never mutates inventory or progression. */
UCLASS()
class CONSTELLATION_API UItemAcquisitionSubsystem : public UTickableWorldSubsystem
{
 GENERATED_BODY()
public:
 FGuid Enqueue(const FItemAcquisitionPresentation& Presentation,FKey ConfirmKey,UObject* LifetimeOwner,TFunction<void(bool)> Resolved);
 void Cancel(FGuid RequestId);
 UFUNCTION(BlueprintCallable,Category="Item Acquisition") void CancelAll();
 UFUNCTION(BlueprintPure,Category="Item Acquisition") bool IsPresenting()const{return Widget!=nullptr;}
 int32 PendingCount()const{return Requests.Num();}
 UFUNCTION(BlueprintPure,Category="Item Acquisition") int32 GetPendingCount()const{return Requests.Num();}
 UFUNCTION(BlueprintPure,Category="Item Acquisition") FKey CurrentConfirmKey()const{return ActiveKey;}
 virtual void Tick(float DeltaTime) override;
 virtual bool IsTickableWhenPaused()const override{return true;}
 virtual TStatId GetStatId()const override{RETURN_QUICK_DECLARE_CYCLE_STAT(UItemAcquisitionSubsystem,STATGROUP_Tickables);}
 virtual void Deinitialize()override;
 void InputKey(FKey Key,bool Down,bool Repeat);
 void ScrollDescription(float PixelDelta);
 bool CapturesInput()const{return bCaptured;}
protected:
 virtual bool DoesSupportWorldType(EWorldType::Type Type)const override{return Type==EWorldType::Game||Type==EWorldType::PIE;}
private:
 UPROPERTY() TArray<FItemAcquisitionRequest> Requests;
 UPROPERTY() TObjectPtr<UItemAcquisitionWidget> Widget;
 TWeakObjectPtr<APlayerController> Player;
 TWeakObjectPtr<UGameViewportClient> Viewport;
 TWeakObjectPtr<ASceneDirectorPlayer> OverlayScene;
 TWeakPtr<SWidget> PreviousFocus,PreviousCaptor;
 TSharedPtr<SWidget> OwnedFocus;
 TSharedPtr<IInputProcessor> Input;
 FItemAcquisitionTiming Timing;
 FKey ActiveKey;
 TSet<FKey> HeldKeys;
 uint8 PreviousCapture=0,PreviousLock=0;
 bool bOldCursor=false,bOldIgnoreInput=false,bCaptured=false,bStopping=false,bCancelling=false;
 double LastTick=0;
 void Capture(APlayerController* PC);
 void Restore();
 void Finish(bool Completed);
 bool StartNext();
};
