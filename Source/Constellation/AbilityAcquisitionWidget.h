#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AbilityAcquisitionWidget.generated.h"
class UAbilityAcquisitionArt;
UCLASS()
class CONSTELLATION_API UAbilityAcquisitionWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UPROPERTY() TObjectPtr<UAbilityAcquisitionArt> Art;
 int32 Slot=0;int32 OwnedMask=0;double Elapsed=0;float ExitOpacity=1;
protected:
 virtual TSharedRef<SWidget> RebuildWidget() override;
 virtual int32 NativePaint(const FPaintArgs&,const FGeometry&,const FSlateRect&,FSlateWindowElementList&,int32,const FWidgetStyle&,bool) const override;
};
