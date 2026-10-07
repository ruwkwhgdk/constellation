#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "SceneDirectorLibrary.generated.h"
class USceneDirectorAsset;
class ULevelSequence;
class UBlueprint;
UCLASS()
class SCENEDIRECTOREDITOR_API USceneDirectorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static bool CompileAuthoringEvents(USceneDirectorAsset* Asset,FString& Report);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static bool ConnectGameSignals(UBlueprint* Blueprint,const FString& Kind,FString& Error);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static bool ConnectMappedInteraction(UBlueprint* Blueprint,FString& Error);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static bool SetGameplayReturnDuration(USceneDirectorAsset* Asset,float Seconds,FString& Error);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static bool DisconnectLegacyVolume(UWorld* World,ULevelSequence* Source,FString& Error);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateSchoolPerformance(ULevelSequence* Source,ULevelSequence* Visual,const TMap<FString,AActor*>& BindingActors,const FString& AssetPath,FString& Report);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static FString InspectLegacySequence(ULevelSequence* Source,UWorld* World);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static bool UpgradeStatueInteraction(FString& Error);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static UBlueprint* CreateStatueInteractionBlueprint(FString& Report);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static void SetDirectorAuthoringOrigin(USceneDirectorAsset* Asset,const FTransform& Origin);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static void ArrangeDirectorGraph(USceneDirectorAsset* Asset);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateStatuePerformance(UWorld* World,FString& Report);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static UBlueprint* GetSequenceDirectorBlueprint(ULevelSequence* Source);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* ImportSequence(ULevelSequence* Source,const FString& AssetPath,FString& Report);
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateExample();
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateConversationExample();
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateBranchingExample();
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateActionsExample();
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateSequenceExample();
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static USceneDirectorAsset* CreateImportExample();
    UFUNCTION(BlueprintCallable,Category="Scene Director|Editor") static bool CompileDirector(USceneDirectorAsset* Asset,FString& Message);
};
