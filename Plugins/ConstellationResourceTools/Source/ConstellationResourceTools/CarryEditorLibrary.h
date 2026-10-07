#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CarryEditorLibrary.generated.h"
class UBlueprint;
class UAnimBlueprint;
class USkeleton;
class UAnimSequence;
class UMaterialInterface;
class AActor;
UCLASS()
class UCarryEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable,Category="Editor|Interaction") static FString CreateInteractionStrings(const FString& SourceCSV);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static FString CreateCarryTables(UBlueprint* Hero,UBlueprint* Chair,UBlueprint* Desk,UBlueprint* Box);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static FString InstallCarryInput(UBlueprint* Blueprint);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static FString InstallCarryOverlay(UAnimBlueprint* Blueprint);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static FString InspectCarrySkeleton(USkeleton* Skeleton);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static UAnimSequence* RetargetCarrySequence(UAnimSequence* Source,USkeleton* Target,const FString& PackagePath,const FString& AssetName);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static FString ConfigureCarryBlueprint(UBlueprint* Blueprint,const FString& AnimationFolder,UMaterialInterface* PreviewMaterial);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static FString ConfigureTestBox(UBlueprint* Blueprint,UClass* HoldableClass);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static void StartCarryReviewPlay();
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static AActor* GetCarryReviewPawn();
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static bool InjectCarryReviewInput(const FString& ActionPath,FVector Value);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static void CaptureCarryReview(const FString& Filename,bool bShowUI=false);
    UFUNCTION(BlueprintCallable,Category="Editor|Carry") static void UseCarryReviewCamera(bool bCloseUp);
};
