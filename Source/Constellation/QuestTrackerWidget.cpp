// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestTrackerWidget.h"
#include "QuestSubsystem.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"

void UQuestTrackerWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.AddDynamic(this, &UQuestTrackerWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.AddDynamic(this, &UQuestTrackerWidget::HandleQuestProgressChanged);
				Sub->OnQuestInnerProgressChanged.AddDynamic(this, &UQuestTrackerWidget::HandleQuestInnerProgressChanged);
				Sub->OnTrackedQuestChanged.AddDynamic(this, &UQuestTrackerWidget::HandleTrackedQuestChanged);
			}
		}
	}

	RefreshTracker();
}

void UQuestTrackerWidget::NativeDestruct()
{
	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleQuestProgressChanged);
				Sub->OnQuestInnerProgressChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleQuestInnerProgressChanged);
				Sub->OnTrackedQuestChanged.RemoveDynamic(this, &UQuestTrackerWidget::HandleTrackedQuestChanged);
			}
		}
	}

	Super::NativeDestruct();
}

void UQuestTrackerWidget::RefreshTracker()
{
	FQuestDisplayInfo Info;

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Info = Sub->GetTrackedQuestDisplayInfo();
			}
		}
	}

	OnTrackerRefreshed(Info);
}

void UQuestTrackerWidget::HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState)
{
	RefreshTracker();
}

void UQuestTrackerWidget::HandleQuestProgressChanged(FName QuestID, int32 NewProgress)
{
	RefreshTracker();
}

void UQuestTrackerWidget::HandleQuestInnerProgressChanged(FName QuestID, int32 NewInnerProgress)
{
	RefreshTracker();
}

void UQuestTrackerWidget::HandleTrackedQuestChanged(FName NewTrackedQuestID)
{
	RefreshTracker();
}
