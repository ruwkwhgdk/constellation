#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "PlayerHUDStyleEditorLibrary.generated.h"
class UBlueprint; class APlayerController;
UCLASS()
class UPlayerHUDStyleEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable,Category="Editor|PlayerHUD") static bool InjectSprintReview(APlayerController* Player);
 UFUNCTION(BlueprintCallable,Category="Editor|PlayerHUD") static bool ApplyStarlightHUD(UBlueprint* Widget,UBlueprint* Heroine,UBlueprint* Stats,FString& Error);
};
