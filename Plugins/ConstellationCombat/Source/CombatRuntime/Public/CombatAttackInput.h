#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CombatAbilitySystem.h"
#include "CombatAttackInput.generated.h"
class UCombatActionDefinition;

// One explicit press queues at most one follow-up for the current execution.
UCLASS(ClassGroup=Combat, meta=(BlueprintSpawnableComponent))
class COMBATRUNTIME_API UCombatAttackInput : public UActorComponent
{
    GENERATED_BODY()
public:
    void Initialize(UCombatAbilitySystem* InSystem);
    UFUNCTION(BlueprintCallable,Category="Combat") bool RequestAttack(UCombatActionDefinition* EntryAction);
    UFUNCTION(BlueprintCallable,Category="Combat") void Clear();
    UFUNCTION(BlueprintPure,Category="Combat") bool HasBufferedAttack() const { return PendingAction!=nullptr; }
    UPROPERTY(BlueprintReadOnly,Category="Combat") FString LastInputReason;
protected:
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
private:
    UPROPERTY() TObjectPtr<UCombatAbilitySystem> System;
    UPROPERTY() TObjectPtr<UCombatActionDefinition> PendingAction;
    uint64 BufferedExecution=0;
    uint64 Generation=0;
    FDelegateHandle EndHandle,DeathHandle,HitHandle,DodgeHandle;
    void Ended(uint64 Execution,ECombatActionResult Result);
    void Detach();
};
