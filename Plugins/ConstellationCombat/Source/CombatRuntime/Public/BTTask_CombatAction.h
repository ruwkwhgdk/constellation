#pragma once
#include "CoreMinimal.h"
#include "BehaviorTree/BTTaskNode.h"
#include "CombatAbilitySystem.h"
#include "BTTask_CombatAction.generated.h"
class UCombatActionDefinition;
class UCombatPatternProfile;
UCLASS(meta=(DisplayName="Execute Combat Action"))
class COMBATRUNTIME_API UBTTask_CombatAction : public UBTTaskNode
{
    GENERATED_BODY()
public:
    UBTTask_CombatAction();
    UPROPERTY(EditAnywhere, Category="Combat") TObjectPtr<UCombatPatternProfile> PatternProfile;
    UPROPERTY(EditAnywhere, Category="Combat") TObjectPtr<UCombatActionDefinition> Action;
    UPROPERTY(EditAnywhere, Category="Combat", meta=(ClampMin="0")) float PlayerRange = 180.f;
    virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* Memory) override;
    virtual EBTNodeResult::Type AbortTask(UBehaviorTreeComponent& OwnerComp, uint8* Memory) override;
    virtual void OnTaskFinished(UBehaviorTreeComponent& OwnerComp, uint8* Memory, EBTNodeResult::Type Result) override;
private:
    TWeakObjectPtr<UCombatAbilitySystem> System;
    TWeakObjectPtr<UBehaviorTreeComponent> Brain;
    FDelegateHandle EndHandle;
    uint64 ExpectedExecution = 0;
    bool bStarting = false;
    bool bCommittedEndDuringStart=false;
    uint64 EncounterEpoch=0;
    FName LastPattern;
    int32 ConsecutiveUses=0;
    void Detach();
    void Ended(uint64 Execution, ECombatActionResult Result);
};
