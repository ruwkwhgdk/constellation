#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Fonts/SlateFontInfo.h"
#include "Styling/SlateBrush.h"
#include "TimerManager.h"
#include "RegionTitleWidget.generated.h"

class UTexture2D;

/** Non-interactive, four-second region introduction. Existing Blueprint text properties remain authoritative. */
UCLASS()
class CONSTELLATION_API URegionTitleWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 URegionTitleWidget(const FObjectInitializer& ObjectInitializer);

 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Region Title|Appearance") FSlateFontInfo TitleFont;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Region Title|Appearance") FSlateFontInfo SubtitleFont;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Region Title|Appearance", meta=(ClampMin="0")) float TitleSubtitleGap=60.f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Region Title|Appearance", meta=(ClampMin="0",ClampMax="1")) float NebulaOpacity=.2f;
 UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Region Title|Appearance") TObjectPtr<UTexture2D> NebulaTexture;

 UFUNCTION(BlueprintCallable, Category="Region Title") void SetRegionText(const FText& Title,const FText& Subtitle);
 UFUNCTION(BlueprintPure, Category="Region Title") FText GetRegionTitleText() const;
 UFUNCTION(BlueprintPure, Category="Region Title") FText GetRegionSubtitleText() const;
 UFUNCTION(BlueprintPure, Category="Region Title") float GetStarsOpacity() const;
 UFUNCTION(BlueprintPure, Category="Region Title") float GetTextOpacity() const;
 UFUNCTION(BlueprintPure, Category="Region Title") bool IsPresentationFinished() const { return bFinished; }

 // The timer delegates to this deterministic clock, also useful to presentation tests.
 void AdvancePresentation(float DeltaSeconds);

protected:
 virtual TSharedRef<SWidget> RebuildWidget() override;
 virtual void NativeConstruct() override;
 virtual void NativeDestruct() override;
 virtual FReply NativeOnMouseButtonDown(const FGeometry&,const FPointerEvent&) override { return FReply::Unhandled(); }
 virtual FReply NativeOnKeyDown(const FGeometry&,const FKeyEvent&) override { return FReply::Unhandled(); }

private:
 friend class FRegionTitleLifecycleTest;
 void TickPresentation();
 void FinishPresentation();
 void UnregisterPresentation();
 float GetFadeOutOpacity() const;
 FText ReadRegionText(FName PropertyName,const FText& Fallback,const TCHAR* MarkupTag) const;
 FSlateBrush NebulaBrush;
 FText FallbackTitle,FallbackSubtitle;
 FTimerHandle PresentationTimer;
 float Elapsed=0.f;
 double LastTickTime=0;
 bool bActive=false,bFinished=false;
 static TArray<TWeakObjectPtr<URegionTitleWidget>> ActivePresentations;
};
