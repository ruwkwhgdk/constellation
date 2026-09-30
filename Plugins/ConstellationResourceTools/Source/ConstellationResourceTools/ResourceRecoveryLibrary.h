#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "ResourceRecoveryLibrary.generated.h"

class UAnimationAsset;
class USkeleton;

UCLASS()
class UResourceRecoveryLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Restores an absent pointer only. Never retargets an existing animation skeleton.
    UFUNCTION(BlueprintCallable, Category = "Editor|Resource Recovery")
    static bool RestoreMissingAnimationSkeleton(UAnimationAsset* Animation, USkeleton* Skeleton);
};
