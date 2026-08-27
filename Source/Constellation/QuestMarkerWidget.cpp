// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestMarkerWidget.h"
#include "QuestSubsystem.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Camera/PlayerCameraManager.h"

void UQuestMarkerWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.AddDynamic(this, &UQuestMarkerWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.AddDynamic(this, &UQuestMarkerWidget::HandleQuestProgressChanged);
				Sub->OnQuestInnerProgressChanged.AddDynamic(this, &UQuestMarkerWidget::HandleQuestInnerProgressChanged);
				Sub->OnTrackedQuestChanged.AddDynamic(this, &UQuestMarkerWidget::HandleTrackedQuestChanged);
			}
		}
	}

	RefreshTargetPosition();
}

void UQuestMarkerWidget::NativeDestruct()
{
	if (const UWorld* World = GetWorld())
	{
		if (UGameInstance* GI = World->GetGameInstance())
		{
			if (UQuestSubsystem* Sub = GI->GetSubsystem<UQuestSubsystem>())
			{
				Sub->OnQuestStateChanged.RemoveDynamic(this, &UQuestMarkerWidget::HandleQuestStateChanged);
				Sub->OnQuestProgressChanged.RemoveDynamic(this, &UQuestMarkerWidget::HandleQuestProgressChanged);
				Sub->OnQuestInnerProgressChanged.RemoveDynamic(this, &UQuestMarkerWidget::HandleQuestInnerProgressChanged);
				Sub->OnTrackedQuestChanged.RemoveDynamic(this, &UQuestMarkerWidget::HandleTrackedQuestChanged);
			}
		}
	}

	Super::NativeDestruct();
}

void UQuestMarkerWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	UpdateMarker();
}

void UQuestMarkerWidget::HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState)
{
	RefreshTargetPosition();
}

void UQuestMarkerWidget::HandleQuestProgressChanged(FName QuestID, int32 NewProgress)
{
	RefreshTargetPosition();
}

void UQuestMarkerWidget::HandleQuestInnerProgressChanged(FName QuestID, int32 NewInnerProgress)
{
	RefreshTargetPosition();
}

void UQuestMarkerWidget::HandleTrackedQuestChanged(FName NewTrackedQuestID)
{
	RefreshTargetPosition();
}

void UQuestMarkerWidget::RefreshTargetPosition()
{
	bHasTarget = false;
	CurrentTargetPosition = FVector::ZeroVector;

	const UWorld* World = GetWorld();
	UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	UQuestSubsystem* Sub = GI ? GI->GetSubsystem<UQuestSubsystem>() : nullptr;
	if (!Sub)
	{
		return;
	}

	const FQuestDisplayInfo Info = Sub->GetTrackedQuestDisplayInfo();
	if (Info.TargetPositions.IsValidIndex(Info.InnerProgress))
	{
		CurrentTargetPosition = Info.TargetPositions[Info.InnerProgress];
		bHasTarget = true;
	}
}

void UQuestMarkerWidget::UpdateMarker()
{
	if (!bHasTarget)
	{
		OnQuestMarkerUpdated(false, 0.f, 0.f);
		return;
	}

	const APlayerController* PC = GetOwningPlayer();
	const APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	if (!PC || !Pawn)
	{
		OnQuestMarkerUpdated(false, 0.f, 0.f);
		return;
	}

	const FVector PawnLocation = Pawn->GetActorLocation();
	static constexpr float CentimetersPerMeter = 100.f;
	const float DistanceMeters = FVector::Dist(PawnLocation, CurrentTargetPosition) / CentimetersPerMeter;

	FVector CameraLocation = PawnLocation;
	float CameraYaw = PC->GetControlRotation().Yaw;
	if (const APlayerCameraManager* CameraManager = PC->PlayerCameraManager)
	{
		CameraLocation = CameraManager->GetCameraLocation();
		CameraYaw = CameraManager->GetCameraRotation().Yaw;
	}

	const FVector2D ToTarget2D(CurrentTargetPosition - CameraLocation);
	const float TargetYaw = FMath::RadiansToDegrees(FMath::Atan2(ToTarget2D.Y, ToTarget2D.X));
	const float ScreenRotationDegrees = FMath::UnwindDegrees(TargetYaw - CameraYaw);

	OnQuestMarkerUpdated(true, ScreenRotationDegrees, DistanceMeters);
}
