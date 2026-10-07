#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "ConstellationVFXEditorLibrary.generated.h"
class UBlueprint;
UCLASS()
class CONSTELLATIONVFXEDITOR_API UConstellationVFXEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Only the audited BP_Glass placeholder; dry-run or idempotent application. Does not save assets.
    UFUNCTION(BlueprintCallable,Category="Constellation|Effects|Editor")
    static bool NeutralizeLegacyGlassPlaceholder(UBlueprint* Blueprint,bool bApply,FString& Report);
};
