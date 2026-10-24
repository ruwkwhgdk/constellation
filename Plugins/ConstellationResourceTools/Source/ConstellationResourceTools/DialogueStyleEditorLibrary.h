#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "DialogueStyleEditorLibrary.generated.h"
class UBlueprint; class UTexture2D; class UUserWidget; class UWorld;
UCLASS()
class UDialogueStyleEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Editor|Dialogue") static UUserWidget* CreateChoiceReview(UWorld* World);
 UFUNCTION(BlueprintCallable,Category="Editor|Dialogue") static bool ApplyStardustChoices(UBlueprint* Blueprint,FString& Error);
 UFUNCTION(BlueprintCallable,Category="Editor|Dialogue") static bool ApplyQuietNebula(UBlueprint* Blueprint,UTexture2D* Atlas,FString& Error);
};
