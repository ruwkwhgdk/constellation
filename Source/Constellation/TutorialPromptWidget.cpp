// Fill out your copyright notice in the Description page of Project Settings.

#include "TutorialPromptWidget.h"
#include "GameFramework/PlayerController.h"

TWeakObjectPtr<UTutorialPromptWidget> UTutorialPromptWidget::ActivePrompt = nullptr;

void UTutorialPromptWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (ActivePrompt.IsValid() && ActivePrompt.Get() != this)
	{
		ActivePrompt->Dismiss();
	}
	ActivePrompt = this;

	bDismissed = false;
	SetIsFocusable(true);

	ApplyInputMode();

	ScheduleRefocus();
}

void UTutorialPromptWidget::NativeDestruct()
{
	if (ActivePrompt.Get() == this)
	{
		ActivePrompt = nullptr;
	}
	Super::NativeDestruct();
}

void UTutorialPromptWidget::ApplyInputMode()
{
	if (APlayerController* PC = GetOwningPlayer())
	{
		FInputModeUIOnly InputMode;
		InputMode.SetLockMouseToViewportBehavior(MouseLockModeWhileVisible);
		if (GetCachedWidget().IsValid())
		{
			InputMode.SetWidgetToFocus(GetCachedWidget());
		}
		PC->SetInputMode(InputMode);
		PC->SetShowMouseCursor(true);
	}
}

FReply UTutorialPromptWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	UE_LOG(LogTemp, Warning, TEXT("Native On MouseButtonDown"));

	// If the pressed button is one of the dismiss keys, close the prompt.
	if (!bDismissed && TargetKeys.Contains(InMouseEvent.GetEffectingButton()))
	{
		Dismiss();
		return FReply::Handled();
	}

	// Otherwise still consume the click so it doesn't fall through to gameplay.
	return FReply::Handled();
}

FReply UTutorialPromptWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	UE_LOG(LogTemp, Warning, TEXT("Native On KeyDown"));

	if (!bDismissed && TargetKeys.Contains(InKeyEvent.GetKey()))
	{
		Dismiss();
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

void UTutorialPromptWidget::NativeOnFocusLost(const FFocusEvent& InFocusEvent)
{
	Super::NativeOnFocusLost(InFocusEvent);

	// Calling SetKeyboardFocus() directly here can re-enter this same event.
	// Defer the refocus attempt to next tick instead.
	if (!bDismissed && ActivePrompt.Get() == this)
	{
		ScheduleRefocus();
	}
}

void UTutorialPromptWidget::ScheduleRefocus()
{
	// Already scheduled or the widget is going away; don't stack another timer.
	if (bRefocusScheduled || bDismissed)
	{
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	bRefocusScheduled = true;

	TWeakObjectPtr<UTutorialPromptWidget> WeakThis(this);
	World->GetTimerManager().SetTimerForNextTick([WeakThis]()
		{
			if (!WeakThis.IsValid())
			{
				return;
			}

			WeakThis->bRefocusScheduled = false;

			if (!WeakThis->bDismissed
				&& WeakThis->ActivePrompt.Get() == WeakThis.Get()
				&& WeakThis->GetCachedWidget().IsValid())
			{
				// Deferred to next tick so this runs outside the focus event's own call stack.
				WeakThis->SetKeyboardFocus();
			}
		});
}

void UTutorialPromptWidget::Dismiss()
{
	UE_LOG(LogTemp, Warning, TEXT("Dismiss called!"));

	if (bDismissed)
	{
		return;
	}
	bDismissed = true;

	if (ActivePrompt.Get() == this)
	{
		ActivePrompt = nullptr;
	}

	if (APlayerController* PC = GetOwningPlayer())
	{
		PC->SetInputMode(FInputModeGameOnly());
		PC->SetShowMouseCursor(false);
	}

	OnTutorialPromptDismissed.Broadcast();
	RemoveFromParent();
}