#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "TutorialToastEditorLibrary.generated.h"
class UBlueprint; class UWorld; class UTutorialPromptWidget;
UCLASS()
class UTutorialToastEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Editor|Tutorial") static bool PrepareToastCaller(UBlueprint* Blueprint,FString& Error);
 UFUNCTION(BlueprintCallable,Category="Editor|Tutorial") static UTutorialPromptWidget* CreateToastReview(UWorld* World, int32 ActionIndex, float Duration=8.f);
};
