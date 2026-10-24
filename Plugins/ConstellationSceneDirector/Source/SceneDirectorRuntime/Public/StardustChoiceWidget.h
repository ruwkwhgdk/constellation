#pragma once
#include "Blueprint/UserWidget.h"
#include "StardustChoiceWidget.generated.h"
class UButton;class UImage;class UOverlay;class UTexture2D;class UTextBlock;class URichTextBlock;
// Skin for the existing choice Blueprint; its buttons and outcome graphs remain intact.
UCLASS()
class SCENEDIRECTORRUNTIME_API UStardustChoiceWidget : public UUserWidget
{
 GENERATED_BODY()
public:
 UStardustChoiceWidget(const FObjectInitializer& Initializer);
 virtual void NativeConstruct() override;
 virtual void NativeTick(const FGeometry&,float) override;
 UFUNCTION(BlueprintCallable,Category="Dialogue|Choice") void RefreshChoiceVisuals();
 UFUNCTION(BlueprintCallable,Category="Dialogue|Choice") bool SetChoiceAvailability(int32 Index,bool bEnabled,FText Reason);
private:
 UPROPERTY() TObjectPtr<UTexture2D> LockedAtlas;
 UPROPERTY(Transient) TArray<TObjectPtr<UImage>> LockedBackgrounds;
 UPROPERTY(Transient) TArray<TObjectPtr<UImage>> ClosedLocks;
 UPROPERTY(Transient) TArray<TObjectPtr<UImage>> OpenLocks;
 UPROPERTY(Transient) TArray<TObjectPtr<UTextBlock>> Reasons;
 UPROPERTY(Transient) TArray<TObjectPtr<URichTextBlock>> Labels;
 TMap<int32,bool> PendingEnabled;
 TMap<int32,FText> PendingReasons;
 TArray<bool> PreviousEnabled;
 TArray<float> UnlockElapsed;

 UPROPERTY() TObjectPtr<UTexture2D> Atlas;
 UPROPERTY(Transient) TArray<TObjectPtr<UButton>> Buttons;
 UPROPERTY(Transient) TArray<TObjectPtr<UImage>> Backgrounds;
 UPROPERTY(Transient) TArray<TObjectPtr<UImage>> Cursors;
 UPROPERTY(Transient) TArray<TObjectPtr<UImage>> Stars;
 UPROPERTY(Transient) TArray<TObjectPtr<UOverlay>> Rows;
 int32 Active=0;
 float Phase=0;
};
