// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "QuestTypes.generated.h"

/** Broad category a quest belongs to. Metadata only — carries no gameplay rules of its own. */
UENUM(BlueprintType)
enum class EQuestType : uint8
{
	Epic,
	Main,
	Sub
};

/**
 * A quest's lifecycle stage. Progress only ever moves forward:
 * Locked -> Available -> Progressed -> Complete.
 */
UENUM(BlueprintType)
enum class EQuestState : uint8
{
	/** Conditions not met yet. Obfuscated as "???"; excluded from search entirely if the quest is Hidden. */
	Locked,
	/** Unlocked but not yet accepted. Basic info (Title/Description) is visible; objectives/progress are hidden. */
	Available,
	/** Accepted and ongoing. Progress starts at 1 and only increases. */
	Progressed,
	/** Finished. The specific outcome is recorded in EndingID. */
	Complete
};

/** One possible outcome of a quest, chosen when the quest is completed. */
USTRUCT(BlueprintType)
struct FQuestEndingDef
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	FName EndingID;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	FText EndingTitle;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	FText EndingDescription;
};

/**
 * Designer-authored definition of a single main-progress step (one entry per Progress value).
 * A step can carry its own sub-progress ("inner progress"): e.g. a step reading "Collect 3 flowers"
 * has InnerProgressCount = 3, one TargetPositions entry per flower for on-screen guidance markers.
 * TargetPositions should have InnerProgressCount entries; leave both at 0/empty for a step with no
 * sub-progress tracking (AdvanceQuestProgress alone carries it to Complete/next step).
 */
USTRUCT(BlueprintType)
struct FQuestProgressStepDef
{
	GENERATED_BODY()

	/** Additional flavor/context text for this step. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	FText Description;

	/** Number of inner sub-progress units this step is divided into. Should match TargetPositions.Num(). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	int32 InnerProgressCount = 0;

	/** World-space marker locations, one per inner sub-progress unit, for on-screen guidance. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	TArray<FVector> TargetPositions;
};

/**
 * UI-ready snapshot of a single quest, with all Locked/Available obfuscation already applied.
 * Widgets should render this directly rather than branching on EQuestState themselves.
 */
USTRUCT(BlueprintType)
struct FQuestDisplayInfo
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	FName QuestID;

	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	EQuestType Type = EQuestType::Sub;

	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	EQuestState State = EQuestState::Locked;

	/** False only when the quest is Locked and marked Hidden — search/minimap should omit it entirely. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	bool bVisible = true;

	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	FText Title;

	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	FText Description;

	/** Text for the quest's current objective step. Empty unless the quest is Progressed. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	FText CurrentObjectiveText;

	/** Flavor/context text for the quest's current step. Empty unless the quest is Progressed. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	FText CurrentStepDescription;

	/** Current progress step (1-based). 0 unless the quest is Progressed or Complete. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	int32 Progress = 0;

	/** Total number of progress steps defined for this quest. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	int32 MaxProgress = 0;

	/** Current step's inner sub-progress. 0 unless the quest is Progressed and the current step tracks sub-progress. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	int32 InnerProgress = 0;

	/** Current step's total inner sub-progress units (from the step definition). 0 if the step has none. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	int32 MaxInnerProgress = 0;

	/** Current step's guidance marker locations (world space), one per inner sub-progress unit. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	TArray<FVector> TargetPositions;

	/** Set once the quest is Complete. */
	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	FName EndingID;

	UPROPERTY(BlueprintReadOnly, Category = "Quest")
	FText EndingText;
};

/** Persisted row for a single quest's runtime state. Only quests that have left Locked need an entry. */
USTRUCT()
struct FQuestSaveEntry
{
	GENERATED_BODY()

	UPROPERTY()
	FName QuestID;

	UPROPERTY()
	EQuestState State = EQuestState::Locked;

	UPROPERTY()
	int32 Progress = 0;

	UPROPERTY()
	FName EndingID;
};

/** In-memory runtime state for a single quest. Not a USTRUCT — internal to UQuestSubsystem. */
struct FQuestRuntimeState
{
	EQuestState State = EQuestState::Locked;
	int32 Progress = 0;
	int32 InnerProgress = 0;
	FName EndingID;
};
