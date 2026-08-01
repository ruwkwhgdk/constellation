// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
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

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual FReply NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;
	virtual void NativeOnFocusLost(const FFocusEvent& InFocusEvent) override;

private:
	void ApplyInputMode();
	// Re-focuses next tick instead of immediately, avoiding re-entrant focus churn during NativeOnFocusLost.
	void ScheduleRefocus();

	bool bDismissed = false;
	bool bRefocusScheduled = false; // Prevents scheduling duplicate refocus timers

	static TWeakObjectPtr<UTutorialPromptWidget> ActivePrompt;
};