#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AbilityAcquisitionEditorLibrary.generated.h"
class UBlueprint;
UCLASS()
class UAbilityAcquisitionEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Editor|Ability UI") static bool InstallAcquisitionHooks(UBlueprint* Blueprint,FString& Error);
};
