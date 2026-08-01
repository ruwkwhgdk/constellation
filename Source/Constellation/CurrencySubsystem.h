// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CurrencySubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnGoldChanged, int32, NewGold);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnStarCoinChanged, int32, NewStarCoin);

/**
 * Holds the player's currency balances (Gold, StarCoin) for the lifetime of the GameInstance,
 * so it survives level travel. Retrieve it from any Blueprint via
 * "Get Game Instance" -> "Get Subsystem (Currency Subsystem)".
 */
UCLASS()
class CONSTELLATION_API UCurrencySubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Anywhere-callable helper: adds Gold without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Currency|StarCoin", meta = (WorldContext = "WorldContextObject"))
	static void AddStarCoinTo(const UObject* WorldContextObject, int32 Amount);

	/** Anywhere-callable helper: adds Gold without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Currency|Gold", meta = (WorldContext = "WorldContextObject"))
	static void AddGoldTo(const UObject* WorldContextObject, int32 Amount);

	/** Broadcast whenever the Gold balance changes. */
	UPROPERTY(BlueprintAssignable, Category = "Currency|Gold")
	FOnGoldChanged OnGoldChanged;

	/** Broadcast whenever the StarCoin balance changes. */
	UPROPERTY(BlueprintAssignable, Category = "Currency|StarCoin")
	FOnStarCoinChanged OnStarCoinChanged;

	/** Adds Amount to the player's Gold balance. Amount must be positive. */
	UFUNCTION(BlueprintCallable, Category = "Currency|Gold")
	void AddGold(int32 Amount);

	/** Attempts to spend Amount Gold. Returns false and makes no change if the balance is insufficient. */
	UFUNCTION(BlueprintCallable, Category = "Currency|Gold")
	bool TrySpendGold(int32 Amount);

	UFUNCTION(BlueprintPure, Category = "Currency|Gold")
	int32 GetGold() const { return Gold; }

	/** Adds Amount to the player's StarCoin balance. Amount must be positive. */
	UFUNCTION(BlueprintCallable, Category = "Currency|StarCoin")
	void AddStarCoin(int32 Amount);

	/** Attempts to spend Amount StarCoin. Returns false and makes no change if the balance is insufficient. */
	UFUNCTION(BlueprintCallable, Category = "Currency|StarCoin")
	bool TrySpendStarCoin(int32 Amount);

	UFUNCTION(BlueprintPure, Category = "Currency|StarCoin")
	int32 GetStarCoin() const { return StarCoin; }

protected:
	UPROPERTY(BlueprintReadOnly, Category = "Currency|Gold", meta = (AllowPrivateAccess = "true"))
	int32 Gold = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Currency|StarCoin", meta = (AllowPrivateAccess = "true"))
	int32 StarCoin = 0;
};
