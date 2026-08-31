// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "QuestTypes.h"
#include "QuestMarkerWidget.generated.h"

/**
 * Always-on HUD element pointing towards the tracked quest's current guidance marker (see
 * AQuestTargetMarker / FQuestProgressStepDef::TargetPositions). Aims at
 * TargetPositions[InnerProgress] of the tracked quest's current step, re-aiming whenever Progress,
 * InnerProgress, or the tracked quest itself changes. Make a Blueprint child of this class (e.g.
 * WBP_QuestMarker) and implement OnQuestMarkerUpdated to place an arrow/distance panel at the
 * target's actual on-screen position (or clamp it to the screen edge when the target is off-screen).
 */
UCLASS(Abstract)
class CONSTELLATION_API UQuestMarkerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/**
	 * Implement in Blueprint to render the marker. bVisible is false when there's no current
	 * target (no quest tracked, or the tracked quest's current step has no marker positions left) —
	 * collapse the panel in that case.
	 *
	 * ScreenPosition is where to place the marker panel, in viewport pixels (same space as
	 * UWidgetLayoutLibrary::GetViewportSize / a CanvasPanelSlot with Anchors (0,0)-(0,0)). Set the
	 * panel's CanvasPanelSlot Position to this value every update.
	 *
	 * bOnScreen is true when the target itself is visible on screen — ScreenPosition is then the
	 * target's exact projected position, and the arrow can be hidden (or just shown static, not
	 * rotated). bOnScreen is false when the target is off-screen — ScreenPosition is then clamped to
	 * the screen edge along the direction to the target, and the arrow should be rotated by
	 * ScreenRotationDegrees (0 = straight up, positive = clockwise) and shown pointing further
	 * outward, offset by however much the source texture's drawn direction differs from "up", e.g.
	 * TextBoxDownArrow needs +180.
	 *
	 * DistanceMeters is the straight-line distance from the player pawn to the target, converted
	 * from Unreal units (cm) to meters.
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Quest")
	void OnQuestMarkerUpdated(bool bVisible, bool bOnScreen, FVector2D ScreenPosition, float ScreenRotationDegrees, float DistanceMeters);

protected:
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	UFUNCTION()
	void HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState);

	UFUNCTION()
	void HandleQuestProgressChanged(FName QuestID, int32 NewProgress);

	UFUNCTION()
	void HandleQuestInnerProgressChanged(FName QuestID, int32 NewInnerProgress);

	UFUNCTION()
	void HandleTrackedQuestChanged(FName NewTrackedQuestID);

	/** Re-pulls the tracked quest's current inner-progress target position from UQuestSubsystem. */
	void RefreshTargetPosition();

	/** Recomputes screen position/rotation/distance from the cached target and fires OnQuestMarkerUpdated. */
	void UpdateMarker();

	/**
	 * Clamps a direction from the viewport center to the edge of a HalfExtents-sized rectangle
	 * centered on it, returning the offset from center to the clamped edge point.
	 */
	static FVector2D ClampDirectionToRectEdge(const FVector2D& Direction, const FVector2D& HalfExtents);

	bool bHasTarget = false;
	FVector CurrentTargetPosition = FVector::ZeroVector;
};
