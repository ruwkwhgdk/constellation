#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarryInputLibrary.generated.h"
class UAnimInstance;

UCLASS()
class CONSTELLATION_API UCarryInputLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // True means carry consumed this input; False continues the original Blueprint flow.
    UFUNCTION(BlueprintCallable, Category="Carry") static bool RouteCarryInput(AActor* Actor,FName Action,FName Phase);
    UFUNCTION(BlueprintCallable, Category="Carry") static void AbortActorCarry(AActor* Actor);
    UFUNCTION(BlueprintPure, Category="Carry") static float CarryIKAlpha(UAnimInstance* AnimInstance);
    UFUNCTION(BlueprintPure, Category="Carry") static FVector CarryGrip(UAnimInstance* AnimInstance,bool bLeft);
    UFUNCTION(BlueprintPure, Category="Carry") static FVector CarryElbow(UAnimInstance* AnimInstance,bool bLeft);
};
