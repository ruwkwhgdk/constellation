// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "TimerManager.h"
#include "TutorialPromptWidget.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnTutorialPromptDismissed);

UCLASS()
class CONSTELLATION_API UTutorialPromptWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial", meta = (ExposeOnSpawn = "true"))
	TArray<FKey> TargetKeys;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial")
	EMouseLockMode MouseLockModeWhileVisible = EMouseLockMode::DoNotLock;

	UPROPERTY(BlueprintAssignable, Category = "Tutorial")
	FOnTutorialPromptDismissed OnTutorialPromptDismissed;

	UFUNCTION(BlueprintCallable, Category = "Tutorial")
	void Dismiss();
	UFUNCTION(BlueprintPure,Category="Tutorial") bool IsWaitingForOpening() const { return bOpeningDeferred; }

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual void NativeOnFocusLost(const FFocusEvent& InFocusEvent) override;

private:
	friend class FSchoolOpeningTutorialRetryTest;
	void ActivatePrompt();
	void WaitForOpening();
	FTimerHandle OpeningTimer;
	bool bOpeningDeferred = false;
	void ApplyInputMode();
	void ReleaseInputMode();
	// Re-focuses next tick instead of immediately, avoiding re-entrant focus churn during NativeOnFocusLost.
	void ScheduleRefocus();

	bool bDismissed = false;
	bool bRefocusScheduled = false; // Prevents scheduling duplicate refocus timers
	FTimerHandle RefocusTimer;

	static TWeakObjectPtr<UTutorialPromptWidget> ActivePrompt;
};
