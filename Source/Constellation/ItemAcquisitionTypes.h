#pragma once
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "ItemAcquisitionTypes.generated.h"
class UTexture2D;
class USoundBase;

/** Presentation only. This payload never grants, removes or persists items. */
USTRUCT(BlueprintType)
struct CONSTELLATION_API FItemAcquisitionPresentation
{
 GENERATED_BODY()
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Item") FName ItemId;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Item") TObjectPtr<UTexture2D> Sprite;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Item") FText Name;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Item",meta=(MultiLine="true")) FText Description;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Item",meta=(ClampMin="1")) int32 Quantity=1;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Layout",meta=(ClampMin="0.1",ClampMax="1")) float SpriteScale=1.f;
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Layout") FVector2D SpriteOffset=FVector2D::ZeroVector;
 // Optional approved one-shot cue; unset means silent presentation.
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Audio") TObjectPtr<USoundBase> AppearanceSound;
};
