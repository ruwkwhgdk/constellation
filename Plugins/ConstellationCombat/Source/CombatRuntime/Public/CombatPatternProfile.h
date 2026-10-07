#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CombatPatternProfile.generated.h"
class UCombatActionDefinition;
class UCombatAbilitySystem;
USTRUCT(BlueprintType)
struct COMBATRUNTIME_API FCombatPatternEntry
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere,BlueprintReadOnly) FName Id;
    UPROPERTY(EditAnywhere,BlueprintReadOnly) TObjectPtr<UCombatActionDefinition> Action;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0")) float MinDistance=0;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0")) float MaxDistance=180;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0",ClampMax="180")) float MaxAngle=80;
    UPROPERTY(EditAnywhere,BlueprintReadOnly) bool bRequireSight=true;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0")) float Weight=1;
    // Zero means unlimited consecutive uses; a committed but interrupted attack still counts.
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0")) int32 MaxConsecutive=1;
};
UCLASS(BlueprintType)
class COMBATRUNTIME_API UCombatPatternProfile : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere,BlueprintReadOnly) TArray<FCombatPatternEntry> Patterns;
    bool Validate(FString& Reason) const;
    int32 Select(const UCombatAbilitySystem* System,float Distance,float Angle,bool HasSight,FName LastId,int32 Consecutive,float Roll,FString& Reason) const;
#if WITH_EDITOR
    virtual EDataValidationResult IsDataValid(FDataValidationContext& Context) const override;
#endif
};
