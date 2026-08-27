// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "QuestTypes.h"
#include "QuestDefinition.generated.h"

/**
 * Designer-authored definition of a single quest. Create instances as Data Assets (or Blueprint
 * child classes of this class when a custom unlock condition is needed) under Content/Data/Quests.
 */
UCLASS(Blueprintable, BlueprintType)
class CONSTELLATION_API UQuestDefinition : public UDataAsset
{
	GENERATED_BODY()

public:
	/** Unique identifier for this quest. Must be unique across the whole UQuestDatabase. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	FName QuestID;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	EQuestType Type = EQuestType::Sub;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	FText Title;

	/** Shown once the quest reaches Available. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	FText Description;

	/** While Locked, a Hidden quest is excluded from search/minimap results entirely (not shown as "???"). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	bool bHidden = false;

	/** Ordered progress steps. ProgressSteps[Progress - 1] is the current step (objective/description/inner-progress/markers). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	TArray<FQuestProgressStepDef> ProgressSteps;

	/** Other quests that must be Complete before this one can unlock. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	TArray<FName> RequiredCompletedQuestIDs;

	/** Possible outcomes selectable when this quest completes. Leave empty for a quest with a single, implicit ending. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	TArray<FQuestEndingDef> PossibleEndings;

	/**
	 * Extra unlock condition evaluated alongside RequiredCompletedQuestIDs. Defaults to true;
	 * override in a Blueprint child class of this asset for conditions other than quest prerequisites
	 * (player level, item owned, world state, etc).
	 */
	UFUNCTION(BlueprintNativeEvent, Category = "Quest")
	bool CheckCustomUnlockCondition(const UObject* WorldContextObject) const;
	virtual bool CheckCustomUnlockCondition_Implementation(const UObject* WorldContextObject) const { return true; }

	/** Looks up the display text for a given ending, or an empty FText if EndingID isn't found. */
	FText FindEndingText(FName EndingID) const;
};
