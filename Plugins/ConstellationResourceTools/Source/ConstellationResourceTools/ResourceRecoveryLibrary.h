#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "ResourceRecoveryLibrary.generated.h"

class UAnimationAsset;
class USkeleton;
class UBlueprint;
class UWorld;

UCLASS()
class UResourceRecoveryLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // Read-only graph export for repeatable logic audits. Does not save the asset.
    UFUNCTION(BlueprintCallable, Category = "Editor|Audit")
    static FString ExportBlueprintGraphs(UBlueprint* Blueprint);

    UFUNCTION(BlueprintCallable, Category = "Editor|Audit")
    static FString ExportLevelBlueprintGraphs(UWorld* World);

    // Read an autosave under a separate mount without replacing the current asset.
    UFUNCTION(BlueprintCallable, Category = "Editor|Audit")
    static UBlueprint* LoadAuditAutosave(const FString& RelativeAutosavePath, const TMap<FString, FString>& PackageRedirects);

    // Preview uses a transient duplicate. Apply edits in memory; caller decides whether to save.
    UFUNCTION(BlueprintCallable, Category = "Editor|Audit")
    static FString RepairKnownBlueprintLogic(UBlueprint* Blueprint, bool bApply = false);

    // Remove the obsolete editor Play call and its missing actor from the vendor demo.
    // Edits in memory only; the caller must check compilation before saving.
    UFUNCTION(BlueprintCallable, Category = "Editor|Audit")
    static FString RepairObsoleteShowcaseCall(UWorld* World);

    // Restores an absent pointer only. Never retargets an existing animation skeleton.
    UFUNCTION(BlueprintCallable, Category = "Editor|Resource Recovery")
    static bool RestoreMissingAnimationSkeleton(UAnimationAsset* Animation, USkeleton* Skeleton);
};
