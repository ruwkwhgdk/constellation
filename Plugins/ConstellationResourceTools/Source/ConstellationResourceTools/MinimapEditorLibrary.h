#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MinimapEditorLibrary.generated.h"
class UMinimapRegionData;

UCLASS()
class UMinimapEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Minimap|Editor") static FString DescribeFloorSamples(UMinimapRegionData* Data,FVector Position);
 UFUNCTION(BlueprintCallable,Category="Minimap|Editor") static FString DescribePawnGround(UObject* WorldContext);
 UFUNCTION(BlueprintCallable,Category="Minimap|Editor") static FString BuildSchoolMap(UObject* WorldContext,UMinimapRegionData* Data);
 // Regenerates geometry/discovery only. Designer overrides and objectives remain intact.
 UFUNCTION(BlueprintCallable, Category="Editor|Minimap", meta=(WorldContext="WorldContext"))
 static bool GenerateSchoolMap(UObject* WorldContext, UMinimapRegionData* Data, FString& Report);
};
