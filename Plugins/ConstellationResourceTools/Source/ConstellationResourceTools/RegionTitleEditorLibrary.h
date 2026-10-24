#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "RegionTitleEditorLibrary.generated.h"
class UBlueprint; class UFont; class UFontFace; class UWorld; class URegionTitleWidget;
UCLASS()
class URegionTitleEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Editor|RegionTitle") static UFont* CreateRegionFont(const FString& FontFilename);
 UFUNCTION(BlueprintCallable,Category="Editor|RegionTitle") static bool ApplyRegionTitle(UBlueprint* Widget,UBlueprint* Trigger,FString& Error);
 UFUNCTION(BlueprintCallable,Category="Editor|RegionTitle") static URegionTitleWidget* CreateRegionReview(UWorld* World,FText Title,FText Subtitle);
};
