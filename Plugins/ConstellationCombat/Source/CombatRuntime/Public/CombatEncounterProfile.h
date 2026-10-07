#pragma once
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CombatEncounterProfile.generated.h"
UCLASS(BlueprintType)
class COMBATRUNTIME_API UCombatEncounterProfile : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="1")) float DetectRadius=800;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="1")) float LoseRadius=1100;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="1")) float LeashRadius=700;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="1")) float AttackDistance=140;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="1")) float MoveSpeed=220;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0.05")) float ThinkInterval=.2f;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0")) float LostSightTime=3;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="1")) float HomeTolerance=50;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0.1")) float RetryDelay=1;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0.1")) float RetryCooldown=3;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="0.1")) float StuckTimeout=2;
    UPROPERTY(EditAnywhere,BlueprintReadOnly,meta=(ClampMin="1")) int32 MaxMoveFailures=3;
    UPROPERTY(EditAnywhere,BlueprintReadOnly) bool bRestoreOnReturn=true;
    bool Validate(FString& Reason) const;
#if WITH_EDITOR
    virtual EDataValidationResult IsDataValid(FDataValidationContext& Context) const override;
#endif
};
