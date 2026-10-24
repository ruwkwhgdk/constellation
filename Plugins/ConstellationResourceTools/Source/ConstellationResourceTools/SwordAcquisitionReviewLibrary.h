#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SwordAcquisitionReviewLibrary.generated.h"
UCLASS()
class USwordAcquisitionReviewLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable) static bool PrepareBackgroundTick(UObject* Context);
 UFUNCTION(BlueprintPure) static bool PawnInputEnabled(class APawn* Pawn);
 UFUNCTION(BlueprintCallable) static bool ConfigureSwordReview(class APawn* Pawn);
 UFUNCTION(BlueprintPure) static FString ReviewInputState(class APawn* Pawn);
 UFUNCTION(BlueprintPure) static float CameraBlendRemaining(class APawn* Pawn);
};
