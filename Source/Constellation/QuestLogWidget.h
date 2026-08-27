// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "QuestTypes.h"
#include "QuestLogWidget.generated.h"

/**
 * Base class for a quest log/journal widget. Pulls quest data from UQuestSubsystem and hands it to
 * Blueprint as a ready-to-render list, so the UMG side never needs to branch on quest state itself.
 * Make a Blueprint child of this class (e.g. WBP_QuestLog) and implement OnQuestListRefreshed.
 */
UCLASS(Abstract)
class CONSTELLATION_API UQuestLogWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Re-pulls every searchable quest's display info and calls OnQuestListRefreshed. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	void RefreshQuestList();

	/** Implement in Blueprint to render Quests (e.g. populate a list/scroll box). */
	UFUNCTION(BlueprintImplementableEvent, Category = "Quest")
	void OnQuestListRefreshed(const TArray<FQuestDisplayInfo>& Quests);

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

private:
	UFUNCTION()
	void HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState);

	UFUNCTION()
	void HandleQuestProgressChanged(FName QuestID, int32 NewProgress);

	UFUNCTION()
	void HandleQuestCompleted(FName QuestID, FName EndingID);
};
