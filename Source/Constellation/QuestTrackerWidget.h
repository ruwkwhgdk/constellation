// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "QuestTypes.h"
#include "QuestTrackerWidget.generated.h"

/**
 * Base class for the always-on HUD quest tracker (e.g. bottom-left corner panel). Shows exactly one
 * quest at a time — whichever UQuestSubsystem currently reports as the tracked quest (auto-picked,
 * Main-type preferred, or pinned via SetTrackedQuest) — rather than a full quest log/journal.
 * Make a Blueprint child of this class (e.g. WBP_QuestTracker) and implement OnTrackerRefreshed.
 */
UCLASS(Abstract)
class CONSTELLATION_API UQuestTrackerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Re-pulls the tracked quest's display info and calls OnTrackerRefreshed. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	void RefreshTracker();

	/**
	 * Implement in Blueprint to render Info. Info.bVisible is false when no quest is currently
	 * tracked (e.g. nothing accepted yet) — collapse the panel in that case.
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Quest")
	void OnTrackerRefreshed(const FQuestDisplayInfo& Info);

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

private:
	UFUNCTION()
	void HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState);

	UFUNCTION()
	void HandleQuestProgressChanged(FName QuestID, int32 NewProgress);

	UFUNCTION()
	void HandleQuestInnerProgressChanged(FName QuestID, int32 NewInnerProgress);

	UFUNCTION()
	void HandleTrackedQuestChanged(FName NewTrackedQuestID);
};
