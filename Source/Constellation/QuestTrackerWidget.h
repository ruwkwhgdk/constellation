// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "QuestTypes.h"
#include "Fonts/SlateFontInfo.h"
#include "QuestTrackerWidget.generated.h"

/**
 * Starlight Guide HUD tracker below the minimap. Shows exactly one
 * quest at a time — whichever UQuestSubsystem currently reports as the tracked quest (auto-picked,
 * Main-type preferred, or pinned via SetTrackedQuest) — rather than a full quest log/journal.
 * Existing Blueprint children retain their refresh event; the native presentation owns rendering.
 */
UCLASS(Abstract)
class CONSTELLATION_API UQuestTrackerWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UQuestTrackerWidget(const FObjectInitializer& ObjectInitializer);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quest|Appearance", meta=(ClampMin="280", ClampMax="420")) float TrackerWidth=310;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quest|Appearance", meta=(ClampMin="0")) float MinimapGap=24;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quest|Appearance") FSlateFontInfo TitleFont;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Quest|Appearance") FSlateFontInfo ObjectiveFont;
	UFUNCTION(BlueprintPure, Category="Quest|Tracker") FQuestDisplayInfo GetTrackerSnapshot()const{return DisplayInfo;}
	UFUNCTION(BlueprintPure, Category="Quest|Tracker") FText GetQuantityLabel()const;
	UFUNCTION(BlueprintPure, Category="Quest|Tracker") bool IsTrackerPresented()const;
	/** Origin in viewport Slate units (DPI applied by viewport once). */
	UFUNCTION(BlueprintPure, Category="Quest|Tracker") FVector2D GetTrackerOrigin()const;
	UFUNCTION(BlueprintPure, Category="Quest|Tracker") FVector2D GetTrackerContentSize()const;
	/** Re-pulls the tracked quest's display info and calls OnTrackerRefreshed. */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	void RefreshTracker();

	/**
	 * Implement in Blueprint to render Info. Info.bVisible is false when no quest is currently
	 * tracked (e.g. nothing accepted yet) — collapse the panel in that case.
	 */
	UFUNCTION(BlueprintImplementableEvent, Category = "Quest")
	void OnTrackerRefreshed(const FQuestDisplayInfo& Info);

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void ReleaseSlateResources(bool bReleaseChildren) override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

private:
	FQuestDisplayInfo DisplayInfo;
	TSharedPtr<class SStarlightQuestTracker> Presentation;
	UFUNCTION()
	void HandleQuestStateChanged(FName QuestID, EQuestState OldState, EQuestState NewState);

	UFUNCTION()
	void HandleQuestProgressChanged(FName QuestID, int32 NewProgress);

	UFUNCTION()
	void HandleQuestInnerProgressChanged(FName QuestID, int32 NewInnerProgress);

	UFUNCTION()
	void HandleTrackedQuestChanged(FName NewTrackedQuestID);
};
