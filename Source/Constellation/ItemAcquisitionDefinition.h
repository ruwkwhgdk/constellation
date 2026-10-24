#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ItemAcquisitionTypes.h"
#include "ItemAcquisitionDefinition.generated.h"

/** Designer-authored display data. No inventory/grant behavior. */
UCLASS(BlueprintType)
class CONSTELLATION_API UItemAcquisitionDefinition : public UDataAsset
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere,BlueprintReadWrite,Category="Presentation",meta=(ShowOnlyInnerProperties))
 FItemAcquisitionPresentation Presentation;
};
