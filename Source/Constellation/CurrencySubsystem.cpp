// Fill out your copyright notice in the Description page of Project Settings.


#include "CurrencySubsystem.h"
#include "ConstellationSaveGame.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"

const FString UCurrencySubsystem::SaveSlotName = TEXT("ConstellationSaveGame");

void UCurrencySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	UConstellationSaveGame* Loaded = nullptr;
	if (UGameplayStatics::DoesSaveGameExist(SaveSlotName, SaveUserIndex))
	{
		Loaded = Cast<UConstellationSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName, SaveUserIndex));
	}
	if (!Loaded)
	{
		Loaded = Cast<UConstellationSaveGame>(UGameplayStatics::CreateSaveGameObject(UConstellationSaveGame::StaticClass()));
	}
	CurrentSaveGame = Loaded;

	if (CurrentSaveGame)
	{
		StarCoin = CurrentSaveGame->StarCoin;
		CollectedStarCoinIDs = CurrentSaveGame->CollectedStarCoinIDs;
		DummyItemCount = CurrentSaveGame->DummyItemCount;
		OpenedChestIDs = CurrentSaveGame->OpenedChestIDs;
	}
}

void UCurrencySubsystem::SaveToDisk()
{
	if (!CurrentSaveGame)
	{
		CurrentSaveGame = Cast<UConstellationSaveGame>(UGameplayStatics::CreateSaveGameObject(UConstellationSaveGame::StaticClass()));
	}
	if (!CurrentSaveGame)
	{
		return;
	}

	CurrentSaveGame->StarCoin = StarCoin;
	CurrentSaveGame->CollectedStarCoinIDs = CollectedStarCoinIDs;
	CurrentSaveGame->DummyItemCount = DummyItemCount;
	CurrentSaveGame->OpenedChestIDs = OpenedChestIDs;
	UGameplayStatics::SaveGameToSlot(CurrentSaveGame, SaveSlotName, SaveUserIndex);
}

bool UCurrencySubsystem::IsStarCoinIDCollected(const FString& CollectableID) const
{
	return CollectedStarCoinIDs.Contains(CollectableID);
}

void UCurrencySubsystem::MarkStarCoinIDCollected(const FString& CollectableID)
{
	if (CollectableID.IsEmpty() || CollectedStarCoinIDs.Contains(CollectableID))
	{
		return;
	}

	CollectedStarCoinIDs.Add(CollectableID);
	SaveToDisk();
	OnStarCoinCollectionChanged.Broadcast(CollectedStarCoinIDs.Num(), AllStarCoinIDs.Num());
}

void UCurrencySubsystem::RegisterStarCoinID(const FString& CollectableID)
{
	if (CollectableID.IsEmpty() || AllStarCoinIDs.Contains(CollectableID))
	{
		return;
	}

	AllStarCoinIDs.Add(CollectableID);
	OnStarCoinCollectionChanged.Broadcast(CollectedStarCoinIDs.Num(), AllStarCoinIDs.Num());
}

bool UCurrencySubsystem::IsChestIDOpened(const FString& ChestID) const
{
	return OpenedChestIDs.Contains(ChestID);
}

void UCurrencySubsystem::MarkChestIDOpened(const FString& ChestID)
{
	if (ChestID.IsEmpty() || OpenedChestIDs.Contains(ChestID))
	{
		return;
	}

	OpenedChestIDs.Add(ChestID);
	SaveToDisk();
}

bool UCurrencySubsystem::IsStarCoinAlreadyCollected(const AActor* CollectableItem)
{
	if (!CollectableItem)
	{
		return false;
	}
	if (const UWorld* World = CollectableItem->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				return Sub->IsStarCoinIDCollected(CollectableItem->GetName());
			}
		}
	}
	return false;
}

void UCurrencySubsystem::MarkStarCoinCollected(const AActor* CollectableItem)
{
	if (!CollectableItem)
	{
		return;
	}
	if (const UWorld* World = CollectableItem->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				Sub->MarkStarCoinIDCollected(CollectableItem->GetName());
			}
		}
	}
}

void UCurrencySubsystem::RegisterStarCoinPickup(const AActor* CollectableItem)
{
	if (!CollectableItem)
	{
		return;
	}
	if (const UWorld* World = CollectableItem->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				Sub->RegisterStarCoinID(CollectableItem->GetName());
			}
		}
	}
}

bool UCurrencySubsystem::IsChestAlreadyOpened(const AActor* Chest)
{
	if (!Chest)
	{
		return false;
	}
	if (const UWorld* World = Chest->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				return Sub->IsChestIDOpened(Chest->GetName());
			}
		}
	}
	return false;
}

void UCurrencySubsystem::MarkChestOpened(const AActor* Chest)
{
	if (!Chest)
	{
		return;
	}
	if (const UWorld* World = Chest->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				Sub->MarkChestIDOpened(Chest->GetName());
			}
		}
	}
}

void UCurrencySubsystem::AddDummyItemTo(const UObject* WorldContextObject, int32 Amount)
{
	if (!WorldContextObject) return;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				Sub->AddDummyItem(Amount);
			}
		}
	}
}

void UCurrencySubsystem::AddStarCoinTo(const UObject* WorldContextObject, int32 Amount)
{
	if (!WorldContextObject) return;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				Sub->AddStarCoin(Amount);
			}
		}
	}
}

void UCurrencySubsystem::AddGoldTo(const UObject* WorldContextObject, int32 Amount)
{
	if (!WorldContextObject) return;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UCurrencySubsystem* Sub = GI->GetSubsystem<UCurrencySubsystem>())
			{
				Sub->AddGold(Amount);
			}
		}
	}
}

void UCurrencySubsystem::AddGold(int32 Amount)
{
	if (Amount <= 0)
	{
		return;
	}

	Gold += Amount;
	OnGoldChanged.Broadcast(Gold);
}

bool UCurrencySubsystem::TrySpendGold(int32 Amount)
{
	if (Amount <= 0 || Amount > Gold)
	{
		return false;
	}

	Gold -= Amount;
	OnGoldChanged.Broadcast(Gold);
	return true;
}

void UCurrencySubsystem::AddStarCoin(int32 Amount)
{
	if (Amount <= 0)
	{
		return;
	}

	StarCoin += Amount;
	OnStarCoinChanged.Broadcast(StarCoin);
}

bool UCurrencySubsystem::TrySpendStarCoin(int32 Amount)
{
	if (Amount <= 0 || Amount > StarCoin)
	{
		return false;
	}

	StarCoin -= Amount;
	OnStarCoinChanged.Broadcast(StarCoin);
	return true;
}

void UCurrencySubsystem::AddDummyItem(int32 Amount)
{
	if (Amount <= 0)
	{
		return;
	}

	DummyItemCount += Amount;
	OnDummyItemChanged.Broadcast(DummyItemCount);
}
