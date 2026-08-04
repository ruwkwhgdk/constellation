// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "ConstellationSaveGame.generated.h"

/**
 * The game's persistent save data. Currently only holds StarCoin progress;
 * extend with additional fields as more systems need to persist.
 */
UCLASS()
class CONSTELLATION_API UConstellationSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
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
};
