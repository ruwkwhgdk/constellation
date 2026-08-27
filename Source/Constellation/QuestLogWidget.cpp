// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestLogWidget.h"
#include "QuestSubsystem.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"

void UQuestLogWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.AddDynamic(this, &UQuestLogWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.AddDynamic(this, &UQuestLogWidget::HandleQuestProgressChanged);
				Sub->OnQuestCompleted.AddDynamic(this, &UQuestLogWidget::HandleQuestCompleted);
			}
		}
	}

	RefreshQuestList();
}

void UQuestLogWidget::NativeDestruct()
{
	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.RemoveDynamic(this, &UQuestLogWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.RemoveDynamic(this, &UQuestLogWidget::HandleQuestProgressChanged);
				Sub->OnQuestCompleted.RemoveDynamic(this, &UQuestLogWidget::HandleQuestCompleted);
			}
		}
	}

	Super::NativeDestruct();
}

void UQuestLogWidget::RefreshQuestList()
{
	TArray<FQuestDisplayInfo> Quests;

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				for (FName QuestID : Sub->GetSearchableQuestIDs(false, EQuestType::Sub))
				{
					Quests.Add(Sub->GetQuestDisplayInfo(QuestID));
				}
			}
		}
	}

	OnQuestListRefreshed(Quests);
}

void UQuestLogWidget::HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState)
{
	RefreshQuestList();
}

void UQuestLogWidget::HandleQuestProgressChanged(FName QuestID, int32 NewProgress)
{
	RefreshQuestList();
}

void UQuestLogWidget::HandleQuestCompleted(FName QuestID, FName EndingID)
{
	RefreshQuestList();
}
