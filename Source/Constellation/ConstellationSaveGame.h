// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "QuestTypes.h"
#include "SceneEventSaveData.h"
#include "ConstellationSaveGame.generated.h"

/**
 * Shared persistent currency, collection, chest and quest data.
 */
UCLASS()
class CONSTELLATION_API UConstellationSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
 UPROPERTY() FSceneEventSaveData SceneEvents;
	UPROPERTY()
	int32 StarCoin = 0;

	/** Stable per-actor IDs (AActor::GetName()) of every StarCoin pickup ever collected. */
	UPROPERTY()
	TArray<FString> CollectedStarCoinIDs;

	UPROPERTY()
	int32 DummyItemCount = 0;

	/** Stable per-actor IDs (AActor::GetName()) of every chest that has been opened. */
	UPROPERTY()
	TArray<FString> OpenedChestIDs;

	/** Runtime state including main and inner progress for quests that have left Locked. */
	UPROPERTY()
	TArray<FQuestSaveEntry> QuestStates;
};
