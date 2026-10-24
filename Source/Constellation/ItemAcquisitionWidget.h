#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "ItemAcquisitionTypes.h"
#include "Styling/SlateBrush.h"
#include "ItemAcquisitionWidget.generated.h"

class UFont;
class SScrollBox;

/** Paint/layout only. The presentation subsystem owns input, queue and time. */
UCLASS()
class CONSTELLATION_API UItemAcquisitionWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UItemAcquisitionWidget(const FObjectInitializer& ObjectInitializer);
 void SetPresentation(const FItemAcquisitionPresentation& InPresentation, FKey ConfirmKey);
 void SetPresentationOpacity(float PanelAlpha, float TextAlpha);
 // Direct routing makes overflow readable with a hidden cursor or gamepad.
 void ScrollDescription(float PixelDelta);
 // Returns a fully contained, aspect-preserving rectangle in the sprite well.
 static FSlateRect FitSprite(FVector2D ImageSize, FVector2D WellSize, float Scale, FVector2D Offset);
protected:
 virtual TSharedRef<SWidget> RebuildWidget() override;
 virtual void ReleaseSlateResources(bool bReleaseChildren) override;
private:
 UPROPERTY(Transient) FItemAcquisitionPresentation Presentation;
 UPROPERTY() TObjectPtr<UTexture2D> NebulaTexture;
 UPROPERTY() TObjectPtr<UTexture2D> HaloTexture;
 UPROPERTY() TObjectPtr<UTexture2D> DividerTexture;
 UPROPERTY() TObjectPtr<UFont> TitleFont;
 FSlateBrush SpriteBrush, NebulaBrush, HaloBrush, DividerBrush;
 TSharedPtr<SScrollBox> DescriptionScroll;
 FText ConfirmLabel;
 float PanelOpacity=0.f, TextOpacity=0.f;
};
