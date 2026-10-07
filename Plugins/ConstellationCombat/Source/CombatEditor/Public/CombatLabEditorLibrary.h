#pragma once
#include "Kismet/BlueprintFunctionLibrary.h"
#include "CombatLabEditorLibrary.generated.h"
class UAnimMontage;
class ACombatLabCharacter;
UCLASS()
class COMBATEDITOR_API UCombatLabEditorLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static ACombatLabCharacter* DuplicateReviewEnemy(ACombatLabCharacter* Source, FVector Offset);
    // True means the report was saved, not that the inspected character is valid.
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static bool SaveCombatCharacterReport(ACombatLabCharacter* Character, FString& SavedPath, FString& Error);
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static bool ValidateCombatCharacter(ACombatLabCharacter* Character, TArray<FString>& Errors, TArray<FString>& Warnings);
    // Empty means valid; shared runtime checks exposed to editor/Python authoring.
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static FString GetCombatAssetError(UObject* Asset);
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static bool BuildEncounterNavigation(UObject* WorldContext);
    // Review folder only; mutates in memory, caller must explicitly save.
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static UAnimMontage* PreviewAuthoredHitWindows(UAnimMontage* Source, const TArray<FName>& Ids, const TArray<float>& Starts, const TArray<float>& Ends);
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static bool ConfigureAuthoredHitWindows(UAnimMontage* Montage, const TArray<FName>& Ids, const TArray<float>& Starts, const TArray<float>& Ends);
    UFUNCTION(BlueprintCallable, Category="Combat|Editor")
    static bool ConfigureReviewMontage(UAnimMontage* Montage, float Start, float End);
};
