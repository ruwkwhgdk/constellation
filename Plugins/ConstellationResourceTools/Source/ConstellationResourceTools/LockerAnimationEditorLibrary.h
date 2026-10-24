#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LockerAnimationEditorLibrary.generated.h"
class UAnimMontage;
class UAnimSequence;

UCLASS()
class ULockerAnimationEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Mutates only the locker montage in memory; the caller explicitly saves it.
    UFUNCTION(BlueprintCallable, Category="Editor|Locker")
    static bool ConfigureLockerMontage(UAnimMontage* Montage, UAnimSequence* Fall, UAnimSequence* Hold, UAnimSequence* GetUp);
};
