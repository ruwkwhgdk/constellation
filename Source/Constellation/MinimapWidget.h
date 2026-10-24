#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Fonts/SlateFontInfo.h"
#include "MinimapWidget.generated.h"

UCLASS() class CONSTELLATION_API UMinimapWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UMinimapWidget(const FObjectInitializer& ObjectInitializer);
 // Slate units; viewport DPI scaling applies once to the complete HUD.
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Minimap",meta=(ClampMin="180",ClampMax="360")) float Diameter=250;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Minimap") FVector2D SafeMargin=FVector2D(32,28);
 UPROPERTY() FSlateFontInfo LabelFont;
protected:
 virtual TSharedRef<SWidget> RebuildWidget() override;
};
