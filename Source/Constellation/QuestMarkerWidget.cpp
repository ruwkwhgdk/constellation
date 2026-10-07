// Fill out your copyright notice in the Description page of Project Settings.


#include "QuestMarkerWidget.h"
#include "QuestMarkerProjection.h"
#include "Engine/LocalPlayer.h"
#include "Engine/GameViewportClient.h"
#include "SceneView.h"
#include "QuestSubsystem.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Blueprint/WidgetLayoutLibrary.h"

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
		OnQuestMarkerUpdated(false, false, FVector2D::ZeroVector, 0.f, 0.f);
		return;
	}

	APlayerController* PC = GetOwningPlayer();
	const APawn* Pawn = PC ? PC->GetPawn() : nullptr;
	if (!PC || !Pawn)
	{
		OnQuestMarkerUpdated(false, false, FVector2D::ZeroVector, 0.f, 0.f);
		return;
	}

	const FVector PawnLocation = Pawn->GetActorLocation();
	static constexpr float CentimetersPerMeter = 100.f;
	const float DistanceMeters = FVector::Dist(PawnLocation, CurrentTargetPosition) / CentimetersPerMeter;

	const FVector2D ViewportSize = UWidgetLayoutLibrary::GetViewportSize(this);
	if (ViewportSize.ContainsNaN() || ViewportSize.X <= 0.0 || ViewportSize.Y <= 0.0 || !FMath::IsFinite(DistanceMeters))
	{
		OnQuestMarkerUpdated(false, false, FVector2D::ZeroVector, 0.f, 0.f);
		return;
	}
	const FVector2D ViewportCenter = ViewportSize * 0.5f;
	FVector2D ScreenPos = FVector2D::ZeroVector;
	const bool bInFront = PC->ProjectWorldLocationToScreen(CurrentTargetPosition, ScreenPos, true);
	if (!bInFront)
	{
		// A failed projection does not supply a usable screen position. Derive the
		// direction without dividing by W, including targets exactly on the camera plane.
		const ULocalPlayer* LP = PC->GetLocalPlayer();
		FSceneViewProjectionData ProjectionData;
		FVector2D Direction;
		if (!LP || !LP->ViewportClient || !LP->ViewportClient->Viewport
			|| !LP->GetProjectionData(LP->ViewportClient->Viewport, ProjectionData)
			|| !QuestMarkerProjection::GetBehindCameraDirection(CurrentTargetPosition,
				ProjectionData.ComputeViewProjectionMatrix(),
				FVector2D(ProjectionData.GetConstrainedViewRect().Width(), ProjectionData.GetConstrainedViewRect().Height()), Direction))
		{
			OnQuestMarkerUpdated(false, false, FVector2D::ZeroVector, 0.f, 0.f);
			return;
		}
		ScreenPos = ViewportCenter + Direction;
	}
	if (ScreenPos.ContainsNaN())
	{
		OnQuestMarkerUpdated(false, false, FVector2D::ZeroVector, 0.f, 0.f);
		return;
	}

	static constexpr float EdgeMarginPixels = 48.f;
	const FVector2D HalfExtents(FMath::Max(ViewportSize.X * 0.5f - EdgeMarginPixels, 1.f),
		FMath::Max(ViewportSize.Y * 0.5f - EdgeMarginPixels, 1.f));

	const FVector2D FromCenter = ScreenPos - ViewportCenter;
	const bool bOnScreen = bInFront
		&& FMath::Abs(FromCenter.X) <= HalfExtents.X
		&& FMath::Abs(FromCenter.Y) <= HalfExtents.Y;

	// GetViewportSize/ProjectWorldLocationToScreen both operate in raw viewport pixels, but a Canvas
	// Panel Slot's Position is in DPI-scaled local space (screen_pixels = local_position * ViewportScale)
	// — without this division the marker drifts away from the true target position (more so off-center)
	// whenever the DPI scale curve isn't exactly 1.0 at the current resolution.
	const float ViewportScale = UWidgetLayoutLibrary::GetViewportScale(this);
	if (!FMath::IsFinite(ViewportScale) || ViewportScale <= 0.f)
	{
		OnQuestMarkerUpdated(false, false, FVector2D::ZeroVector, 0.f, 0.f);
		return;
	}

	if (bOnScreen)
	{
		OnQuestMarkerUpdated(true, true, ScreenPos / ViewportScale, 0.f, DistanceMeters);
		return;
	}

	const FVector2D ClampedOffset = QuestMarkerProjection::ClampDirectionToRectEdge(FromCenter, HalfExtents);
	const FVector2D ClampedScreenPos = ViewportCenter + ClampedOffset;
	// 0 = straight up, positive = clockwise, matching screen space where +X is right and +Y is down.
	const float ScreenRotationDegrees = FMath::RadiansToDegrees(FMath::Atan2(ClampedOffset.X, -ClampedOffset.Y));

	OnQuestMarkerUpdated(true, false, ClampedScreenPos / ViewportScale, ScreenRotationDegrees, DistanceMeters);
}
