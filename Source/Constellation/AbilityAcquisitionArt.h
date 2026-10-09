#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "AbilityAcquisitionArt.generated.h"
class UTexture2D;class UDataTable;class USoundBase;class UFont;
UCLASS(BlueprintType)
class CONSTELLATION_API UAbilityAcquisitionArt : public UDataAsset
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TObjectPtr<UTexture2D> Background;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TObjectPtr<UTexture2D> Emblem;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TArray<TObjectPtr<UTexture2D>> Dormant;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TArray<TObjectPtr<UTexture2D>> Stars;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TArray<TObjectPtr<UTexture2D>> NewStars;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TArray<TObjectPtr<UTexture2D>> Lines;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TArray<TObjectPtr<UTexture2D>> LitLines;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TObjectPtr<UDataTable> Descriptions;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TObjectPtr<UFont> TitleFont;
 UPROPERTY(EditAnywhere,BlueprintReadOnly) TArray<TObjectPtr<USoundBase>> Sounds;
 bool IsReady() const;
 FText Description(int32 Slot) const;
};
