#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "FallAnimationEditorLibrary.generated.h"
class UAnimBlueprint;
UCLASS()
class UFallAnimationEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Editor|Fall") static FString InstallFallSlot(UAnimBlueprint* Blueprint);
};
