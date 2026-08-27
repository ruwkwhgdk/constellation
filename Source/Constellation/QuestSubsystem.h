// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "QuestTypes.h"
#include "QuestSubsystem.generated.h"

class UConstellationSaveGame;
class UQuestDatabase;
class UQuestDefinition;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnQuestStateChanged, FName, QuestID, EQuestState, OldState, EQuestState, NewState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnQuestProgressChanged, FName, QuestID, int32, NewProgress);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnQuestInnerProgressChanged, FName, QuestID, int32, NewInnerProgress);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnQuestCompleted, FName, QuestID, FName, EndingID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTrackedQuestChanged, FName, NewTrackedQuestID);

/**
 * Owns runtime quest state (Locked/Available/Progressed/Complete + Progress/Ending) for the lifetime
 * of the GameInstance, persisting it into the shared ConstellationSaveGame slot. Retrieve it from any
 * Blueprint via "Get Game Instance" -> "Get Subsystem (Quest Subsystem)", or use the anywhere-callable
 * static helpers below.
 *
 * Quests are authored as UQuestDefinition data assets, cataloged in a single UQuestDatabase asset that
 * this subsystem auto-loads from /Game/Data/Quests/DA_QuestDatabase on Initialize.
 */
UCLASS()
class CONSTELLATION_API UQuestSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Loads every UQuestDefinition from Database into the catalog, then re-evaluates unlocks for all Locked quests. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	void RegisterQuestDatabase(UQuestDatabase* Database);

	/** Current lifecycle stage of QuestID. Unknown quests report Locked. */
	UFUNCTION(BlueprintPure, Category = "Quest")
	EQuestState GetQuestState(FName QuestID) const;

	/** Current progress step (1-based). 0 if the quest hasn't been accepted (or doesn't exist). */
	UFUNCTION(BlueprintPure, Category = "Quest")
	int32 GetQuestProgress(FName QuestID) const;

	/** Current step's inner sub-progress. 0 if the quest hasn't been accepted (or doesn't exist). */
	UFUNCTION(BlueprintPure, Category = "Quest")
	int32 GetQuestInnerProgress(FName QuestID) const;

	/** Ending recorded when the quest completed. NAME_None if not yet Complete. */
	UFUNCTION(BlueprintPure, Category = "Quest")
	FName GetQuestEnding(FName QuestID) const;

	/** Attempts Locked -> Available. Returns false if prerequisites/custom condition aren't met, or the quest isn't Locked. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	bool TryUnlockQuest(FName QuestID);

	/** Attempts Available -> Progressed(1). Returns false if the quest isn't currently Available. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	bool AcceptQuest(FName QuestID);

	/** Attempts Progressed(N) -> Progressed(N+1), clamped to the quest's number of progress steps. Resets InnerProgress to 0. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	bool AdvanceQuestProgress(FName QuestID);

	/** Attempts InnerProgress -> InnerProgress+1 within the current step, clamped to that step's InnerProgressCount. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	bool AdvanceInnerQuestProgress(FName QuestID);

	/** Attempts Progressed -> Complete, recording EndingID. Returns false if the quest isn't currently Progressed. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	bool CompleteQuest(FName QuestID, FName EndingID);

	/** UI-ready snapshot of QuestID with Locked/Available obfuscation already applied. */
	UFUNCTION(BlueprintPure, Category = "Quest")
	FQuestDisplayInfo GetQuestDisplayInfo(FName QuestID) const;

	/**
	 * Pins QuestID as the single quest shown by tracker UI (e.g. a bottom-left HUD panel). Must
	 * currently be Progressed. Returns false (no change) otherwise. Cleared automatically to another
	 * Progressed quest (or NAME_None) whenever the tracked quest completes.
	 */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	bool SetTrackedQuest(FName QuestID);

	/** QuestID of the current tracker-UI quest, or NAME_None if no quest is Progressed. */
	UFUNCTION(BlueprintPure, Category = "Quest")
	FName GetTrackedQuestID() const;

	/** UI-ready snapshot of the current tracked quest. bVisible is false when nothing is tracked. */
	UFUNCTION(BlueprintPure, Category = "Quest")
	FQuestDisplayInfo GetTrackedQuestDisplayInfo() const;

	/** All quest IDs visible in search/minimap (excludes Locked+Hidden quests), optionally filtered by Type. */
	UFUNCTION(BlueprintPure, Category = "Quest")
	TArray<FName> GetSearchableQuestIDs(bool bFilterByType, EQuestType TypeFilter) const;

	/** Anywhere-callable helper: unlocks a quest without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Quest", meta = (WorldContext = "WorldContextObject"))
	static bool TryUnlockQuestFor(const UObject* WorldContextObject, FName QuestID);

	/** Anywhere-callable helper: accepts a quest without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Quest", meta = (WorldContext = "WorldContextObject"))
	static bool AcceptQuestFor(const UObject* WorldContextObject, FName QuestID);

	/** Anywhere-callable helper: advances a quest's progress without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Quest", meta = (WorldContext = "WorldContextObject"))
	static bool AdvanceQuestProgressFor(const UObject* WorldContextObject, FName QuestID);

	/** Anywhere-callable helper: advances a quest's inner progress without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Quest", meta = (WorldContext = "WorldContextObject"))
	static bool AdvanceInnerQuestProgressFor(const UObject* WorldContextObject, FName QuestID);

	/** Anywhere-callable helper: completes a quest without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintCallable, Category = "Quest", meta = (WorldContext = "WorldContextObject"))
	static bool CompleteQuestFor(const UObject* WorldContextObject, FName QuestID, FName EndingID);

	/** Anywhere-callable helper: fetches a quest's display info without needing a Get Subsystem node in BP. */
	UFUNCTION(BlueprintPure, Category = "Quest", meta = (WorldContext = "WorldContextObject"))
	static FQuestDisplayInfo GetQuestDisplayInfoFor(const UObject* WorldContextObject, FName QuestID);

	/** Broadcast whenever a quest's EQuestState changes. */
	UPROPERTY(BlueprintAssignable, Category = "Quest")
	FOnQuestStateChanged OnQuestStateChanged;

	/** Broadcast whenever a Progressed quest's Progress value increases. */
	UPROPERTY(BlueprintAssignable, Category = "Quest")
	FOnQuestProgressChanged OnQuestProgressChanged;

	/** Broadcast whenever a Progressed quest's InnerProgress value increases. */
	UPROPERTY(BlueprintAssignable, Category = "Quest")
	FOnQuestInnerProgressChanged OnQuestInnerProgressChanged;

	/** Broadcast whenever a quest reaches Complete. */
	UPROPERTY(BlueprintAssignable, Category = "Quest")
	FOnQuestCompleted OnQuestCompleted;

	/** Broadcast whenever the tracker-UI quest changes (explicit SetTrackedQuest, auto-pick, or cleared to NAME_None). */
	UPROPERTY(BlueprintAssignable, Category = "Quest")
	FOnTrackedQuestChanged OnTrackedQuestChanged;

private:
	void SetQuestState(FName QuestID, EQuestState NewState);
	void EvaluateAllLockedQuests();
	bool IsUnlockConditionMet(const UQuestDefinition* Quest) const;
	const UQuestDefinition* FindQuestDefinition(FName QuestID) const;
	void SaveToDisk();
	/** Re-validates TrackedQuestID, picking another Progressed quest (Main-type preferred) if it's no longer valid. */
	void AutoPickTrackedQuestIfNeeded();

	static const FString SaveSlotName;
	static constexpr int32 SaveUserIndex = 0;
	static const TCHAR* DefaultDatabasePath;

	UPROPERTY(Transient)
	TObjectPtr<UConstellationSaveGame> CurrentSaveGame = nullptr;

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UQuestDefinition>> QuestDefinitions;

	TMap<FName, FQuestRuntimeState> RuntimeStates;

	/** QuestID of the quest tracker UI should show. NAME_None if no quest is Progressed. Not persisted. */
	UPROPERTY(Transient)
	FName TrackedQuestID;
};
