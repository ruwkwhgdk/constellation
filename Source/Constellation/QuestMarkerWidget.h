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
 * WBP_QuestMarker) and implement OnQuestMarkerUpdated to rotate an arrow image and show the
 * distance text.
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
	 * ScreenRotationDegrees is the target's bearing relative to the camera's forward direction
	 * (0 = straight ahead, positive = clockwise/to the right), ignoring camera pitch so the arrow
	 * behaves like a flat compass needle. Rotate the arrow image by this value (offset by however
	 * much the source texture's drawn direction differs from "up", e.g. TextBoxDownArrow needs +180).
	 *
	 * DistanceMeters is the straight-line distance from the player pawn to the target, converted
	 * from Unreal units (cm) to meters.
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Quest")
	void OnQuestMarkerUpdated(bool bVisible, float ScreenRotationDegrees, float DistanceMeters);

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

	/** Recomputes screen rotation/distance from the cached target and fires OnQuestMarkerUpdated. */
	void UpdateMarker();

	bool bHasTarget = false;
	FVector CurrentTargetPosition = FVector::ZeroVector;
};
