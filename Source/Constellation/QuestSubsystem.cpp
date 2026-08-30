// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestSubsystem.h"
#include "ConstellationSaveGame.h"
#include "QuestDatabase.h"
#include "QuestDefinition.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "UObject/UObjectGlobals.h"
#include "Kismet/GameplayStatics.h"

const FString UQuestSubsystem::SaveSlotName = TEXT("ConstellationSaveGame");
const TCHAR* UQuestSubsystem::DefaultDatabasePath = TEXT("/Game/Data/Quests/DA_QuestDatabase.DA_QuestDatabase");

namespace
{
	/** Resolves the entry for the given 1-based Progress (0 before the quest starts) from a per-step text array, clamped to a valid index. */
	FText GetTextForProgress(const TArray<FText>& PerStepText, int32 Progress)
	{
		if (PerStepText.Num() == 0)
		{
			return FText::GetEmpty();
		}
		const int32 Index = FMath::Clamp(Progress - 1, 0, PerStepText.Num() - 1);
		return PerStepText[Index];
	}
}

void UQuestSubsystem::Initialize(FSubsystemCollectionBase& Collection)
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
		for (const FQuestSaveEntry& Entry : CurrentSaveGame->QuestStates)
		{
			FQuestRuntimeState& RS = RuntimeStates.Add(Entry.QuestID);
			RS.State = Entry.State;
			RS.Progress = Entry.Progress;
			RS.EndingID = Entry.EndingID;
		}
	}

	if (UQuestDatabase* Database = LoadObject<UQuestDatabase>(nullptr, DefaultDatabasePath))
	{
		RegisterQuestDatabase(Database);
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("UQuestSubsystem: no quest database found at %s. Quests will stay Locked until RegisterQuestDatabase is called."), DefaultDatabasePath);
	}

	AutoPickTrackedQuestIfNeeded();
}

void UQuestSubsystem::RegisterQuestDatabase(UQuestDatabase* Database)
{
	if (!Database)
	{
		return;
	}

	for (UQuestDefinition* Quest : Database->Quests)
	{
		if (!Quest || Quest->QuestID.IsNone())
		{
			continue;
		}
		QuestDefinitions.Add(Quest->QuestID, Quest);
	}

	EvaluateAllLockedQuests();
}

void UQuestSubsystem::EvaluateAllLockedQuests()
{
	for (const auto& Pair : QuestDefinitions)
	{
		if (GetQuestState(Pair.Key) == EQuestState::Locked)
		{
			TryUnlockQuest(Pair.Key);
		}
	}
}

const UQuestDefinition* UQuestSubsystem::FindQuestDefinition(FName QuestID) const
{
	if (const TObjectPtr<UQuestDefinition>* Found = QuestDefinitions.Find(QuestID))
	{
		return *Found;
	}
	return nullptr;
}

bool UQuestSubsystem::IsUnlockConditionMet(const UQuestDefinition* Quest) const
{
	if (!Quest)
	{
		return false;
	}

	for (const FName& RequiredID : Quest->RequiredCompletedQuestIDs)
	{
		if (GetQuestState(RequiredID) != EQuestState::Complete)
		{
			return false;
		}
	}

	return Quest->CheckCustomUnlockCondition(GetGameInstance());
}

EQuestState UQuestSubsystem::GetQuestState(FName QuestID) const
{
	if (const FQuestRuntimeState* RS = RuntimeStates.Find(QuestID))
	{
		return RS->State;
	}
	return EQuestState::Locked;
}

int32 UQuestSubsystem::GetQuestProgress(FName QuestID) const
{
	if (const FQuestRuntimeState* RS = RuntimeStates.Find(QuestID))
	{
		return RS->Progress;
	}
	return 0;
}

int32 UQuestSubsystem::GetQuestInnerProgress(FName QuestID) const
{
	if (const FQuestRuntimeState* RS = RuntimeStates.Find(QuestID))
	{
		return RS->InnerProgress;
	}
	return 0;
}

FName UQuestSubsystem::GetQuestEnding(FName QuestID) const
{
	if (const FQuestRuntimeState* RS = RuntimeStates.Find(QuestID))
	{
		return RS->EndingID;
	}
	return NAME_None;
}

void UQuestSubsystem::SetQuestState(FName QuestID, EQuestState NewState)
{
	FQuestRuntimeState& RS = RuntimeStates.FindOrAdd(QuestID);
	const EQuestState OldState = RS.State;
	RS.State = NewState;

	OnQuestStateChanged.Broadcast(QuestID, OldState, NewState);
	SaveToDisk();
}

