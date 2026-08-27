// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "QuestTargetMarker.generated.h"

class UQuestDefinition;

/**
 * Editor-only placement aid for authoring FQuestProgressStepDef::TargetPositions visually.
 * Place one in the level per progress step, drag its Points widgets in the Level Viewport to the
 * desired guidance-marker locations, then press "Sync To Quest" to bake the current world-space
 * positions into the QuestDefinition asset (and keep InnerProgressCount in sync with them).
 *
 * Points are edited in this actor's local space (like BP_Monster_Patrol's PatrolPositions) and
 * converted to world space only when synced. Purely a design-time tool — never spawned at runtime.
 */
UCLASS(Blueprintable)
class CONSTELLATION_API AQuestTargetMarker : public AActor
{
	GENERATED_BODY()

public:
	AQuestTargetMarker();

	/** Quest asset whose progress step this marker feeds. */
	UPROPERTY(EditAnywhere, Category = "Quest Target Marker")
	TObjectPtr<UQuestDefinition> Quest;

	/** 1-based progress step to write into (matches FQuestDisplayInfo::Progress). */
	UPROPERTY(EditAnywhere, Category = "Quest Target Marker", meta = (ClampMin = "1"))
	int32 StepIndex = 1;

	/** Guidance marker locations, edited here in this actor's local space via the viewport widgets. */
	UPROPERTY(EditAnywhere, Category = "Quest Target Marker", meta = (MakeEditWidget = true))
	TArray<FVector> Points;

	/**
	 * Writes Points (converted to world space) into Quest->ProgressSteps[StepIndex - 1].TargetPositions
	 * and sets that step's InnerProgressCount to match. No-ops with a log warning if Quest is unset or
	 * StepIndex is out of range.
	 */
	UFUNCTION(CallInEditor, Category = "Quest Target Marker")
	void SyncToQuest();
};
