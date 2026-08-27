// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestTargetMarker.h"
#include "QuestDefinition.h"

AQuestTargetMarker::AQuestTargetMarker()
{
	PrimaryActorTick.bCanEverTick = false;
	bIsEditorOnlyActor = true;

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

void AQuestTargetMarker::SyncToQuest()
{
	if (!Quest)
	{
		UE_LOG(LogTemp, Warning, TEXT("AQuestTargetMarker::SyncToQuest: No Quest assigned on %s"), *GetActorLabel());
		return;
	}

	if (!Quest->ProgressSteps.IsValidIndex(StepIndex - 1))
	{
		UE_LOG(LogTemp, Warning, TEXT("AQuestTargetMarker::SyncToQuest: StepIndex %d is out of range for %s (%d step(s))"),
			StepIndex, *Quest->GetName(), Quest->ProgressSteps.Num());
		return;
	}

	Quest->Modify();

	FQuestProgressStepDef& Step = Quest->ProgressSteps[StepIndex - 1];
	Step.TargetPositions.Reset(Points.Num());
	for (const FVector& LocalPoint : Points)
	{
		Step.TargetPositions.Add(GetActorTransform().TransformPosition(LocalPoint));
	}
	Step.InnerProgressCount = Step.TargetPositions.Num();

	Quest->MarkPackageDirty();

	UE_LOG(LogTemp, Log, TEXT("AQuestTargetMarker::SyncToQuest: Wrote %d position(s) into %s step %d"),
		Step.TargetPositions.Num(), *Quest->GetName(), StepIndex);
}