bool UQuestSubsystem::TryUnlockQuest(FName QuestID)
{
	const UQuestDefinition* Quest = FindQuestDefinition(QuestID);
	if (!Quest || GetQuestState(QuestID) != EQuestState::Locked)
	{
		return false;
	}

	if (!IsUnlockConditionMet(Quest))
	{
		return false;
	}

	SetQuestState(QuestID, EQuestState::Available);
	return true;
}

bool UQuestSubsystem::AcceptQuest(FName QuestID)
{
	if (GetQuestState(QuestID) != EQuestState::Available)
	{
		return false;
	}

	FQuestRuntimeState& RS = RuntimeStates.FindOrAdd(QuestID);
	RS.State = EQuestState::Progressed;
	RS.Progress = 1;
	RS.InnerProgress = 0;

	OnQuestStateChanged.Broadcast(QuestID, EQuestState::Available, EQuestState::Progressed);
	OnQuestProgressChanged.Broadcast(QuestID, RS.Progress);
	AutoPickTrackedQuestIfNeeded();
	SaveToDisk();
	return true;
}

bool UQuestSubsystem::AdvanceQuestProgress(FName QuestID)
{
	const UQuestDefinition* Quest = FindQuestDefinition(QuestID);
	if (!Quest || GetQuestState(QuestID) != EQuestState::Progressed)
	{
		return false;
	}

	FQuestRuntimeState* RS = RuntimeStates.Find(QuestID);
	if (!RS)
	{
		return false;
	}

	const int32 MaxSteps = Quest->ProgressSteps.Num();
	if (RS->Progress >= MaxSteps)
	{
		return false;
	}

	RS->Progress += 1;
	RS->InnerProgress = 0;
	OnQuestProgressChanged.Broadcast(QuestID, RS->Progress);
	SaveToDisk();
	return true;
}

bool UQuestSubsystem::AdvanceInnerQuestProgress(FName QuestID)
{
	const UQuestDefinition* Quest = FindQuestDefinition(QuestID);
	if (!Quest || GetQuestState(QuestID) != EQuestState::Progressed)
	{
		return false;
	}

	FQuestRuntimeState* RS = RuntimeStates.Find(QuestID);
	if (!RS)
	{
		return false;
	}

	if (!Quest->ProgressSteps.IsValidIndex(RS->Progress - 1))
	{
		return false;
	}

	const int32 MaxInner = Quest->ProgressSteps[RS->Progress - 1].InnerProgressCount;
	if (RS->InnerProgress >= MaxInner)
	{
		return false;
	}

	RS->InnerProgress += 1;
	OnQuestInnerProgressChanged.Broadcast(QuestID, RS->InnerProgress);
	SaveToDisk();
	return true;
}

bool UQuestSubsystem::AddQuestProgress(FName QuestID, int32 Amount)
{
	return SetQuestProgress(QuestID, GetQuestProgress(QuestID) + Amount);
}

bool UQuestSubsystem::AddQuestInnerProgress(FName QuestID, int32 Amount)
{
	return SetQuestInnerProgress(QuestID, GetQuestInnerProgress(QuestID) + Amount);
}

bool UQuestSubsystem::SetQuestProgress(FName QuestID, int32 NewProgress)
{
	const UQuestDefinition* Quest = FindQuestDefinition(QuestID);
	if (!Quest || GetQuestState(QuestID) != EQuestState::Progressed)
	{
		return false;
	}

	FQuestRuntimeState* RS = RuntimeStates.Find(QuestID);
	if (!RS)
	{
		return false;
	}

	const int32 MaxSteps = Quest->ProgressSteps.Num();
	if (MaxSteps <= 0)
	{
		return false;
	}

	const int32 Clamped = FMath::Clamp(NewProgress, 1, MaxSteps);
	if (Clamped == RS->Progress)
	{
		return false;
	}

	RS->Progress = Clamped;
	RS->InnerProgress = 0;
	OnQuestProgressChanged.Broadcast(QuestID, RS->Progress);
	SaveToDisk();
	return true;
}

