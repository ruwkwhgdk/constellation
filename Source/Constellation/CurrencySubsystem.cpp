// Fill out your copyright notice in the Description page of Project Settings.


#include "CurrencySubsystem.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"

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
