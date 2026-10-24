#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "TimerManager.h"
#include "Styling/SlateBrush.h"
#include "TutorialPromptWidget.generated.h"

class SBox;
class UTexture2D;
UENUM(BlueprintType)
enum class ETutorialPromptAction : uint8 { Auto, Movement, Jump, Attack, Transform, PickUp };
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnTutorialPromptDismissed);

UCLASS()
class CONSTELLATION_API UTutorialPromptWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UTutorialPromptWidget(const FObjectInitializer& ObjectInitializer);
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial", meta=(ExposeOnSpawn="true")) TArray<FKey> TargetKeys;
 // Retained for existing Blueprint serialization. Toasts never change input mode.
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial") EMouseLockMode MouseLockModeWhileVisible = EMouseLockMode::DoNotLock;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial") ETutorialPromptAction Action = ETutorialPromptAction::Auto;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial", meta=(ClampMin="0")) float FadeInSeconds = .25f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial", meta=(ClampMin="0")) float HoldSeconds = 8.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial", meta=(ClampMin="0")) float FadeOutSeconds = .35f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Tutorial") FText FooterText;
 UPROPERTY(BlueprintAssignable, Category="Tutorial") FOnTutorialPromptDismissed OnTutorialPromptDismissed;
 UFUNCTION(BlueprintPure, Category="Tutorial") FText GetInstructionText() const;
 UFUNCTION(BlueprintCallable, Category="Tutorial") void Dismiss();
 UFUNCTION(BlueprintCallable, Category="Tutorial") void NotifyTutorialActionCompleted(ETutorialPromptAction CompletedAction);
 UFUNCTION(BlueprintCallable, Category="Tutorial") static void NotifyPlayerTutorialActionCompleted(APlayerController* Player, ETutorialPromptAction CompletedAction);
 UFUNCTION(BlueprintPure, Category="Tutorial") bool IsWaitingForOpening() const { return bOpeningDeferred; }
protected:
 virtual TSharedRef<SWidget> RebuildWidget() override;
 virtual void ReleaseSlateResources(bool bReleaseChildren) override;
 virtual void NativeConstruct() override;
 virtual void NativeDestruct() override;
 virtual FReply NativeOnMouseButtonDown(const FGeometry&, const FPointerEvent&) override { return FReply::Unhandled(); }
 virtual FReply NativeOnKeyDown(const FGeometry&, const FKeyEvent&) override { return FReply::Unhandled(); }
 void AdvanceToast(float DeltaSeconds);
 int32 GetStackIndex() const;
private:
 friend class FSchoolOpeningTutorialRetryTest;
 friend class FTutorialPromptVisibilityBudgetTest;
 bool CanAdvancePresentation() const;
 void ActivatePrompt();
 void WaitForOpening();
 void TickToast();
 void FinishDismissal();
 void UnregisterToast();
 static void RefreshStacks();
 ETutorialPromptAction ResolveAction() const;
 bool ObserveAction();
 FText GetBodyText() const;
 FText GetKeyText() const;
 FText GetVerbText() const;
 FTimerHandle OpeningTimer, ToastTimer;
 bool bOpeningDeferred=false, bActive=false, bFadingOut=false, bDismissed=false, bQueued=false;
 float Elapsed=0, FadeElapsed=0, FadeStartOpacity=1;
 double LastTickTime=0;
 FVector LastPawnLocation=FVector::ZeroVector;
 TWeakObjectPtr<APawn> ObservedPawn, InitialPawn;
 TWeakObjectPtr<UActorComponent> TransformComponent;
 TArray<TWeakObjectPtr<UActorComponent>> LegacyAttackComponents;
 bool bInitiallyTransformed=false;
 int32 InitialMontageInstanceId=INDEX_NONE;
 uint64 InitialExecution=0;
 bool bPreviouslyJumping=false;
 UPROPERTY() TObjectPtr<UTexture2D> Atlas;
 FSlateBrush PanelBrush, OrnamentBrush, KeyBrush;
 TSharedPtr<SBox> ToastBox;
 static TArray<TWeakObjectPtr<UTutorialPromptWidget>> ActivePrompts;
};