bool UQuestSubsystem::SetQuestInnerProgress(FName QuestID, int32 NewInnerProgress)
{
	const UQuestDefinition* Quest = FindQuestDefinition(QuestID);
	if (!Quest || GetQuestState(QuestID) != EQuestState::Progressed)
	{
		return false;
	}

	FQuestRuntimeState* RS = RuntimeStates.Find(QuestID);
	if (!RS)
	{
		return false;
	}

	if (!Quest->ProgressSteps.IsValidIndex(RS->Progress - 1))
	{
		return false;
	}

	const int32 MaxInner = Quest->ProgressSteps[RS->Progress - 1].InnerProgressCount;
	if (MaxInner <= 0)
	{
		return false;
	}

	const int32 Clamped = FMath::Clamp(NewInnerProgress, 0, MaxInner);
	if (Clamped == RS->InnerProgress)
	{
		return false;
	}

	RS->InnerProgress = Clamped;
	OnQuestInnerProgressChanged.Broadcast(QuestID, RS->InnerProgress);
	SaveToDisk();
	return true;
}

bool UQuestSubsystem::CompleteQuest(FName QuestID, FName EndingID)
{
	if (GetQuestState(QuestID) != EQuestState::Progressed)
	{
		return false;
	}

	FQuestRuntimeState* RS = RuntimeStates.Find(QuestID);
	if (!RS)
	{
		return false;
	}

	RS->State = EQuestState::Complete;
	RS->EndingID = EndingID;

	OnQuestStateChanged.Broadcast(QuestID, EQuestState::Progressed, EQuestState::Complete);
	OnQuestCompleted.Broadcast(QuestID, EndingID);
	AutoPickTrackedQuestIfNeeded();
	SaveToDisk();
	return true;
}

FQuestDisplayInfo UQuestSubsystem::GetQuestDisplayInfo(FName QuestID) const
{
	FQuestDisplayInfo Info;
	Info.QuestID = QuestID;

	const UQuestDefinition* Quest = FindQuestDefinition(QuestID);
	if (!Quest)
	{
		Info.bVisible = false;
		return Info;
	}

	Info.Type = Quest->Type;
	Info.State = GetQuestState(QuestID);
	Info.MaxProgress = Quest->ProgressSteps.Num();

	switch (Info.State)
	{
	case EQuestState::Locked:
		Info.bVisible = !Quest->bHidden;
		Info.Title = FText::FromString(TEXT("???"));
		Info.Description = FText::FromString(TEXT("???"));
		break;

	case EQuestState::Available:
		Info.bVisible = true;
		Info.Title = Quest->Title;
		Info.Description = GetTextForProgress(Quest->Description, Info.Progress);
		break;

	case EQuestState::Progressed:
	{
		Info.bVisible = true;
		Info.Title = Quest->Title;
		Info.Progress = GetQuestProgress(QuestID);
		Info.Description = GetTextForProgress(Quest->Description, Info.Progress);
		Info.CurrentObjectiveText = GetTextForProgress(Quest->Objective, Info.Progress);
		if (Quest->ProgressSteps.IsValidIndex(Info.Progress - 1))
		{
			const FQuestProgressStepDef& Step = Quest->ProgressSteps[Info.Progress - 1];
			Info.CurrentStepDescription = Step.Description;
			Info.MaxInnerProgress = Step.InnerProgressCount;
			Info.TargetPositions = Step.TargetPositions;
		}
		Info.InnerProgress = GetQuestInnerProgress(QuestID);
		break;
	}

	case EQuestState::Complete:
	{
		Info.bVisible = true;
		Info.Title = Quest->Title;
		Info.Progress = GetQuestProgress(QuestID);
		Info.Description = GetTextForProgress(Quest->Description, Info.Progress);
		Info.EndingID = GetQuestEnding(QuestID);
		Info.EndingText = Quest->FindEndingText(Info.EndingID);
		break;
	}
	}

	return Info;
}

bool UQuestSubsystem::SetTrackedQuest(FName QuestID)
{
	if (GetQuestState(QuestID) != EQuestState::Progressed)
	{
		return false;
	}

	if (TrackedQuestID != QuestID)
	{
		TrackedQuestID = QuestID;
		OnTrackedQuestChanged.Broadcast(TrackedQuestID);
	}
	return true;
}

FName UQuestSubsystem::GetTrackedQuestID() const
{
	return TrackedQuestID;
}

FQuestDisplayInfo UQuestSubsystem::GetTrackedQuestDisplayInfo() const
{
	return GetQuestDisplayInfo(TrackedQuestID);
}

