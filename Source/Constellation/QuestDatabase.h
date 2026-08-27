// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "QuestDatabase.generated.h"

class UQuestDefinition;

/**
 * The full catalog of quests in the game. Author a single instance of this asset
 * (by convention at /Game/Data/Quests/DA_QuestDatabase) and list every UQuestDefinition in it;
 * UQuestSubsystem auto-loads it from that path on startup.
 */
UCLASS(BlueprintType)
class CONSTELLATION_API UQuestDatabase : public UDataAsset
{
	GENERATED_BODY()

public:
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Quest")
	TArray<TObjectPtr<UQuestDefinition>> Quests;
};
