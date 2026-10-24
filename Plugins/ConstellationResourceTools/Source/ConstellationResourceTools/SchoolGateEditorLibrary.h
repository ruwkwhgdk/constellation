#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SchoolGateEditorLibrary.generated.h"
class UBlueprint;
UCLASS()
class USchoolGateEditorLibrary : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public: UFUNCTION(BlueprintCallable,Category="Editor|School Gate") static void PrepareReviewAudio();
 UFUNCTION(BlueprintCallable,Category="Editor|School Gate") static FString Install(UBlueprint* Blueprint);
};