void UQuestSubsystem::AutoPickTrackedQuestIfNeeded()
{
	if (!TrackedQuestID.IsNone() && GetQuestState(TrackedQuestID) == EQuestState::Progressed)
	{
		return;
	}

	const FName OldTrackedQuestID = TrackedQuestID;
	TrackedQuestID = NAME_None;

	// Prefer a Main-type quest so the primary story thread wins over side content.
	for (const auto& Pair : RuntimeStates)
	{
		if (Pair.Value.State != EQuestState::Progressed)
		{
			continue;
		}
		const UQuestDefinition* Quest = FindQuestDefinition(Pair.Key);
		if (Quest && Quest->Type == EQuestType::Main)
		{
			TrackedQuestID = Pair.Key;
			break;
		}
	}

	if (TrackedQuestID.IsNone())
	{
		for (const auto& Pair : RuntimeStates)
		{
			if (Pair.Value.State == EQuestState::Progressed)
			{
				TrackedQuestID = Pair.Key;
				break;
			}
		}
	}

	if (TrackedQuestID != OldTrackedQuestID)
	{
		OnTrackedQuestChanged.Broadcast(TrackedQuestID);
	}
}

TArray<FName> UQuestSubsystem::GetSearchableQuestIDs(bool bFilterByType, EQuestType TypeFilter) const
{
	TArray<FName> Result;
	for (const auto& Pair : QuestDefinitions)
	{
		const UQuestDefinition* Quest = Pair.Value;
		if (!Quest)
		{
			continue;
		}
		if (bFilterByType && Quest->Type != TypeFilter)
		{
			continue;
		}

		const EQuestState State = GetQuestState(Pair.Key);
		if (State == EQuestState::Locked && Quest->bHidden)
		{
			continue;
		}

		Result.Add(Pair.Key);
	}
	return Result;
}

void UQuestSubsystem::SaveToDisk()
{
	if (!CurrentSaveGame)
	{
		CurrentSaveGame = Cast<UConstellationSaveGame>(UGameplayStatics::CreateSaveGameObject(UConstellationSaveGame::StaticClass()));
	}
	if (!CurrentSaveGame)
	{
		return;
	}

	TArray<FQuestSaveEntry> Entries;
	Entries.Reserve(RuntimeStates.Num());
	for (const auto& Pair : RuntimeStates)
	{
		FQuestSaveEntry Entry;
		Entry.QuestID = Pair.Key;
		Entry.State = Pair.Value.State;
		Entry.Progress = Pair.Value.Progress;
		Entry.EndingID = Pair.Value.EndingID;
		Entries.Add(Entry);
	}

	CurrentSaveGame->QuestStates = Entries;
	UGameplayStatics::SaveGameToSlot(CurrentSaveGame, SaveSlotName, SaveUserIndex);
}

bool UQuestSubsystem::TryUnlockQuestFor(const UObject* WorldContextObject, FName QuestID)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->TryUnlockQuest(QuestID);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::AcceptQuestFor(const UObject* WorldContextObject, FName QuestID)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->AcceptQuest(QuestID);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::AdvanceQuestProgressFor(const UObject* WorldContextObject, FName QuestID)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->AdvanceQuestProgress(QuestID);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::CompleteQuestFor(const UObject* WorldContextObject, FName QuestID, FName EndingID)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->CompleteQuest(QuestID, EndingID);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::AdvanceInnerQuestProgressFor(const UObject* WorldContextObject, FName QuestID)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->AdvanceInnerQuestProgress(QuestID);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::AddQuestProgressFor(const UObject* WorldContextObject, FName QuestID, int32 Amount)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->AddQuestProgress(QuestID, Amount);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::AddQuestInnerProgressFor(const UObject* WorldContextObject, FName QuestID, int32 Amount)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->AddQuestInnerProgress(QuestID, Amount);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::SetQuestProgressFor(const UObject* WorldContextObject, FName QuestID, int32 NewProgress)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->SetQuestProgress(QuestID, NewProgress);
			}
		}
	}
	return false;
}

bool UQuestSubsystem::SetQuestInnerProgressFor(const UObject* WorldContextObject, FName QuestID, int32 NewInnerProgress)
{
	if (!WorldContextObject) return false;
	if (const UWorld* World = WorldContextObject->GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				return Sub->SetQuestInnerProgress(QuestID, NewInnerProgress);
			}
		}
	}
	return false;
}

FQuestDisplayInfo UQuestSubsystem::GetQuestDisplayInfoFor(const UObject* WorldContextObject, FName QuestID)
{
	if (WorldContextObject)
	{
		if (const UWorld* World = WorldContextObject->GetWorld())
		{
			if (UGameInstance* GI = World->GetGameInstance())
			{
				if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
				{
					return Sub->GetQuestDisplayInfo(QuestID);
				}
			}
		}
	}
	return FQuestDisplayInfo();
}
