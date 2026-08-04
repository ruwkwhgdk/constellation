// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CurrencySubsystem.generated.h"

class UConstellationSaveGame;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnGoldChanged, int32, NewGold);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnStarCoinChanged, int32, NewStarCoin);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnStarCoinCollectionChanged, int32, Collected, int32, Total);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDummyItemChanged, int32, NewDummyItemCount);

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
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** True if this StarCoin pickup was already permanently collected in a previous session. */
	UFUNCTION(BlueprintPure, Category = "Currency|StarCoin")
	static bool IsStarCoinAlreadyCollected(const AActor* CollectableItem);

	/** Permanently marks this StarCoin pickup as collected and immediately persists the save. */
	UFUNCTION(BlueprintCallable, Category = "Currency|StarCoin")
	static void MarkStarCoinCollected(const AActor* CollectableItem);

	/** Registers a placed StarCoin pickup so it counts toward the total. Call once from the pickup's BeginPlay. */
	UFUNCTION(BlueprintCallable, Category = "Currency|StarCoin")
	static void RegisterStarCoinPickup(const AActor* CollectableItem);

	/** Number of distinct StarCoin pickups permanently collected so far. */
	UFUNCTION(BlueprintPure, Category = "Currency|StarCoin")
	int32 GetCollectedStarCoinCount() const { return CollectedStarCoinIDs.Num(); }

	/** Number of distinct StarCoin pickups registered (placed) in the game so far. */
	UFUNCTION(BlueprintPure, Category = "Currency|StarCoin")
	int32 GetTotalStarCoinCount() const { return AllStarCoinIDs.Num(); }

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

	/** Broadcast whenever the collected or total StarCoin pickup count changes. */
	UPROPERTY(BlueprintAssignable, Category = "Currency|StarCoin")
	FOnStarCoinCollectionChanged OnStarCoinCollectionChanged;

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

	/** True if this chest was already permanently opened in a previous session. */
	UFUNCTION(BlueprintPure, Category = "Chest")
	static bool IsChestAlreadyOpened(const AActor* Chest);

	/** Permanently marks this chest as opened and immediately persists the save. */
	UFUNCTION(BlueprintCallable, Category = "Chest")
	static void MarkChestOpened(const AActor* Chest);

	/** Anywhere-callable helper: grants dummy items without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Item", meta = (WorldContext = "WorldContextObject"))
	static void AddDummyItemTo(const UObject* WorldContextObject, int32 Amount);

	/** Adds Amount to the player's dummy item count. Amount must be positive. */
	UFUNCTION(BlueprintCallable, Category = "Item")
	void AddDummyItem(int32 Amount);

	UFUNCTION(BlueprintPure, Category = "Item")
	int32 GetDummyItemCount() const { return DummyItemCount; }

	/** Broadcast whenever the dummy item count changes. */
	UPROPERTY(BlueprintAssignable, Category = "Item")
	FOnDummyItemChanged OnDummyItemChanged;

protected:
	UPROPERTY(BlueprintReadOnly, Category = "Currency|Gold", meta = (AllowPrivateAccess = "true"))
	int32 Gold = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Currency|StarCoin", meta = (AllowPrivateAccess = "true"))
	int32 StarCoin = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Item", meta = (AllowPrivateAccess = "true"))
	int32 DummyItemCount = 0;

private:
	bool IsStarCoinIDCollected(const FString& CollectableID) const;
	void MarkStarCoinIDCollected(const FString& CollectableID);
	void RegisterStarCoinID(const FString& CollectableID);
	bool IsChestIDOpened(const FString& ChestID) const;
	void MarkChestIDOpened(const FString& ChestID);
	void SaveToDisk();

	static const FString SaveSlotName;
	static constexpr int32 SaveUserIndex = 0;

	UPROPERTY(Transient)
	TObjectPtr<UConstellationSaveGame> CurrentSaveGame = nullptr;

	TArray<FString> CollectedStarCoinIDs;

	/** Not persisted: rebuilt each session as placed StarCoin pickups call RegisterStarCoinPickup in BeginPlay. */
	TSet<FString> AllStarCoinIDs;

	/** Stable per-actor IDs (AActor::GetName()) of every chest that has been opened. */
	TArray<FString> OpenedChestIDs;
};
